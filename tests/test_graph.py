import os
import json
from devknowledge.extraction.graph import generate_knowledge_graph
from devknowledge.core.db import DBManager

def test_generate_knowledge_graph(tmpdir):
    db_path = os.path.join(tmpdir, "test.db")
    db = DBManager(db_path)
    db.initialize()
    
    cap_id = db.add_capability("GraphQL", "API")
    analysis_id = db.record_analysis("/tmp")
    ev_id = db.add_evidence(analysis_id, "file", "schema.graphql", "api", "graphql")
    db.link_capability_evidence(cap_id, ev_id)
    
    out_path = os.path.join(tmpdir, "out.json")
    graph = generate_knowledge_graph(db_path, out_path)
    
    assert os.path.exists(out_path)
    
    with open(out_path) as f:
        data = json.load(f)
        assert data["@type"] == "SoftwareSourceCode"
        assert len(data["capabilities"]) == 1
        assert data["capabilities"][0]["name"] == "GraphQL"
        assert len(data["capabilities"][0]["evidence"]) == 1
        assert data["capabilities"][0]["evidence"][0]["reference"] == "schema.graphql"
