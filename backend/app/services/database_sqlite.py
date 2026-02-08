"""
VeriFlow - SQLite Service Layer (Lightweight alternative)
Handles database operations for sessions and executions using SQLite.
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

class SQLiteDB:
    def __init__(self, db_path='veriflow.db'):
        self.db_path = Path(db_path)
        # Ensure the parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            # Add workflow_complete column
            try:
                cursor.execute("ALTER TABLE agent_sessions ADD COLUMN workflow_complete BOOLEAN DEFAULT FALSE")
            except sqlite3.OperationalError:
                # Column already exists, which is fine
                pass

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    run_id TEXT PRIMARY KEY,
                    scholar_extraction_complete BOOLEAN,
                    scholar_isa_json_path TEXT,
                    engineer_workflow_id TEXT,
                    engineer_cwl_path TEXT,
                    workflow_complete BOOLEAN DEFAULT FALSE
                )
            ''')
            conn.commit()

    def create_or_update_agent_session(
        self,
        run_id: str,
        **kwargs: Any
    ):
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT run_id FROM agent_sessions WHERE run_id = ?", (run_id,))
            exists = cursor.fetchone()
            
            columns = list(kwargs.keys())
            values = list(kwargs.values())
            
            if exists:
                set_clause = ", ".join([f"{col} = ?" for col in columns])
                sql = f"UPDATE agent_sessions SET {set_clause} WHERE run_id = ?"
                values.append(run_id)
                cursor.execute(sql, tuple(values))
            else:
                columns.append("run_id")
                values.append(run_id)
                placeholders = ", ".join(["?"] * len(columns))
                sql = f"INSERT INTO agent_sessions ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(sql, tuple(values))
                
            conn.commit()

    def get_agent_session(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_sessions WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None

database_service = SQLiteDB(db_path="db/veriflow.db")