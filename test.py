from fastapi import FastAPI

app = FastAPI()

# This is our 'Logic' endpoint
@app.get("/add")
def add_numbers(num1: int, num2: int):
    result = num1 + num2
    return {"message": "Success", "sum": result}