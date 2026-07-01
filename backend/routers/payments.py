from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from auth import get_current_user
import stripe
import os

router = APIRouter(prefix="/payments", tags=["Payments"])

# Set your secret keys (in production, use environment variables)
stripe.api_key = "sk_test_your_stripe_secret_key"
STRIPE_WEBHOOK_SECRET = "whsec_your_webhook_secret"

# Replace with an actual Price ID from your Stripe Dashboard
PRO_PLAN_PRICE_ID = "price_1Pabc123..." 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create-checkout-session")
def create_checkout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Generates a secure Stripe hosted checkout page for the user to enter their card.
    """
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[{
                'price': PRO_PLAN_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url="http://localhost:3000/dashboard?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:3000/dashboard",
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    """
    Stripe hits this endpoint automatically when a payment succeeds or fails.
    """
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event when a subscription is successfully created and paid
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session['customer_details']['email']
        stripe_customer_id = session['customer']

        # Find the user and upgrade their account
        user = db.query(User).filter(User.email == customer_email).first()
        if user:
            user.stripe_customer_id = stripe_customer_id
            user.plan_tier = "pro"
            user.subscription_status = "active"
            db.commit()

    return {"status": "success"}