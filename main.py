from fastapi import FastAPI, HTTPException

app = FastAPI()

# Our "Memory Ledger" to count visitors
request_counts = {}

@app.get("/secure-data")
async def get_data():
    user_ip = "127.0.0.1" # Pretending this is the user's ID
    
    # Logic: If they aren't in memory, add them. 
    # If they are, increase their count.
    if user_ip not in request_counts:
        request_counts[user_ip] = 1
    else:
        request_counts[user_ip] += 1
        
    # If they click too fast (more than 5 times), block them!
    if request_counts[user_ip] > 5:
        raise HTTPException(status_code=429, detail="Too many requests! Slow down.")

    return {
        "message": "Welcome to the secure vault!", 
        "your_hits": request_counts[user_ip]
    }