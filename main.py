import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World", "Railway_Test": "SUCCESS", "Port": os.getenv("PORT", "8000")}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test")
def test():
    return {"test": "Railway is working!", "env_vars": {
        "PORT": os.getenv("PORT"),
        "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "not_set")
    }}
