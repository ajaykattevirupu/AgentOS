from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.agent import AgentEvent
from datetime import datetime, timedelta

class EventService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_agent_events(
        self, 
        agent_id: str, 
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[AgentEvent]:
        """Get events for an agent"""
        query = self.db.query(AgentEvent).filter(
            AgentEvent.agent_id == agent_id
        )
        
        if since:
            query = query.filter(AgentEvent.timestamp >= since)
        
        return query.order_by(AgentEvent.timestamp.desc()).limit(limit).all()
    
    def get_timeline(self, agent_id: str) -> List[dict]:
        """Get formatted timeline for display"""
        events = self.get_agent_events(agent_id)
        
        timeline = []
        for event in reversed(events):  # Chronological order
            timeline.append({
                'timestamp': event.timestamp.isoformat(),
                'action': event.action,
                'status': event.status,
                'step': event.step,
                'data': event.data,
                'cost': event.cost_usd
            })
        
        return timeline
    
    def get_agent_cost(self, agent_id: str) -> float:
        """Calculate total cost from events"""
        total = self.db.query(AgentEvent).filter(
            AgentEvent.agent_id == agent_id
        ).with_entities(
            func.sum(AgentEvent.cost_usd)
        ).scalar()
        
        return total or 0.0