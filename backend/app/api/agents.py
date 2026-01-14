from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.agent import Agent, AgentStatus
from app.core.orchestrator import AgentExecutor
from app.core.events import EventService

router = APIRouter()

class AgentCreate(BaseModel):
    task: str
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str  # User's own API key
    max_cost_usd: float = 10.0

class AgentResponse(BaseModel):
    id: str
    task: str
    status: str
    current_step: int
    total_steps: Optional[int]
    cost_usd: float
    runtime_seconds: int
    confidence_score: Optional[float]
    estimated_cost_min: Optional[float]
    estimated_cost_max: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[dict]
    error: Optional[str]

async def run_agent_background(agent_id: str):
    """Background task to run agent"""
    from app.core.database import get_db_context
    
    with get_db_context() as db:
        executor = AgentExecutor(agent_id, db)
        await executor.run()

@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent: AgentCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create and start a new agent"""
    agent_id = str(uuid.uuid4())
    
    # Create agent in DB
    new_agent = Agent(
        id=agent_id,
        task=agent.task,
        provider=agent.provider,
        model=agent.model,
        status=AgentStatus.PENDING,
        config={
            'api_key': agent.api_key,  # In production, encrypt this!
            'max_cost_usd': agent.max_cost_usd
        },
        total_steps=1,  # Simple for now
        confidence_score=85.0,  # TODO: Calculate actual confidence
        estimated_cost_min=2.50,
        estimated_cost_max=4.00,
        estimated_runtime_min=120,
        estimated_runtime_max=300
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    # Start agent in background
    background_tasks.add_task(run_agent_background, agent_id)
    
    return AgentResponse(
        id=new_agent.id,
        task=new_agent.task,
        status=new_agent.status.value,
        current_step=new_agent.current_step,
        total_steps=new_agent.total_steps,
        cost_usd=new_agent.cost_usd,
        runtime_seconds=new_agent.runtime_seconds,
        confidence_score=new_agent.confidence_score,
        estimated_cost_min=new_agent.estimated_cost_min,
        estimated_cost_max=new_agent.estimated_cost_max,
        created_at=new_agent.created_at,
        started_at=new_agent.started_at,
        completed_at=new_agent.completed_at,
        result=new_agent.result,
        error=new_agent.error
    )

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent status"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        id=agent.id,
        task=agent.task,
        status=agent.status.value,
        current_step=agent.current_step,
        total_steps=agent.total_steps,
        cost_usd=agent.cost_usd,
        runtime_seconds=agent.runtime_seconds,
        confidence_score=agent.confidence_score,
        estimated_cost_min=agent.estimated_cost_min,
        estimated_cost_max=agent.estimated_cost_max,
        created_at=agent.created_at,
        started_at=agent.started_at,
        completed_at=agent.completed_at,
        result=agent.result,
        error=agent.error
    )

@router.get("/{agent_id}/timeline")
async def get_timeline(agent_id: str, db: Session = Depends(get_db)):
    """Get agent event timeline"""
    event_service = EventService(db)
    return {"timeline": event_service.get_timeline(agent_id)}

@router.post("/{agent_id}/kill")
async def kill_agent(agent_id: str, db: Session = Depends(get_db)):
    """Kill a running agent"""
    import redis
    redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
    redis_client.set(f'kill:{agent_id}', '1')
    
    return {"status": "kill_signal_sent", "agent_id": agent_id}

@router.post("/{agent_id}/resume")
async def resume_agent(
    agent_id: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resume a failed/paused agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.status not in [AgentStatus.FAILED, AgentStatus.PAUSED]:
        raise HTTPException(status_code=400, detail="Agent cannot be resumed")
    
    # Reset status
    agent.status = AgentStatus.PENDING
    agent.error = None
    db.commit()
    
    # Restart in background
    background_tasks.add_task(run_agent_background, agent_id)
    
    return {"status": "resuming", "agent_id": agent_id}