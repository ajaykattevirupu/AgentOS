from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import redis.asyncio as redis
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, agent_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
    
    def disconnect(self, agent_id: str):
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
    
    async def send_message(self, agent_id: str, message: dict):
        if agent_id in self.active_connections:
            await self.active_connections[agent_id].send_json(message)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    await manager.connect(agent_id, websocket)
    
    # Subscribe to Redis pub/sub for this agent
    redis_client = await redis.Redis(host='redis', port=6379, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f'agent:{agent_id}')
    
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await websocket.send_json(data)
    except WebSocketDisconnect:
        manager.disconnect(agent_id)
        await pubsub.unsubscribe(f'agent:{agent_id}')
        await redis_client.close()