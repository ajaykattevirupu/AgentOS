from typing import List, Dict, Any, Optional
import uuid
import time
from datetime import datetime
from app.core.llm_providers import get_provider
from app.models.agent import Agent, AgentStatus, AgentEvent
from app.core.database import SessionLocal
import redis
import json

class AgentExecutor:
    def __init__(self, agent_id: str, db_session):
        self.agent_id = agent_id
        self.db = db_session
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # Load agent from DB
        self.agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not self.agent:
            raise ValueError(f"Agent {agent_id} not found")
    
    def emit_event(self, action: str, status: str, data: Dict = None, cost: float = 0.0):
        """Emit an event and broadcast via Redis"""
        event = AgentEvent(
            agent_id=self.agent_id,
            step=self.agent.current_step,
            action=action,
            status=status,
            data=data or {},
            cost_usd=cost
        )
        self.db.add(event)
        self.db.commit()
        
        # Broadcast to Redis for real-time updates
        self.redis_client.publish(
            f'agent:{self.agent_id}',
            json.dumps({
                'agent_id': self.agent_id,
                'action': action,
                'status': status,
                'step': self.agent.current_step,
                'data': data,
                'cost': cost,
                'timestamp': datetime.utcnow().isoformat()
            })
        )
    
    def save_checkpoint(self, state: Dict):
        """Save checkpoint for resume capability"""
        self.agent.checkpoint_data = state
        self.agent.current_step = state.get('current_step', 0)
        self.db.commit()
        
        self.emit_event(
            action='checkpoint_saved',
            status='completed',
            data={'step': self.agent.current_step}
        )
    
    def check_kill_signal(self) -> bool:
        """Check if user requested kill"""
        kill_signal = self.redis_client.get(f'kill:{self.agent_id}')
        return kill_signal == '1'
    
    def check_budget(self, estimated_next_cost: float = 0) -> bool:
        """Check if we're approaching budget limit"""
        max_cost = self.agent.config.get('max_cost_usd', 10.0)
        current_cost = self.agent.cost_usd
        
        if current_cost + estimated_next_cost > max_cost * 0.9:
            return False
        return True
    
    async def execute_step(self, step_config: Dict) -> Dict[str, Any]:
        """Execute a single step"""
        step_num = step_config['step_number']
        self.agent.current_step = step_num
        
        # Check kill signal
        if self.check_kill_signal():
            raise Exception("Agent killed by user")
        
        # Check budget
        if not self.check_budget(estimated_next_cost=0.5):
            self.agent.status = AgentStatus.PAUSED
            self.db.commit()
            self.emit_event(
                action='budget_pause',
                status='paused',
                data={'reason': 'Approaching budget limit'}
            )
            raise Exception("Paused: approaching budget limit")
        
        # Execute LLM call
        provider = get_provider(
            provider=self.agent.provider,
            api_key=self.agent.config.get('api_key'),
            model=self.agent.model
        )
        
        prompt = step_config['prompt']
        
        self.emit_event(
            action='llm_call',
            status='running',
            data={
                'provider': self.agent.provider,
                'model': self.agent.model,
                'prompt_preview': prompt[:100] + '...'
            }
        )
        
        start_time = time.time()
        result = await provider.complete(prompt)
        duration = time.time() - start_time
        
        # Update agent cost
        self.agent.cost_usd += result['cost_usd']
        self.db.commit()
        
        self.emit_event(
            action='llm_response',
            status='completed',
            data={
                'tokens': result['tokens_total'],
                'duration_seconds': round(duration, 2),
                'response_preview': result['content'][:200] + '...'
            },
            cost=result['cost_usd']
        )
        
        return result
    
    async def run(self):
        """Main execution loop"""
        try:
            self.agent.status = AgentStatus.RUNNING
            self.agent.started_at = datetime.utcnow()
            self.db.commit()
            
            self.emit_event(
                action='agent_started',
                status='running',
                data={'task': self.agent.task}
            )
            
            # Simple workflow for MVP: just execute the task as one LLM call
            # Later: break into multiple steps, tools, etc.
            
            step_config = {
                'step_number': 1,
                'prompt': f"Task: {self.agent.task}\n\nPlease complete this task and provide a detailed response."
            }
            
            result = await self.execute_step(step_config)
            
            # Save result
            self.agent.result = {
                'content': result['content'],
                'tokens': result['tokens_total'],
                'cost': result['cost_usd']
            }
            self.agent.status = AgentStatus.COMPLETED
            self.agent.completed_at = datetime.utcnow()
            self.agent.runtime_seconds = int((self.agent.completed_at - self.agent.started_at).total_seconds())
            self.db.commit()
            
            self.emit_event(
                action='agent_completed',
                status='completed',
                data={
                    'runtime_seconds': self.agent.runtime_seconds,
                    'total_cost': self.agent.cost_usd
                }
            )
            
            return self.agent.result
            
        except Exception as e:
            self.agent.status = AgentStatus.FAILED
            self.agent.error = str(e)
            self.db.commit()
            
            self.emit_event(
                action='agent_failed',
                status='failed',
                data={'error': str(e)}
            )
            
            raise