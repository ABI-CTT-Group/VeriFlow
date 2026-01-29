-- VeriFlow PostgreSQL Database Schema
-- Per SPEC.md Section 3.6

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent Sessions table
-- Stores session state for Scholar, Engineer, and Reviewer agents
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Scholar agent state
    scholar_extraction_complete BOOLEAN DEFAULT FALSE,
    scholar_isa_json_path TEXT,
    scholar_confidence_scores_path TEXT,
    scholar_context_used TEXT,
    
    -- Engineer agent state
    engineer_workflow_id VARCHAR(255),
    engineer_cwl_path TEXT,
    engineer_tools_generated JSONB DEFAULT '[]'::jsonb,
    engineer_adapters_generated JSONB DEFAULT '[]'::jsonb,
    
    -- Reviewer agent state
    reviewer_validations_passed BOOLEAN DEFAULT FALSE,
    reviewer_validation_errors JSONB DEFAULT '[]'::jsonb,
    reviewer_suggestions JSONB DEFAULT '[]'::jsonb
);

-- Conversation History table
-- Stores messages for Gemini API context
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    agent VARCHAR(50) NOT NULL CHECK (agent IN ('scholar', 'engineer', 'reviewer'))
);

-- Executions table
-- Tracks workflow execution status
CREATE TABLE IF NOT EXISTS executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) NOT NULL,
    dag_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'success', 'partial_failure', 'failed')),
    overall_progress INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    node_statuses JSONB DEFAULT '{}'::jsonb,
    logs JSONB DEFAULT '[]'::jsonb
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agent_sessions_upload_id ON agent_sessions(upload_id);
CREATE INDEX IF NOT EXISTS idx_conversation_history_session_id ON conversation_history(session_id);
CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);

-- Updated at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_agent_sessions_updated_at
    BEFORE UPDATE ON agent_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_executions_updated_at
    BEFORE UPDATE ON executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
