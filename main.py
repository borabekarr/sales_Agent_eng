from fastapi import FastAPI
import datetime

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "🚀 DEPLOYMENT TEST 🚀": "SUCCESS",
        "message": "THIS IS DEFINITELY OUR APP RUNNING",
        "timestamp": str(datetime.datetime.now()),
        "test_id": "RAILWAY_TEST_2024_07_31_FINAL",
        "status": "✅ Working perfectly!"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "message": "✅ OUR HEALTH ENDPOINT IS WORKING",
        "app": "sales_assistant_backend"
    }

@app.get("/obvious-test")
def obvious_test():
    return {
        "🎯 OBVIOUS TEST": "If you see this, Railway is serving our app!",
        "railway_working": True,
        "deployment_successful": True,
        "next_step": "Add full sales assistant features"
    }
