import click
import os
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
def analyze(repo_path):
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
                
    # 3. Agentic Workflow to resolve gaps
    router = AgentRouter(db)
    router.resolve_gaps(repo_path)
    
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

if __name__ == '__main__':
    cli()
