from fastapi import FastAPI, HTTPException, status

# This is the line you are missing!
app = FastAPI()

BANNED_USERS = {"spam_bot", "hacker123", "bad_actor"}

@app.get("/login/{username}")
def login(username: str):
    # We convert the input to lowercase so 'Hacker123' becomes 'hacker123'
    name_to_check = username.lower()
    
    if name_to_check in BANNED_USERS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")
    
    return {"status": "Success", "message": f"Welcome, {username}!"}