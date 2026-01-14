from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class AgentStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    task = Column(String, nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.PENDING)
    
    # Config
    provider = Column(String)  # "openai", "anthropic"
    model = Column(String)
    config = Column(JSON)
    
    # Execution
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer)
    checkpoint_data = Column(JSON)
    
    # Metrics
    cost_usd = Column(Float, default=0.0)
    runtime_seconds = Column(Integer, default=0)
    
    # Trust metrics
    confidence_score = Column(Float)
    estimated_cost_min = Column(Float)
    estimated_cost_max = Column(Float)
    estimated_runtime_min = Column(Integer)
    estimated_runtime_max = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    result = Column(JSON)
    error = Column(String)


class AgentEvent(Base):
    __tablename__ = "agent_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False, index=True)
    
    step = Column(Integer)
    action = Column(String)  # "llm_call", "tool_use", "checkpoint", etc
    status = Column(String)  # "running", "completed", "failed"
    
    data = Column(JSON)
    cost_usd = Column(Float, default=0.0)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)