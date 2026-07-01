from celery import Celery
from database import SessionLocal
from models import UsageLog
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Inside tasks.py

def log_api_request():
    # Placeholder for your future Celery task
    pass

# Initialize Celery and point it to a local Redis instance
celery_app = Celery(
    "meterflow_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task(name="log_api_request")
def log_api_request(key_id: int, endpoint: str, status_code: int, method: str, latency: float):
    """
    This background task runs inside the Celery worker process.
    It takes the log data sent from the gateway and saves it to the database.
    """
    db = SessionLocal()
    try:
        new_log = UsageLog(
            api_key_id=key_id,
            endpoint=endpoint,
            status_code=status_code,
            method=method,
            latency_ms=latency * 1000 # Convert seconds to milliseconds
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Error executing background logging task: {e}")
        db.rollback()
    finally:
        db.close()