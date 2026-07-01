from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
import hashlib
from database import SessionLocal
from models import APIKey, User
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/keys", tags=["Key Management"])

# Reusing the generate function from Day 1
def generate_api_key():
    raw_key = secrets.token_urlsafe(32)
    formatted_key = f"mf_live_{raw_key}"
    key_hash = hashlib.sha256(formatted_key.encode()).hexdigest()
    return formatted_key, key_hash

@router.post("/")
def create_key(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    raw_key, hashed_key = generate_api_key()
    
    new_key = APIKey(
        key_hash=hashed_key,
        prefix=raw_key[:12], # Store the prefix so the UI can show "mf_live_ABCD..." 
        user_id=current_user.id
    )
    db.add(new_key)
    db.commit()
    
    # This is the ONLY time the user will ever see the raw key
    return {"message": "Store this key safely. It will not be shown again.", "api_key": raw_key}

@router.delete("/{key_id}")
def revoke_key(key_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Find the key and ensure it belongs to the requesting user
    db_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == current_user.id).first()
    
    if not db_key:
        raise HTTPException(status_code=404, detail="Key not found")
    if not db_key.is_active:
        raise HTTPException(status_code=400, detail="Key is already revoked")
        
    # Soft delete
    db_key.is_active = False
    db_key.revoked_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Key successfully revoked."}