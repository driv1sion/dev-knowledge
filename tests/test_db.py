import pytest
import os
import tempfile
from devknowledge.core.db import DBManager

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DBManager(path)
    db.initialize()
    yield db
    os.unlink(path)

def test_db_initialization(temp_db):
    assert temp_db is not None
    # Check that tables exist
    with temp_db._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "analyses" in tables
        assert "evidence" in tables
        assert "capabilities" in tables
        assert "capability_evidence" in tables

def test_db_operations(temp_db):
    analysis_id = temp_db.record_analysis("/tmp/test")
    assert analysis_id
    
    cap_id = temp_db.add_capability("Test Cap", "Category")
    assert cap_id
    
    # Adding duplicate should return same id
    cap_id2 = temp_db.add_capability("Test Cap", "Category")
    assert cap_id == cap_id2
    
    ev_id = temp_db.add_evidence(analysis_id, "test", "ref", "key", "val")
    assert ev_id
    
    temp_db.link_capability_evidence(cap_id, ev_id)
    
    assert temp_db.has_capability("Test Cap")
    assert not temp_db.has_capability("Missing Cap")
