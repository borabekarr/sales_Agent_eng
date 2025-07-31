from fastapi import FastAPI

app = FastAPI(title="Sales Assistant Backend - Debug")

@app.get("/")
async def root():
    return {"message": "Debug version running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Debug mode - basic health check"}

# Test basic imports one by one
@app.get("/test-imports")
async def test_imports():
    results = {}
    
    try:
        from services.assembly_ai import AssemblyAIService
        results["assembly_ai"] = "✅ OK"
    except Exception as e:
        results["assembly_ai"] = f"❌ {str(e)}"
    
    try:
        from services.gemini_api import GeminiAPIService
        results["gemini_api"] = "✅ OK"
    except Exception as e:
        results["gemini_api"] = f"❌ {str(e)}"
    
    try:
        from services.conversation import ConversationService
        results["conversation"] = "✅ OK"
    except Exception as e:
        results["conversation"] = f"❌ {str(e)}"
    
    try:
        from agents.orchestrator import ConversationOrchestrator
        results["orchestrator"] = "✅ OK"
    except Exception as e:
        results["orchestrator"] = f"❌ {str(e)}"
    
    try:
        from services.feedback_service import FeedbackService
        results["feedback_service"] = "✅ OK"
    except Exception as e:
        results["feedback_service"] = f"❌ {str(e)}"
    
    return {"import_test_results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
