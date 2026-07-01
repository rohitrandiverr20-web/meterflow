from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./meterflow.db")

# We will swap this to your PostgreSQL URL later, using SQLite for now to get auth working
SQLALCHEMY_DATABASE_URL = "sqlite:///./meterflow.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Add this inside your database.py file
def get_db():
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()