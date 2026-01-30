"""
VeriFlow - PostgreSQL Service Layer
Handles database operations for sessions and executions.
"""

import os
import json
from typing import Optional, List
from datetime import datetime
import asyncpg
from contextlib import asynccontextmanager

from app.models.session import AgentSession, Message, ScholarState, EngineerState, ReviewerState
from app.models.execution import ExecutionStatus, LogEntry


class DatabaseService:
    """Service layer for PostgreSQL database operations."""
    
    def __init__(self):
        """Initialize database connection parameters."""
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://veriflow:veriflow123@localhost:5432/veriflow"
        )
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Create database connection pool."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.database_url)
    
    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if self.pool is None:
            await self.connect()
        async with self.pool.acquire() as conn:
            yield conn
    
    # Session operations
    async def create_session(self, upload_id: str) -> AgentSession:
        """Create a new agent session."""
        session = AgentSession(upload_id=upload_id)
        
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO agent_sessions (
                    session_id, upload_id, created_at, updated_at,
                    scholar_extraction_complete, scholar_isa_json_path,
                    scholar_confidence_scores_path, scholar_context_used,
                    engineer_workflow_id, engineer_cwl_path,
                    engineer_tools_generated, engineer_adapters_generated,
                    reviewer_validations_passed, reviewer_validation_errors,
                    reviewer_suggestions
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """,
                session.session_id,
                session.upload_id,
                datetime.fromisoformat(session.created_at),
                datetime.fromisoformat(session.updated_at),
                session.scholar_state.extraction_complete,
                session.scholar_state.isa_json_path,
                session.scholar_state.confidence_scores_path,
                session.scholar_state.context_used,
                session.engineer_state.workflow_id,
                session.engineer_state.cwl_path,
                json.dumps(session.engineer_state.tools_generated),
                json.dumps(session.engineer_state.adapters_generated),
                session.reviewer_state.validations_passed,
                json.dumps(session.reviewer_state.validation_errors),
                json.dumps(session.reviewer_state.suggestions),
            )
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get a session by ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent_sessions WHERE session_id = $1",
                session_id,
            )
        
        if row is None:
            return None
        
        return self._row_to_session(row)
    
    async def get_session_by_upload(self, upload_id: str) -> Optional[AgentSession]:
        """Get a session by upload ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent_sessions WHERE upload_id = $1 ORDER BY created_at DESC LIMIT 1",
                upload_id,
            )
        
        if row is None:
            return None
        
        return self._row_to_session(row)
    
    async def update_session(self, session: AgentSession) -> None:
        """Update an existing session."""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                UPDATE agent_sessions SET
                    updated_at = $2,
                    scholar_extraction_complete = $3,
                    scholar_isa_json_path = $4,
                    scholar_confidence_scores_path = $5,
                    scholar_context_used = $6,
                    engineer_workflow_id = $7,
                    engineer_cwl_path = $8,
                    engineer_tools_generated = $9,
                    engineer_adapters_generated = $10,
                    reviewer_validations_passed = $11,
                    reviewer_validation_errors = $12,
                    reviewer_suggestions = $13
                WHERE session_id = $1
                """,
                session.session_id,
                datetime.utcnow(),
                session.scholar_state.extraction_complete,
                session.scholar_state.isa_json_path,
                session.scholar_state.confidence_scores_path,
                session.scholar_state.context_used,
                session.engineer_state.workflow_id,
                session.engineer_state.cwl_path,
                json.dumps(session.engineer_state.tools_generated),
                json.dumps(session.engineer_state.adapters_generated),
                session.reviewer_state.validations_passed,
                json.dumps(session.reviewer_state.validation_errors),
                json.dumps(session.reviewer_state.suggestions),
            )
    
    def _row_to_session(self, row) -> AgentSession:
        """Convert a database row to AgentSession."""
        return AgentSession(
            session_id=str(row["session_id"]),
            upload_id=row["upload_id"],
            created_at=row["created_at"].isoformat(),
            updated_at=row["updated_at"].isoformat(),
            scholar_state=ScholarState(
                extraction_complete=row["scholar_extraction_complete"],
                isa_json_path=row["scholar_isa_json_path"],
                confidence_scores_path=row["scholar_confidence_scores_path"],
                context_used=row["scholar_context_used"],
            ),
            engineer_state=EngineerState(
                workflow_id=row["engineer_workflow_id"],
                cwl_path=row["engineer_cwl_path"],
                tools_generated=json.loads(row["engineer_tools_generated"]) if row["engineer_tools_generated"] else [],
                adapters_generated=json.loads(row["engineer_adapters_generated"]) if row["engineer_adapters_generated"] else [],
            ),
            reviewer_state=ReviewerState(
                validations_passed=row["reviewer_validations_passed"],
                validation_errors=json.loads(row["reviewer_validation_errors"]) if row["reviewer_validation_errors"] else [],
                suggestions=json.loads(row["reviewer_suggestions"]) if row["reviewer_suggestions"] else [],
            ),
        )
    
    # Conversation history operations
    async def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to conversation history."""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO conversation_history (session_id, role, content, timestamp, agent)
                VALUES ($1, $2, $3, $4, $5)
                """,
                session_id,
                message.role.value,
                message.content,
                datetime.fromisoformat(message.timestamp),
                message.agent.value,
            )
    
    async def get_conversation_history(self, session_id: str) -> List[Message]:
        """Get conversation history for a session."""
        async with self.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM conversation_history 
                WHERE session_id = $1 
                ORDER BY timestamp ASC
                """,
                session_id,
            )
        
        return [
            Message(
                id=str(row["id"]),
                role=row["role"],
                content=row["content"],
                timestamp=row["timestamp"].isoformat(),
                agent=row["agent"],
            )
            for row in rows
        ]
    
    # Execution operations
    async def create_execution(
        self,
        workflow_id: str,
        dag_id: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> str:
        """Create a new execution record."""
        import uuid
        execution_id = str(uuid.uuid4())
        
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO executions (execution_id, workflow_id, dag_id, status, config)
                VALUES ($1, $2, $3, $4, $5)
                """,
                execution_id,
                workflow_id,
                dag_id,
                ExecutionStatus.QUEUED.value,
                json.dumps(config or {}),
            )
        
        return execution_id
    
    async def get_execution(self, execution_id: str) -> Optional[dict]:
        """Get execution by ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM executions WHERE execution_id = $1",
                execution_id,
            )
        
        if row is None:
            return None
        
        return {
            "execution_id": str(row["execution_id"]),
            "workflow_id": row["workflow_id"],
            "dag_id": row["dag_id"],
            "status": row["status"],
            "overall_progress": row["overall_progress"],
            "config": json.loads(row["config"]) if row["config"] else {},
            "node_statuses": json.loads(row["node_statuses"]) if row["node_statuses"] else {},
            "logs": json.loads(row["logs"]) if row["logs"] else [],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
            "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
        }
    
    async def update_execution_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        overall_progress: int = 0,
        node_statuses: Optional[dict] = None,
    ) -> None:
        """Update execution status."""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                UPDATE executions SET
                    status = $2,
                    overall_progress = $3,
                    node_statuses = $4,
                    updated_at = $5,
                    completed_at = CASE WHEN $2 IN ('success', 'failed', 'partial_failure') THEN $5 ELSE NULL END
                WHERE execution_id = $1
                """,
                execution_id,
                status.value,
                overall_progress,
                json.dumps(node_statuses or {}),
                datetime.utcnow(),
            )
    
    async def add_execution_log(self, execution_id: str, log_entry: LogEntry) -> None:
        """Add a log entry to execution."""
        async with self.get_connection() as conn:
            # Append to logs JSON array
            await conn.execute(
                """
                UPDATE executions 
                SET logs = logs || $2::jsonb
                WHERE execution_id = $1
                """,
                execution_id,
                json.dumps([log_entry.model_dump()]),
            )


# Global service instance
db_service = DatabaseService()
