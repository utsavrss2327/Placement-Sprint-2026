import fakeredis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse  # Import this!

app = FastAPI()

r = fakeredis.FakeRedis(decode_responses=True)

LIMIT = 5
WINDOW_SIZE = 60 

@app.middleware("http")
async def redis_rate_limiter(request: Request, call_next):
    client_ip = request.client.host
    redis_key = f"rate_limit:{client_ip}"
    
    current_requests = r.get(redis_key)
    
    if current_requests is not None:
        current_requests = int(current_requests)
        
        if current_requests >= LIMIT:
            # FIX: Instead of raising a raw error, return a clean JSON response
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests via Mock Redis! Slow down."}
            )
        
        r.incr(redis_key)
    else:
        r.setex(redis_key, WINDOW_SIZE, 1)
            
    response = await call_next(request)
    return response

@app.get("/")
def home():
    return {"message": "FastAPI + Mock Redis Rate Limiter is officially live!"}