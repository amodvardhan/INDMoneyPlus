"""Database models for agent orchestrator"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class AgentRun(Base):
    __tablename__ = "agent_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    flow_type = Column(String, nullable=False, index=True)  # "analysis", "rebalance", "execution_prep"
    input_json = Column(JSON, nullable=False)
    output_json = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="running", index=True)  # "running", "completed", "failed", "pending_approval"
    executed_by = Column(Integer, nullable=True)  # User ID who executed/approved
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    action_logs = relationship("AgentActionLog", back_populates="agent_run", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_agent_runs_user_flow', 'user_id', 'flow_type'),
        Index('ix_agent_runs_status', 'status'),
    )


class AgentActionLog(Base):
    __tablename__ = "agent_action_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step = Column(Integer, nullable=False)  # Step number in the workflow
    tool_called = Column(String, nullable=False, index=True)  # Name of tool/service called
    tool_input = Column(JSON, nullable=True)  # Input to the tool
    tool_output = Column(JSON, nullable=True)  # Output from the tool
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    agent_run = relationship("AgentRun", back_populates="action_logs")
    
    __table_args__ = (
        Index('ix_agent_action_logs_run_step', 'agent_run_id', 'step'),
    )

