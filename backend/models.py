from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="developer") # Roles: developer, admin
    
    stripe_customer_id = Column(String, nullable=True)
    plan_tier = Column(String, default="free") # Options: free, pro
    subscription_status = Column(String, default="inactive")
    
    api_keys = relationship("APIKey", back_populates="owner")

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    prefix = Column(String, index=True) # Useful for identifying keys later
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="api_keys")
    
class ManagedAPI(Base):
    __tablename__ = "managed_apis"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    target_url = Column(String) # The actual backend URL MeterFlow will proxy to
    metadata_config = Column(JSON, default={}) # Store extra config like default rate limits
    
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="managed_apis")
    # You might want to link API keys directly to specific APIs or keep them account-wide


    
# Open models.py and add this to the bottom of the file:

class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Stores which API Key was used (linked to the api_keys table)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), index=True)
    
    # Stores the exact URL/endpoint hit
    endpoint = Column(String, nullable=False)
    
    # Stores the HTTP response status (e.g., 200, 404, 429)
    status_code = Column(Integer, nullable=False)
    
    # Stores the exact time the request occurred
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Optional but highly recommended additions for billing analytics:
    method = Column(String, nullable=False)  # GET, POST, etc.
    latency_ms = Column(Float, nullable=True) # How fast the target API responded

    # Relationship back to the API Key model
    api_key = relationship("APIKey")
    
# Add this to the bottom of models.py

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Billing details
    billing_period = Column(String, index=True)  # Format: "YYYY-MM" (e.g., "2026-06")
    total_requests = Column(Integer, default=0)
    amount_due = Column(Float, default=0.0)
    
    # Payment tracking
    status = Column(String, default="pending")  # Options: pending, paid, overdue
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Optional relationship
    user = relationship("User")
    
