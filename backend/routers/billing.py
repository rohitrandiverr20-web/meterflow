from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from database import SessionLocal
from models import User, APIKey, UsageLog
from auth import get_current_user

router = APIRouter(prefix="/billing", tags=["Billing & Usage"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define SaaS Pricing Constants
FREE_TIER_LIMIT = 1000
COST_PER_REQUEST = 0.005

@router.get("/current-usage")
def get_current_usage(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Calculates the real-time usage and accrued cost for the current month.
    """
    # 1. Determine the current month (e.g., June 2026)
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    # 2. Join UsageLogs with APIKeys to count only this user's requests for the month
    total_requests = db.query(func.count(UsageLog.id)).join(APIKey).filter(
        APIKey.user_id == current_user.id,
        UsageLog.timestamp >= start_of_month
    ).scalar() or 0

    # 3. Apply Pricing Logic
    billable_requests = max(0, total_requests - FREE_TIER_LIMIT)
    accrued_cost = billable_requests * COST_PER_REQUEST

    return {
        "billing_period": now.strftime("%Y-%m"),
        "total_requests": total_requests,
        "free_tier_allowance": FREE_TIER_LIMIT,
        "billable_requests": billable_requests,
        "current_cost_usd": round(accrued_cost, 2)
    }