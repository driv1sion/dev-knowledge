import sqlite3
import os
import uuid
from datetime import datetime

class DBManager:
    def __init__(self, db_path: str = "knowledge.db"):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def initialize(self):
        """Initializes the database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            project_path TEXT,
            commit_sha TEXT,
            analyzed_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            analysis_id TEXT REFERENCES analyses(id),
            source_type TEXT,
            source_reference TEXT,
            extracted_key TEXT,
            extracted_value TEXT,
            confidence REAL
        );

        CREATE TABLE IF NOT EXISTS capabilities (
            id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT
        );

        CREATE TABLE IF NOT EXISTS capability_evidence (
            capability_id TEXT REFERENCES capabilities(id),
            evidence_id TEXT REFERENCES evidence(id)
        );
        """
        with self._get_conn() as conn:
            conn.executescript(schema)
            conn.commit()

    def record_analysis(self, project_path: str, commit_sha: str = "unknown") -> str:
        analysis_id = str(uuid.uuid4())
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO analyses (id, project_path, commit_sha, analyzed_at) VALUES (?, ?, ?, ?)",
                (analysis_id, project_path, commit_sha, datetime.now())
            )
            conn.commit()
        return analysis_id

    def add_evidence(self, analysis_id: str, source_type: str, source_reference: str, 
                     extracted_key: str, extracted_value: str, confidence: float = 1.0) -> str:
        evidence_id = str(uuid.uuid4())
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO evidence (id, analysis_id, source_type, source_reference, extracted_key, extracted_value, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (evidence_id, analysis_id, source_type, source_reference, extracted_key, extracted_value, confidence)
            )
            conn.commit()
        return evidence_id
    
    def add_capability(self, name: str, category: str = "general") -> str:
        capability_id = str(uuid.uuid4())
        with self._get_conn() as conn:
            # Avoid duplicates by name (in a more complex schema this would have a UNIQUE constraint)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM capabilities WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            
            conn.execute(
                "INSERT INTO capabilities (id, name, category) VALUES (?, ?, ?)",
                (capability_id, name, category)
            )
            conn.commit()
        return capability_id
    
    def link_capability_evidence(self, capability_id: str, evidence_id: str):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO capability_evidence (capability_id, evidence_id) VALUES (?, ?)",
                (capability_id, evidence_id)
            )
            conn.commit()

    def clear_capability_evidence(self, capability_id: str):
        """Removes existing evidence links for a capability so they can be overwritten."""
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM capability_evidence WHERE capability_id = ?",
                (capability_id,)
            )
            conn.commit()

    def get_evidence_value(self, capability_name: str) -> str:
        """Retrieves the latest extracted value for a given capability name."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.extracted_value 
                FROM evidence e
                JOIN capability_evidence ce ON e.id = ce.evidence_id
                JOIN capabilities c ON c.id = ce.capability_id
                WHERE c.name = ?
                ORDER BY e.id DESC LIMIT 1
            """, (capability_name,))
            row = cursor.fetchone()
            return row[0] if row else None

    def has_capability(self, name: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM capabilities WHERE name = ?", (name,))
            return cursor.fetchone() is not None
