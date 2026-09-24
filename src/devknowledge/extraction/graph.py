import json
from devknowledge.core.db import DBManager

def generate_knowledge_graph(db_path: str, output_path: str):
    """
    Exports the SQLite state into a static JSON-LD formatted Knowledge Graph.
    """
    db = DBManager(db_path)
    
    # In a full implementation, we would query the database properly
    # This is an MVP demonstrating the schema layout
    graph = {
        "@context": "https://schema.org/",
        "@type": "SoftwareSourceCode",
        "capabilities": [],
        "milestones": []
    }
    
    with db._get_conn() as conn:
        # Extract capabilities and their evidence
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category FROM capabilities")
        for cap_row in cursor.fetchall():
            cap_id, name, category = cap_row
            
            # Get evidence for this capability
            evidence_list = []
            ev_cursor = conn.cursor()
            ev_cursor.execute("""
                SELECT e.source_type, e.source_reference, e.confidence, e.extracted_value 
                FROM evidence e
                JOIN capability_evidence ce ON e.id = ce.evidence_id
                WHERE ce.capability_id = ?
            """, (cap_id,))
            
            for ev_row in ev_cursor.fetchall():
                evidence_list.append({
                    "type": ev_row[0],
                    "reference": ev_row[1],
                    "confidence": ev_row[2],
                    "value": ev_row[3]
                })
                
            graph["capabilities"].append({
                "@id": f"#cap-{cap_id}",
                "name": name,
                "category": category,
                "evidence": evidence_list
            })
            
    with open(output_path, 'w') as f:
        json.dump(graph, f, indent=2)
    
    return graph
