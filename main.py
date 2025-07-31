from fastapi import FastAPI

app = FastAPI(title="Sales Assistant Backend - Test")

@app.get("/")
async def root():
    return {"message": "Sales Assistant Backend is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Basic FastAPI deployment test"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
