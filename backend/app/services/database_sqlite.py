"""
VeriFlow - SQLite Service Layer
Handles database operations for sessions and executions using SQLite.
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SQLiteDB:
    def __init__(self, db_path='db/veriflow.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    run_id TEXT PRIMARY KEY,
                    scholar_extraction_complete BOOLEAN,
                    scholar_isa_json_path TEXT,
                    engineer_workflow_id TEXT,
                    engineer_cwl_path TEXT,
                    workflow_complete BOOLEAN DEFAULT FALSE,
                    agent_directives TEXT,
                    user_context TEXT
                )
            ''')
            
            # Migrations
            cursor.execute("PRAGMA table_info(agent_sessions)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if "workflow_complete" not in columns:
                cursor.execute("ALTER TABLE agent_sessions ADD COLUMN workflow_complete BOOLEAN DEFAULT FALSE")
            
            if "agent_directives" not in columns:
                cursor.execute("ALTER TABLE agent_sessions ADD COLUMN agent_directives TEXT")

            if "user_context" not in columns:
                cursor.execute("ALTER TABLE agent_sessions ADD COLUMN user_context TEXT")
                logger.info("Migrated DB: Added user_context column")

            conn.commit()

    def create_or_update_agent_session(self, run_id: str, **kwargs: Any):
        """
        Updates the session.
        """
        if "agent_directives" in kwargs and isinstance(kwargs["agent_directives"], dict):
            kwargs["agent_directives"] = json.dumps(kwargs["agent_directives"])

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
                data = dict(row)
                if data.get("agent_directives"):
                    try:
                        data["agent_directives"] = json.loads(data["agent_directives"])
                    except json.JSONDecodeError:
                        data["agent_directives"] = {}
                else:
                    data["agent_directives"] = {}
                return data
            return None
            
    def get_full_state_mock(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Reconstruct state from DB session + files.
        Crucial for restarts: retrieves persisted user_context.
        """
        session = self.get_agent_session(run_id)
        if not session:
            return None
            
        state = {
            "run_id": run_id,
            "agent_directives": session.get("agent_directives", {}),
            "user_context": session.get("user_context"), # <--- RETRIEVE CONTEXT
            # We assume paths are re-provided or stored elsewhere for full robustness,
            # but for this logic we ensure context is safe.
        }
        
        # Load Scholar Output
        if session.get("scholar_isa_json_path") and os.path.exists(session["scholar_isa_json_path"]):
            with open(session["scholar_isa_json_path"], 'r') as f:
                state["isa_json"] = json.load(f)
                
        # Load Engineer Output
        if session.get("engineer_cwl_path") and os.path.exists(session["engineer_cwl_path"]):
            with open(session["engineer_cwl_path"], 'r') as f:
                state["generated_code"] = json.load(f)
                
        return state

database_service = SQLiteDB(db_path="db/veriflow.db")