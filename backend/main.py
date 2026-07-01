import time
import hashlib
import httpx
from fastapi import FastAPI, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import APIKey, ManagedAPI
from routers import apis, keys
from tasks import log_api_request
from routers import apis, keys, billing
import redis.asyncio as redis
from routers import apis, keys, billing, payments

# Create all database tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MeterFlow API Billing Platform")

# Attach the routes from your 'routers' folder
app.include_router(apis.router)
app.include_router(keys.router)
app.include_router(billing.router)
app.include_router(payments.router)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# DAY 5-6: API GATEWAY (CORE MIDDLEWARE)
# ==========================================

async def verify_api_key(request: Request, db: Session = Depends(get_db)):
    """
    STEP 1: VALIDATE API KEY
    This runs before the request is allowed to go through.
    """
    api_key_header = request.headers.get("X-API-Key")
    
    if not api_key_header:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    
    # Hash the incoming key to match what is stored in the database
    key_hash = hashlib.sha256(api_key_header.encode()).hexdigest()
    
    # Look up the key (Note: In production, this specific query should be cached in Redis)
    db_key = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
    
    if not db_key:
        raise HTTPException(status_code=403, detail="Invalid or revoked API Key")
        
    return db_key


@app.api_route("/proxy/{api_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_proxy(
    api_name: str, 
    path: str, 
    request: Request, 
    api_key: APIKey = Depends(verify_api_key), 
    db: Session = Depends(get_db)
):
    """
    STEP 2 & 3: FORWARD REQUEST & LOG USAGE
    This acts as a catch-all route. If a user hits /proxy/my-api/users, 
    it finds "my-api" in the DB and forwards the request to its actual URL.
    """
    start_time = time.time()
    
    # Find where this request is supposed to go
    target_api = db.query(ManagedAPI).filter(ManagedAPI.name == api_name).first()
    if not target_api:
        raise HTTPException(status_code=404, detail="Target API not found in MeterFlow")
        
    # Construct the final destination URL
    target_url = f"{target_api.target_url}/{path}"
    
    # Extract the body if it's a POST/PUT request
    body = await request.body()
    
    # Forward the request using httpx
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=dict(request.headers), # Pass the user's headers through
                content=body,
                params=request.query_params
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Bad Gateway: Could not reach target API")

    # Calculate how long the request took
    process_time = time.time() - start_time

    # STEP 3: LOG THE REQUEST (Asynchronous)
    # This triggers the Celery worker you set up in tasks.py so it doesn't slow down the gateway
    log_api_request.delay(
        key_id=api_key.id,
        endpoint=target_url,
        method=request.method,
        status_code=response.status_code,
        latency=process_time
    )

    # Return the target API's response back to the user
    return response.json()

redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

# Define your limit (e.g., 60 requests per minute)
RATE_LIMIT = 60 
WINDOW_SECONDS = 60 

# ... (keep your existing verify_api_key function)

# ==========================================
# DAY 12: RATE LIMITING DEPENDENCY
# ==========================================
async def check_rate_limit(api_key: APIKey = Depends(verify_api_key)):
    """
    Checks Redis to see if the API key has exceeded its allowed requests.
    Uses a Fixed Window algorithm (counting requests per minute).
    """
    # 1. Create a unique Redis key tied to the current minute and the user's API key
    current_minute = int(time.time() // WINDOW_SECONDS)
    redis_key = f"rate_limit:{api_key.key_hash}:{current_minute}"
    
    # 2. Increment the counter in Redis
    request_count = await redis_client.incr(redis_key)
    
    # 3. If this is the first request in the window, set the key to expire
    if request_count == 1:
        await redis_client.expire(redis_key, WINDOW_SECONDS)
        
    # 4. Block the request if they are over the limit
    if request_count > RATE_LIMIT:
        raise HTTPException(
            status_code=429, 
            detail="Too Many Requests. Your rate limit has been exceeded."
        )
        
    return api_key

# ==========================================
# UPDATE THE GATEWAY PROXY
# ==========================================
@app.api_route("/proxy/{api_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_proxy(
    api_name: str, 
    path: str, 
    request: Request, 
    # UPDATE: Change the dependency here from verify_api_key to check_rate_limit
    api_key: APIKey = Depends(check_rate_limit), 
    db: Session = Depends(get_db)
):
    
    start_time = time.time()
    