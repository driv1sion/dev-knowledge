import os
import json
import pytest
from devknowledge.portfolio.updater import update_portfolio_projects

@pytest.fixture
def temp_portfolio(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    kg_path = tmp_path / "kg.json"
    kg_data = {
        "capabilities": [
            {"category": "Language", "name": "Language: Python"},
            {"category": "Dependency", "name": "Dependency: pytest"},
            {"category": "Concept", "name": "REST API"}
        ],
        "milestones": ["Milestone 1"]
    }
    with open(kg_path, "w") as f:
        json.dump(kg_data, f)
        
    return str(data_dir), str(kg_path)

def test_new_project_ordering(temp_portfolio):
    data_dir, kg_path = temp_portfolio
    
    # Let's create an existing projects.json with 5 projects
    projects_file = os.path.join(data_dir, "projects.json")
    existing_projects = [
        {"id": "proj-1", "title": "P1", "order": 1},
        {"id": "proj-2", "title": "P2", "order": 2},
        {"id": "proj-3", "title": "P3", "order": 3},
        {"id": "proj-4", "title": "P4", "order": 4},
        {"id": "proj-5", "title": "P5", "order": 5}
    ]
    with open(projects_file, "w") as f:
        json.dump(existing_projects, f)
        
    update_portfolio_projects(data_dir, "new-proj", kg_path)
    
    with open(projects_file, "r") as f:
        updated = json.load(f)
        
    assert len(updated) == 6
    assert updated[0]["id"] == "proj-1"
    assert updated[1]["id"] == "proj-2"
    assert updated[2]["id"] == "proj-3"
    assert updated[3]["id"] == "proj-new-proj"
    assert updated[3]["order"] == 4
    assert updated[4]["id"] == "proj-4"
    assert updated[4]["order"] == 5
    assert updated[5]["id"] == "proj-5"
    assert updated[5]["order"] == 6
    
    # Check populated fields
    assert "Python" in updated[3]["techStack"]
    assert "pytest" in updated[3]["techStack"]
    assert "REST API" in updated[3]["features"]

def test_continuous_updates(temp_portfolio):
    data_dir, kg_path = temp_portfolio
    
    projects_file = os.path.join(data_dir, "projects.json")
    existing_projects = [
        {"id": "proj-1", "title": "P1", "order": 1},
        {"id": "proj-exist", "title": "Exist", "order": 2, "techStack": ["OldTech"]},
        {"id": "proj-3", "title": "P3", "order": 3}
    ]
    with open(projects_file, "w") as f:
        json.dump(existing_projects, f)
        
    update_portfolio_projects(data_dir, "exist", kg_path)
    
    with open(projects_file, "r") as f:
        updated = json.load(f)
        
    assert len(updated) == 3
    assert updated[1]["id"] == "proj-exist"
    assert updated[1]["order"] == 2
    assert "OldTech" in updated[1]["techStack"]
    assert "Python" in updated[1]["techStack"]
