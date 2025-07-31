from fastapi import FastAPI

app = FastAPI(title="Sales Assistant Backend - Debug Mode v2")

@app.get("/")
async def root():
    return {
        "message": "DEBUG MODE v2 - UPDATED", 
        "status": "debug_running",
        "version": "2024-07-31-v2"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "message": "DEBUG MODE v2 - Health check working",
        "debug": True
    }

@app.get("/debug-imports")
async def debug_imports():
    """Test imports one by one to identify failures"""
    results = {"debug_version": "v2", "timestamp": "2024-07-31"}
    
    # Test core imports first
    try:
        import os
        results["os"] = "✅ OK"
    except Exception as e:
        results["os"] = f"❌ {str(e)}"
    
    try:
        from utils.config import get_settings
        results["config"] = "✅ OK"
    except Exception as e:
        results["config"] = f"❌ {str(e)}"
    
    try:
        from services.assembly_ai import AssemblyAIService
        results["assembly_ai"] = "✅ OK"
    except Exception as e:
        results["assembly_ai"] = f"❌ {str(e)[:200]}"
    
    try:
        from services.gemini_api import GeminiAPIService
        results["gemini_api"] = "✅ OK"
    except Exception as e:
        results["gemini_api"] = f"❌ {str(e)[:200]}"
    
    try:
        from agents.orchestrator import ConversationOrchestrator
        results["orchestrator"] = "✅ OK"
    except Exception as e:
        results["orchestrator"] = f"❌ {str(e)[:200]}"
    
    try:
        from services.feedback_service import FeedbackService
        results["feedback_service"] = "✅ OK"
    except Exception as e:
        results["feedback_service"] = f"❌ {str(e)[:200]}"
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
