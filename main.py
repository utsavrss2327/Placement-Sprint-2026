import fakeredis
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import SessionLocal, APIUser, generate_api_key

app = FastAPI()
r = fakeredis.FakeRedis(decode_responses=True)

LIMIT = 5
WINDOW_SIZE = 60 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 1. Endpoint: Generate Key ---
@app.post("/generate-key/")
def create_api_key(username: str, db: Session = Depends(get_db)):
    existing_user = db.query(APIUser).filter(APIUser.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists!")
    
    new_key = generate_api_key()
    new_user = APIUser(username=username, api_key=new_key)
    db.add(new_user)
    db.commit()
    
    return {"message": "Key generated!", "username": username, "api_key": new_key}

# --- 2. The Upgraded Global Middleware ---
@app.middleware("http")
async def secure_rate_limiter(request: Request, call_next):
    # Bypass the security check for our documentation and key generation routes
    if request.url.path in ["/docs", "/openapi.json", "/generate-key/"]:
        return await call_next(request)
        
    # Extract the API key from the request headers
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        return JSONResponse(status_code=401, content={"detail": "Missing API Key header."})
        
    # Open a quick database session to verify the key
    db = SessionLocal()
    user = db.query(APIUser).filter(APIUser.api_key == api_key).first()
    db.close()
    
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Invalid API Key."})
        
    # Rate limit based on their unique USERNAME, not their IP!
    redis_key = f"rate_limit:{user.username}"
    
    current_requests = r.get(redis_key)
    if current_requests is not None:
        if int(current_requests) >= LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests, {user.username}! Slow down."}
            )
        r.incr(redis_key)
    else:
        r.setex(redis_key, WINDOW_SIZE, 1)
            
    return await call_next(request)

# --- 3. Protected Resource Endpoint ---
@app.get("/data/")
def get_secret_data():
    return {"message": "If you are reading this, your API key is valid and you are not rate-limited!"}