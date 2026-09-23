import click
from devknowledge.core.db import DBManager

class AgentRouter:
    def __init__(self, db: DBManager):
        self.db = db

    def evaluate_knowledge(self):
        """
        Evaluates the SQLite database for missing critical fields and returns a list of gaps.
        """
        gaps = []
        if not self.db.has_capability("Deployment Architecture"):
            gaps.append("Deployment Architecture")
        
        if not self.db.has_capability("Primary Database"):
            gaps.append("Primary Database")
            
        return gaps

    def resolve_gaps(self, repo_path: str):
        """
        Attempts to resolve knowledge gaps using deterministic checks, falling back to human input.
        """
        gaps = self.evaluate_knowledge()
        for gap in gaps:
            # MVP: Directly fallback to human asking for MVP since we don't have all local tools built yet.
            answer = click.prompt(f"Knowledge Gap Detected: What is the {gap} for this project?", type=str)
            if answer:
                cap_id = self.db.add_capability(name=gap, category="Architecture")
                # We create an analysis entry just to link the evidence
                analysis_id = self.db.record_analysis(project_path=repo_path)
                evidence_id = self.db.add_evidence(
                    analysis_id=analysis_id,
                    source_type="human",
                    source_reference="cli_prompt",
                    extracted_key=gap,
                    extracted_value=answer,
                    confidence=1.0
                )
                self.db.link_capability_evidence(cap_id, evidence_id)
                click.echo(f"Stored {gap} -> {answer}")
