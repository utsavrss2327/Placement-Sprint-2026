import time
import fakeredis
from fastapi import FastAPI, Request, Depends, HTTPException, status, BackgroundTasks
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

# --- NEW: The Heavy Background Task ---
def send_welcome_email(username: str):
    print(f"\n[BACKGROUND TASK STARTED] Preparing to send welcome email to {username}...")
    time.sleep(5) # Simulating a slow 5-second process (like connecting to an email server)
    print(f"[BACKGROUND TASK COMPLETE] Welcome email successfully sent to {username}!\n")

# --- 1. Endpoint: Generate Key (Upgraded with BackgroundTasks) ---
@app.post("/generate-key/")
def create_api_key(username: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing_user = db.query(APIUser).filter(APIUser.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists!")
    
    new_key = generate_api_key()
    new_user = APIUser(username=username, api_key=new_key)
    db.add(new_user)
    db.commit()
    
    # Command FastAPI to run this function AFTER sending the instant response to the user
    background_tasks.add_task(send_welcome_email, username)
    
    return {
        "message": "Key generated! Look at your Mac terminal in exactly 5 seconds.", 
        "username": username, 
        "api_key": new_key
    }

# --- 2. The Global Middleware (Unchanged) ---
@app.middleware("http")
async def secure_rate_limiter(request: Request, call_next):
    if request.url.path in ["/docs", "/openapi.json", "/generate-key/"]:
        return await call_next(request)
        
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return JSONResponse(status_code=401, content={"detail": "Missing API Key header."})
        
    db = SessionLocal()
    user = db.query(APIUser).filter(APIUser.api_key == api_key).first()
    db.close()
    
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Invalid API Key."})
        
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

# --- 3. Protected Resource Endpoint (Unchanged) ---
@app.get("/data/")
def get_secret_data():
    return {"message": "If you are reading this, your API key is valid and you are not rate-limited!"}