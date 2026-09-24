import click
import os
import re
from devknowledge.core.db import DBManager
from devknowledge.agents.llm import summarize_project

class AgentRouter:
    def __init__(self, db: DBManager):
        self.db = db

    def _read_file(self, path):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _gather_docs(self, repo_path):
        docs_content = []
        readme_path = os.path.join(repo_path, "README.md")
        content = self._read_file(readme_path)
        if content:
            docs_content.append(f"--- README.md ---\n{content}\n")
            
        docs_dir = os.path.join(repo_path, "docs")
        if os.path.isdir(docs_dir):
            for root, _, files in os.walk(docs_dir):
                for file in files:
                    if file.endswith(".md") or file.endswith(".txt"):
                        file_path = os.path.join(root, file)
                        content = self._read_file(file_path)
                        if content:
                            docs_content.append(f"--- {os.path.relpath(file_path, repo_path)} ---\n{content}\n")
                            
        return "\n".join(docs_content)


    def infer_description(self, repo_path):
        readme_path = os.path.join(repo_path, "README.md")
        content = self._read_file(readme_path)
        if content:
            # Simple heuristic: find first paragraph after title
            paragraphs = re.split(r'\n\s*\n', content)
            for p in paragraphs:
                p = p.strip()
                if p and not p.startswith('#') and not p.startswith('[!'):
                    return p
        return None

    def infer_architecture(self, repo_path):
        arch_path = os.path.join(repo_path, "ARCHITECTURE.md")
        content = self._read_file(arch_path)
        if content:
            paragraphs = re.split(r'\n\s*\n', content)
            for p in paragraphs:
                p = p.strip()
                if p and not p.startswith('#') and not p.startswith('[!'):
                    return p
            
        docs_arch = os.path.join(repo_path, "docs", "architecture.md")
        content = self._read_file(docs_arch)
        if content:
            paragraphs = re.split(r'\n\s*\n', content)
            for p in paragraphs:
                p = p.strip()
                if p and not p.startswith('#') and not p.startswith('[!'):
                    return p

        # Check README for Architecture section
        readme_path = os.path.join(repo_path, "README.md")
        content = self._read_file(readme_path)
        if content:
            match = re.search(r'#+\s*Architecture(.*?)(?=\n#|$)', content, re.IGNORECASE | re.DOTALL)
            if match:
                arch_text = match.group(1).strip()
                paragraphs = re.split(r'\n\s*\n', arch_text)
                for p in paragraphs:
                    p = p.strip()
                    if p and not p.startswith('#') and not p.startswith('[!'):
                        return p
                
        return None

    def infer_impact(self, repo_path):
        readme_path = os.path.join(repo_path, "README.md")
        content = self._read_file(readme_path)
        metrics = {}
        if content:
            # Simplistic search for metrics or results
            match = re.search(r'#+\s*(?:Impact|Results)(.*?)(?=\n#|$)', content, re.IGNORECASE | re.DOTALL)
            if match:
                metrics["Impact: Result"] = match.group(1).strip()
        return metrics

    def infer_features(self, repo_path):
        readme_path = os.path.join(repo_path, "README.md")
        content = self._read_file(readme_path)
        features = []
        if content:
            match = re.search(r'#+\s*Features(.*?)(?=\n#|$)', content, re.IGNORECASE | re.DOTALL)
            if match:
                features_text = match.group(1).strip()
                for line in features_text.split('\n'):
                    line = line.strip()
                    line = re.sub(r'^[-*]\s*', '', line)
                    line = line.replace('**', '')
                    if line:
                        features.append(line)
        return features

    def resolve_gaps(self, repo_path: str, interactive: bool = False):
        target_capabilities = [
            "Project Description",
            "Architecture Rationale",
            "Impact: Situation",
            "Impact: Task",
            "Impact: Action",
            "Impact: Result"
        ]
        
        # Try LLM first
        inferred = {}
        features = []
        if os.environ.get("GEMINI_API_KEY"):
            click.echo("Using Gemini LLM for documentation summarization...")
            docs_content = self._gather_docs(repo_path)
            if docs_content:
                llm_summary = summarize_project(docs_content)
                if llm_summary:
                    if llm_summary.get("description"):
                        inferred["Project Description"] = llm_summary["description"]
                    if llm_summary.get("architecture_rationale"):
                        inferred["Architecture Rationale"] = llm_summary["architecture_rationale"]
                    if llm_summary.get("impact"):
                        imp = llm_summary["impact"]
                        if imp.get("situation"): inferred["Impact: Situation"] = imp["situation"]
                        if imp.get("task"): inferred["Impact: Task"] = imp["task"]
                        if imp.get("action"): inferred["Impact: Action"] = imp["action"]
                        if imp.get("result"): inferred["Impact: Result"] = imp["result"]
                    if llm_summary.get("features"):
                        features = llm_summary["features"]

        # Fallbacks to heuristics
        if "Project Description" not in inferred:
            desc = self.infer_description(repo_path)
            if desc: inferred["Project Description"] = desc
        
        if "Architecture Rationale" not in inferred:
            arch = self.infer_architecture(repo_path)
            if arch: inferred["Architecture Rationale"] = arch
        
        if "Impact: Result" not in inferred:
            inferred.update(self.infer_impact(repo_path))
        
        if not features:
            features = self.infer_features(repo_path)
            
        for feat in features:
            if not self.db.has_capability(feat):
                self._save_gap(repo_path, feat, "", source="inference", category="Feature")
                click.echo(f"Auto-inferred Feature from documentation: {feat}")
        
        for gap in target_capabilities:
            cached_value = self.db.get_evidence_value(gap)
            auto_val = inferred.get(gap)
            
            if gap.startswith("Impact:"):
                click.echo(f"\n--- Knowledge Gap: {gap} ---")
                if auto_val:
                    click.echo(f"[LLM Inferred]: {auto_val}")
                
                answer = click.prompt(f"Add manual {gap} (leave empty to use LLM inference only)", type=str, default="", show_default=False)
                
                final_val = auto_val or ""
                if answer and answer.strip():
                    if final_val:
                        final_val = f"{final_val}\n{answer.strip()}"
                    else:
                        final_val = answer.strip()
                
                if final_val:
                    self._save_gap(repo_path, gap, final_val, source="human" if answer.strip() else "inference")
                    click.echo(f"Stored {gap}.")
                else:
                    click.echo(f"Skipped {gap}.")
            else:
                # If we auto-inferred something, always overwrite cache to keep it fresh
                if auto_val:
                    self._save_gap(repo_path, gap, auto_val, source="inference")
                    click.echo(f"Auto-inferred {gap} from documentation.")
                    continue
                    
                # If not auto-inferred, and not cached, OR interactive mode requested
                if not cached_value or interactive:
                    click.echo(f"\\n--- Knowledge Gap: {gap} ---")
                    answer = ""
                    if gap in ["Project Description", "Architecture Rationale"]:
                        click.echo(f"Please provide a detailed {gap}. Opening your default text editor...")
                        default_text = cached_value if cached_value else f"\\n# Enter {gap} below\\n"
                        answer = click.edit(text=default_text)
                        if answer:
                            answer = answer.replace(f"# Enter {gap} below\\n", "").strip()
                    else:
                        answer = click.prompt(f"Please provide {gap}", type=str, default=cached_value or "")
                        
                    if answer and answer.strip():
                        self._save_gap(repo_path, gap, answer.strip(), source="human")
                        click.echo(f"Stored {gap}.")
                    else:
                        click.echo(f"Skipped {gap}.")

    def _save_gap(self, repo_path, gap, value, source="human", category="Portfolio"):
        cap_id = self.db.add_capability(name=gap, category=category)
        # Clear old evidence so we just have the latest
        self.db.clear_capability_evidence(cap_id)
        
        analysis_id = self.db.record_analysis(project_path=repo_path)
        evidence_id = self.db.add_evidence(
            analysis_id=analysis_id,
            source_type=source,
            source_reference="docs" if source == "inference" else "cli_prompt",
            extracted_key=gap,
            extracted_value=value,
            confidence=1.0 if source == "human" else 0.8
        )
        self.db.link_capability_evidence(cap_id, evidence_id)
