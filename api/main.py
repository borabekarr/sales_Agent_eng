from fastapi import APIRouter

router = APIRouter()

@router.post("/start_call")
async def start_call(customer: dict):
    # Add your logic to start a call here
    print(f"Starting call with {customer['customer']}")
    return {"status": "Call started", "customer": customer['customer']}

@router.post("/test_call")
async def test_call():
    # Add your logic for a test call here
    print("Starting test call")
    return {"status": "Test call started"} 