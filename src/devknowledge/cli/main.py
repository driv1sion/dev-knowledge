import click
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from devknowledge.core.db import DBManager
from devknowledge.analyzers.metrics import extract_metrics
from devknowledge.analyzers.deps import extract_dependencies
from devknowledge.analyzers.git import extract_git_history
from devknowledge.agents.router import AgentRouter
from devknowledge.extraction.graph import generate_knowledge_graph

@click.group()
def cli():
    """devknowledge - An open-source, local-first developer knowledge pipeline."""
    pass

@cli.command()
@click.argument('repo_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--interactive', '-i', is_flag=True, help="Force interactive prompts for manual data")
def analyze(repo_path, interactive):
    """Analyze a local repository to extract facts and capabilities."""
    click.echo(f"Analyzing repository at {repo_path}...")
    
    db_path = os.path.join(repo_path, "knowledge.db")
    db = DBManager(db_path)
    db.initialize()
    
    analysis_id = db.record_analysis(repo_path)
    
    # 1. Extract Metrics (scc)
    metrics = extract_metrics(repo_path)
    if metrics:
        click.echo("Extracted metrics.")
        for lang in metrics:
            lang_name = lang.get("Name")
            if lang_name:
                cap_id = db.add_capability(name=f"Language: {lang_name}", category="Language")
                ev_id = db.add_evidence(analysis_id, "scc", repo_path, "language", lang_name)
                db.link_capability_evidence(cap_id, ev_id)
                
    # 2. Extract Dependencies (syft)
    deps = extract_dependencies(repo_path)
    if deps:
        click.echo("Extracted dependencies.")
        for dep in deps:
            dep_name = dep.get("name")
            if dep_name:
                cap_id = db.add_capability(name=f"Dependency: {dep_name}", category="Dependency")
                ev_id = db.add_evidence(analysis_id, "syft", repo_path, "dependency", dep_name)
                db.link_capability_evidence(cap_id, ev_id)
                
    # 3. Extract Git History (git)
    commits = extract_git_history(repo_path)
    if commits:
        click.echo("Extracted git history.")
        # Unique authors
        authors = set(c["author"] for c in commits)
        for author in authors:
            cap_id = db.add_capability(name=f"Contributor: {author}", category="Contributor")
            # Find the most recent commit by this author for evidence
            latest_commit = next(c for c in commits if c["author"] == author)
            ev_id = db.add_evidence(analysis_id, "git", repo_path, "commit", latest_commit["hash"])
            db.link_capability_evidence(cap_id, ev_id)
                
    # 4. Agentic Workflow to resolve gaps
    router = AgentRouter(db)
    router.resolve_gaps(repo_path, interactive)
    
    click.echo("Analysis complete.")

@cli.command()
@click.argument('repo_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def publish(repo_path):
    """Publish the analyzed knowledge into a Knowledge Graph."""
    click.echo(f"Publishing knowledge graph for {repo_path}...")
    db_path = os.path.join(repo_path, "knowledge.db")
    output_path = os.path.join(repo_path, "knowledge_graph.json")
    generate_knowledge_graph(db_path, output_path)
    click.echo(f"Published to {output_path}")

@cli.command()
@click.argument('portfolio_data_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('project_name', type=str)
@click.argument('knowledge_graph_path', type=click.Path(exists=True, dir_okay=False))
def update_portfolio(portfolio_data_dir, project_name, knowledge_graph_path):
    """Update the portfolio projects index with the new knowledge graph."""
    click.echo(f"Updating portfolio for project {project_name}...")
    from devknowledge.portfolio.updater import update_portfolio_projects
    
    update_portfolio_projects(portfolio_data_dir, project_name, knowledge_graph_path)
    click.echo("Portfolio updated successfully.")

if __name__ == '__main__':
    cli()
