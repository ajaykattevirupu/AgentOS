# backend/app/init_db.py
from app.models.agent import Base
from app.core.database import engine

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized!")

if __name__ == "__main__":
    init_db()