from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.api import agents
from app.core.database import engine
from app.models.agent import Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgentOS API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])

@app.get("/")
def root():
    return {"message": "AgentOS API", "version": "0.1.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}