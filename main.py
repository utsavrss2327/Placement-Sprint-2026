import time
import fakeredis
from fastapi import FastAPI, Request, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel # <-- NEW IMPORT

from database import SessionLocal, APIUser, SecureNote, generate_api_key # <-- Added SecureNote

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

# --- Pydantic Schema for receiving data ---
class NoteCreate(BaseModel):
    content: str

def send_welcome_email(username: str):
    print(f"\n[BACKGROUND TASK STARTED] Preparing to send welcome email to {username}...")
    time.sleep(5) 
    print(f"[BACKGROUND TASK COMPLETE] Welcome email successfully sent to {username}!\n")

@app.post("/generate-key/")
def create_api_key(username: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing_user = db.query(APIUser).filter(APIUser.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists!")
    
    new_key = generate_api_key()
    new_user = APIUser(username=username, api_key=new_key)
    db.add(new_user)
    db.commit()
    
    background_tasks.add_task(send_welcome_email, username)
    return {"message": "Key generated!", "username": username, "api_key": new_key}

# --- The Middleware (Upgraded with request.state) ---
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
        
    # --- NEW: Stick a post-it note on the request with the username! ---
    request.state.username = user.username
        
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

# --- NEW: The Core Business Logic Endpoint ---
@app.post("/notes/")
def create_secure_note(note: NoteCreate, request: Request, db: Session = Depends(get_db)):
    # 1. Read the post-it note left by the middleware
    owner_username = request.state.username
    
    # 2. Save the note to the database under their name
    new_note = SecureNote(username=owner_username, content=note.content)
    db.add(new_note)
    db.commit()
    
    # 3. Return a success response
    return {
        "message": "Vault note securely saved!", 
        "owner": owner_username, 
        "saved_content": note.content
    }

# --- NEW: Endpoint to Retrieve Your Notes ---
@app.get("/notes/")
def get_my_notes(request: Request, db: Session = Depends(get_db)):
    # 1. Who is asking? Read the post-it note from the middleware
    owner_username = request.state.username
    
    # 2. Query the database for ONLY the notes belonging to this user
    user_notes = db.query(SecureNote).filter(SecureNote.username == owner_username).all()
    
    # 3. Format the notes into a clean list and return them
    formatted_notes = [{"id": note.id, "content": note.content} for note in user_notes]
    
    return {
        "owner": owner_username,
        "total_notes": len(formatted_notes),
        "notes": formatted_notes
    }