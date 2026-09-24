import json
import os
import subprocess
import re
import requests

def update_portfolio_projects(portfolio_data_dir: str, project_name: str, knowledge_graph_path: str):
    projects_file = os.path.join(portfolio_data_dir, "projects.json")
    
    # 1. Load the knowledge graph
    with open(knowledge_graph_path, 'r') as f:
        kg = json.load(f)
        
    # Extract some basic info from KG to populate the project
    capabilities = kg.get("capabilities", [])
    milestones = kg.get("milestones", [])
    
    # Fetch live links from GitHub API
    repo_dir = os.path.dirname(knowledge_graph_path)
    github_url = ""
    live_url = ""
    try:
        remote_url = subprocess.check_output(
            ["git", "-C", repo_dir, "config", "--get", "remote.origin.url"], 
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        
        match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?', remote_url)
        if match:
            owner, repo = match.groups()
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            try:
                res = requests.get(api_url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    github_url = data.get("html_url", "")
                    homepage = data.get("homepage", "")
                    if homepage:
                        live_url = homepage
            except Exception:
                pass
    except Exception:
        pass
    
    # Extract tech stack (e.g., from capabilities with category 'Language' or 'Dependency')
    tech_stack = []
    for cap in capabilities:
        if cap.get("category") in ["Language", "Dependency"]:
            # e.g., "Language: Python" -> "Python"
            name = cap.get("name", "")
            if ": " in name:
                tech_stack.append(name.split(": ")[1])
            else:
                tech_stack.append(name)
    
    features = [cap.get("name") for cap in capabilities if cap.get("category") not in ["Language", "Dependency", "Portfolio", "Contributor"]]
    
    # Extract Portfolio fields
    description = "Automatically extracted from dev-knowledge."
    rationale = ""
    situation = ""
    task = ""
    action = ""
    result = ""
    
    for cap in capabilities:
        name = cap.get("name")
        evidence = cap.get("evidence", [])
        if not evidence:
            continue
            
        value = evidence[0].get("value", "")
        
        if name == "Project Description":
            description = value
        elif name == "Architecture Rationale":
            rationale = value
        elif name == "Impact: Situation":
            situation = value
        elif name == "Impact: Task":
            task = value
        elif name == "Impact: Action":
            action = value
        elif name == "Impact: Result":
            result = value
            
    # 2. Load existing projects
    projects = []
    if os.path.exists(projects_file):
        with open(projects_file, 'r') as f:
            try:
                projects = json.load(f)
            except json.JSONDecodeError:
                projects = []
                
    # Sort existing projects by order to ensure we have a clean list
    for i, p in enumerate(projects):
        if "order" not in p:
            p["order"] = i + 1
            
    projects.sort(key=lambda x: x.get("order", float('inf')))
    
    # 3. Match project by Github URL repo name or ID
    existing_idx = -1
    project_id = project_name.lower() # Default ID for new projects
    
    for i, p in enumerate(projects):
        p_github = p.get("githubUrl", "")
        url_match = re.search(r'github\.com[:/][^/]+/([^/.]+)', p_github)
        if url_match and url_match.group(1).lower() == project_name.lower():
            existing_idx = i
            project_id = p.get("id")
            break
        elif p.get("id", "").lower() == project_name.lower() or p.get("id", "").lower() == f"proj-{project_name.lower()}":
            existing_idx = i
            project_id = p.get("id")
            break
            
    if existing_idx != -1:
        # Continuous Update: update fields, keep existing order
        p = projects[existing_idx]
        
        # Don't overwrite description and features with bad inference
        # p["techStack"] = list(set(p.get("techStack", []) + tech_stack))
        # p["features"] = list(set(p.get("features", []) + features))
        # if description != "Automatically extracted from dev-knowledge.":
        #     p["description"] = description
        if rationale:
            if "architectureDiagram" not in p:
                p["architectureDiagram"] = {"nodes": [], "edges": []}
            p["architectureDiagram"]["rationale"] = rationale
            
        if situation or task or action or result:
            if "impactMetrics" not in p:
                p["impactMetrics"] = {}
            if situation: p["impactMetrics"]["situation"] = situation
            if task: p["impactMetrics"]["task"] = task
            if action: p["impactMetrics"]["action"] = action
            if result: p["impactMetrics"]["result"] = result
            
        if milestones:
            if "progression" not in p:
                p["progression"] = {"commitHistory": [], "milestones": []}
            p["progression"]["milestones"] = milestones
            
        if github_url:
            p["githubUrl"] = github_url
        if live_url:
            p["liveUrl"] = live_url
            
        # Keep existing order, title, etc.
    else:
        # New Project: insert at 4th position (index 3)
        impact_metrics = {}
        if situation: impact_metrics["situation"] = situation
        if task: impact_metrics["task"] = task
        if action: impact_metrics["action"] = action
        if result: impact_metrics["result"] = result

        new_project = {
            "id": project_id,
            "title": project_name.replace("-", " ").title(),
            "category": "Personal",  # Default
            "description": description,
            "techStack": tech_stack,
            "features": features,
            "githubUrl": github_url,
            "liveUrl": live_url,
            "architectureDiagram": {
                "nodes": [],
                "edges": []
            },
            "progression": {
                "commitHistory": [],
                "milestones": milestones
            }
        }
        
        if rationale:
            new_project["architectureDiagram"]["rationale"] = rationale
            
        if impact_metrics:
            new_project["impactMetrics"] = impact_metrics
        
        insert_idx = min(3, len(projects))
        projects.insert(insert_idx, new_project)
        
    # 4. Re-assign orders cleanly from 1 to N
    for i, p in enumerate(projects):
        p["order"] = i + 1
        
    # 5. Write back to projects.json
    with open(projects_file, 'w') as f:
        json.dump(projects, f, indent=2)
        
    return projects
