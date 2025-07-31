from fastapi import FastAPI
import os

app = FastAPI(title="Sales Assistant Backend - FORCE UPDATE")

@app.get("/")
async def root():
    return {
        "message": "FORCE UPDATE - This is definitely our app!", 
        "status": "running_our_code",
        "version": "FORCE-2024-07-31",
        "environment_check": {
            "port": os.getenv("PORT", "not_set"),
            "has_gemini_key": "GEMINI_API_KEY" in os.environ,
            "has_assembly_key": "ASSEMBLY_AI_API_KEY" in os.environ
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "message": "FORCE UPDATE - Our health endpoint",
        "app": "sales_assistant_backend"
    }

@app.get("/test")
async def test():
    return {"test": "This proves our app is running", "timestamp": "2024-07-31"}

@app.get("/debug-imports")
async def debug_imports():
    """Test imports to find the problem"""
    results = {"status": "testing_imports", "app": "sales_assistant"}
    
    try:
        import sys
        results["python_path"] = sys.path[:3]  # First 3 paths
    except Exception as e:
        results["python_path"] = f"Error: {e}"
    
    try:
        import os
        results["environment"] = {
            "PORT": os.getenv("PORT"),
            "PYTHONPATH": os.getenv("PYTHONPATH"),
            "PWD": os.getenv("PWD")
        }
    except Exception as e:
        results["environment"] = f"Error: {e}"
    
    # Test if our modules exist
    try:
        import services
        results["services_module"] = "✅ Found"
    except Exception as e:
        results["services_module"] = f"❌ {str(e)}"
    
    try:
        import agents
        results["agents_module"] = "✅ Found"
    except Exception as e:
        results["agents_module"] = f"❌ {str(e)}"
    
    try:
        import utils
        results["utils_module"] = "✅ Found"
    except Exception as e:
        results["utils_module"] = f"❌ {str(e)}"
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
