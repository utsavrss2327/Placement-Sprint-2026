import time
from fastapi import FastAPI, Request, HTTPException, status

app = FastAPI()

# This will store: { "ip_address": {"count": int, "start_time": float} }
rate_limit_track = {}

# Configuration: Max 5 requests per 60 seconds
LIMIT = 5
WINDOW_SIZE = 60 

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    
    if client_ip not in rate_limit_track:
        # First time seeing this IP, initialize the window
        rate_limit_track[client_ip] = {"count": 1, "start_time": current_time}
    else:
        user_data = rate_limit_track[client_ip]
        
        # Check if the 60-second window has passed
        if current_time - user_data["start_time"] > WINDOW_SIZE:
            # Window expired! Reset the counter and start a new window
            user_data["count"] = 1
            user_data["start_time"] = current_time
        else:
            # Still inside the window, increment the count
            user_data["count"] += 1
            
        # Check if they breached the limit inside the active window
        if user_data["count"] > LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests! Slow down."
            )
            
    response = await call_next(request)
    return response
@app.get("/")
def home():
    return {"message": "Welcome to the API! Hit refresh to test the rate limiter."}