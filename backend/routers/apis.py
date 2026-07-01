from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import ManagedAPI, User
from auth import get_current_user # From your Day 1-2 auth logic
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/apis", tags=["API Management"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class APICreate(BaseModel):
    name: str
    target_url: str
    description: Optional[str] = None
    metadata_config: Optional[dict] = {}

@router.post("/")
def create_api(api_data: APICreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_api = ManagedAPI(
        name=api_data.name,
        target_url=api_data.target_url,
        description=api_data.description,
        metadata_config=api_data.metadata_config,
        user_id=current_user.id
    )
    db.add(new_api)
    db.commit()
    db.refresh(new_api)
    return new_api