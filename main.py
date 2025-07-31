import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from agents.orchestrator import ConversationOrchestrator
from models.schemas import (
    SessionCreate, SessionResponse, SessionStatus, 
    ConversationState, SuggestionResponse, 
    ConversationSummary, PerformanceMetrics,
    InterruptRequest, AdvanceStageRequest
)
from services.assembly_ai import AssemblyAIService
from services.gemini_api import GeminiAPIService
from services.conversation import ConversationService
from utils.config import get_settings
from utils.logging import setup_logging, get_logger

# Add new imports for learning system
from services.feedback_service import FeedbackService
from services.learning_analysis_service import LearningAnalysisService
from services.enhanced_agent_service import EnhancedAgentService
from services.meeting_review_service import MeetingReviewService
from models.learning_schemas import (
    SuggestionFeedback, CustomerReaction, ConversationAnalysis, MeetingReview
)

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Global service instances
assembly_ai_service = AssemblyAIService()
gemini_api_service = GeminiAPIService()
conversation_service = ConversationService()

# Initialize learning services
feedback_service = FeedbackService()
learning_analysis_service = LearningAnalysisService()
enhanced_agent_service = EnhancedAgentService()
meeting_review_service = MeetingReviewService()

# Active sessions storage
active_sessions: Dict[str, ConversationOrchestrator] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Sales Assistant Backend")
    yield
    logger.info("Shutting down Sales Assistant Backend")
    # Cleanup active sessions
    for session_id in list(active_sessions.keys()):
        await cleanup_session(session_id)

# Initialize FastAPI app
from fastapi import FastAPI
from api.main import router as api_router
from services.conversation import router as conversation_router
from services.feedback_service import router as feedback_router
from services.learning_analysis_service import router as learning_analysis_router
from services.meeting_review_service import router as meeting_review_router

app = FastAPI(
    title="AI Sales Assistant API",
    description="Powering real-time sales conversations with AI.",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api", tags=["Calls"])
app.include_router(conversation_router, prefix="/api/conversation", tags=["Conversation"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(learning_analysis_router, prefix="/api/learning", tags=["Learning & Analysis"])
app.include_router(meeting_review_router, prefix="/api/review", tags=["Meeting Review"])


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the AI Sales Assistant API"}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "active_sessions": len(active_sessions)
    }

# Session Management Endpoints

@app.post("/start-session", response_model=SessionResponse)
async def start_session(session_data: SessionCreate):
    """Start a new conversation session"""
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize conversation orchestrator
        orchestrator = ConversationOrchestrator(
            session_id=session_id,
            user_id=session_data.user_id,
            assembly_ai_service=assembly_ai_service,
            gemini_api_service=gemini_api_service,
            conversation_service=conversation_service
        )
        
        # Store session
        active_sessions[session_id] = orchestrator
        websocket_connections[session_id] = []
        
        logger.info(f"Started session {session_id} for user {session_data.user_id}")
        
        return SessionResponse(
            session_id=session_id,
            status="active",
            start_time=datetime.utcnow(),
            current_stage="opening",
            configuration={
                "languages": ["en", "tr"],
                "speaker_diarization": True,
                "real_time_suggestions": True
            }
        )
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start session")

@app.post("/end-session/{session_id}")
async def end_session(session_id: str):
    """End a conversation session"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        orchestrator = active_sessions[session_id]
        
        # Generate final summary
        summary = await orchestrator.generate_session_summary()
        
        # Cleanup session
        await cleanup_session(session_id)
        
        logger.info(f"Ended session {session_id}")
        
        return {
            "session_id": session_id,
            "status": "ended",
            "end_time": datetime.utcnow(),
            "summary": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to end session")

@app.get("/session-status/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get current session status"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    orchestrator = active_sessions[session_id]
    
    return SessionStatus(
        session_id=session_id,
        status="active",
        current_stage=orchestrator.current_stage,
        start_time=orchestrator.start_time,
        last_activity=orchestrator.last_activity,
        message_count=len(orchestrator.conversation_history)
    )

# Conversation Management Endpoints

@app.get("/next-suggestion/{session_id}", response_model=SuggestionResponse)
async def get_next_suggestion(session_id: str):
    """Get the next AI suggestion"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    orchestrator = active_sessions[session_id]
    suggestion = await orchestrator.generate_next_suggestion()
    
    return suggestion

@app.post("/handle-interrupt/{session_id}")
async def handle_interrupt(session_id: str, request: InterruptRequest):
    """Handle customer interruption"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    orchestrator = active_sessions[session_id]
    result = await orchestrator.handle_interrupt(
        speaker=request.speaker,
        text=request.text,
        timestamp=request.timestamp
    )
    
    # Broadcast to connected WebSockets
    await broadcast_to_session(session_id, {
        "type": "interrupt_handled",
        "data": result
    })
    
    return result

@app.get("/conversation-state/{session_id}", response_model=ConversationState)
async def get_conversation_state(session_id: str):
    """Get current conversation state"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    orchestrator = active_sessions[session_id]
    
    return ConversationState(
        session_id=session_id,
        current_stage=orchestrator.current_stage,
        customer_profile=orchestrator.customer_profile,
        conversation_history=orchestrator.conversation_history[-10:],  # Last 10 messages
        context_stack=orchestrator.context_stack,
        last_suggestion=orchestrator.last_suggestion
    )

@app.post("/advance-stage/{session_id}")
async def advance_stage(session_id: str, request: AdvanceStageRequest):
    """Manually advance to next conversation stage"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    orchestrator = active_sessions[session_id]
    result = await orchestrator.advance_conversation_stage(request.target_stage)
    
    # Broadcast to connected WebSockets
    await broadcast_to_session(session_id, {
        "type": "stage_advanced",
        "data": result
    })
    
    return result

@app.get("/current-stage/{session_id}")
async def get_current_stage(session_id: str):
    """Get current sales stage information"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    orchestrator = active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "current_stage": orchestrator.current_stage,
        "stage_progress": orchestrator.get_stage_progress(),
        "suggested_actions": orchestrator.get_stage_actions()
    }

# Analytics Endpoints

@app.get("/conversation-summary/{session_id}", response_model=ConversationSummary)
async def get_conversation_summary(session_id: str):
    """Get conversation summary and analysis"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    orchestrator = active_sessions[session_id]
    summary = await orchestrator.generate_session_summary()
    
    return summary

@app.get("/performance-metrics/{session_id}", response_model=PerformanceMetrics)
async def get_performance_metrics(session_id: str):
    """Get performance metrics for the session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    orchestrator = active_sessions[session_id]
    metrics = await orchestrator.calculate_performance_metrics()
    
    return metrics

# Learning & Feedback Endpoints
@app.post("/feedback/suggestion")
async def record_suggestion_feedback(feedback: SuggestionFeedback):
    """Record feedback for an AI suggestion"""
    try:
        success = await feedback_service.record_suggestion_feedback(feedback)
        if success:
            return {"status": "success", "message": "Feedback recorded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record feedback")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")


@app.post("/feedback/customer-reaction")
async def record_customer_reaction(reaction: CustomerReaction):
    """Record customer reaction during conversation"""
    try:
        success = await feedback_service.record_customer_reaction(reaction)
        if success:
            return {"status": "success", "message": "Customer reaction recorded"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record reaction")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording reaction: {str(e)}")


@app.post("/learning/review-meeting/{session_id}")
async def conduct_meeting_review(
    session_id: str,
    customer_profile: Optional[Dict[str, Any]] = None
):
    """Conduct comprehensive post-meeting analysis and learning"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        review_results = await meeting_review_service.conduct_full_meeting_review(
            session_id=session_id,
            customer_profile=customer_profile
        )
        
        if "error" in review_results:
            raise HTTPException(status_code=500, detail=review_results["error"])
        
        return review_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meeting review failed: {str(e)}")


@app.post("/learning/queue-review/{session_id}")
async def queue_meeting_review(
    session_id: str,
    priority: str = "normal",
    customer_profile: Optional[Dict[str, Any]] = None
):
    """Queue a meeting for asynchronous review"""
    try:
        await meeting_review_service.queue_meeting_for_review(
            session_id=session_id,
            customer_profile=customer_profile,
            priority=priority
        )
        
        return {
            "status": "queued",
            "message": f"Meeting {session_id} queued for review",
            "priority": priority
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue review: {str(e)}")


@app.get("/learning/patterns/{agent_type}")
async def get_learning_patterns(
    agent_type: str,
    scenario: Optional[str] = None,
    days_back: int = 30
):
    """Get learning patterns for a specific agent"""
    try:
        patterns = await feedback_service.get_learning_patterns(
            agent_type=agent_type,
            scenario=scenario,
            days_back=days_back
        )
        
        return {
            "agent_type": agent_type,
            "scenario": scenario,
            "days_back": days_back,
            "patterns": patterns
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@app.get("/learning/agent-performance/{agent_type}")
async def get_agent_performance(agent_type: str):
    """Get performance metrics for a specific agent"""
    try:
        performance = await feedback_service.get_agent_performance_metrics(agent_type)
        
        return {
            "agent_type": agent_type,
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent performance: {str(e)}")


@app.get("/learning/summary")
async def get_learning_summary(days_back: int = 7):
    """Get summary of learning activities"""
    try:
        summary = await meeting_review_service.get_learning_summary(days_back=days_back)
        
        return {
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning summary: {str(e)}")


@app.get("/learning/optimization-report")
async def get_optimization_report():
    """Generate system optimization report"""
    try:
        report = await meeting_review_service.generate_system_optimization_report()
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate optimization report: {str(e)}")


@app.post("/learning/force-update")
async def force_learning_update(agent_type: Optional[str] = None):
    """Force update of learning data (clear caches, refresh patterns)"""
    try:
        await enhanced_agent_service.force_learning_update(agent_type=agent_type)
        
        return {
            "status": "success",
            "message": f"Learning data updated for {agent_type or 'all agents'}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to force learning update: {str(e)}")


@app.get("/learning/real-time-stats")
async def get_real_time_learning_stats():
    """Get real-time learning statistics"""
    try:
        stats = await enhanced_agent_service.get_real_time_learning_stats()
        
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning stats: {str(e)}")


# Enhanced suggestion endpoint that uses learning insights
@app.get("/enhanced-suggestion/{session_id}")
async def get_enhanced_suggestion(session_id: str, scenario_key: Optional[str] = None):
    """Get AI suggestion enhanced with learning insights"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        orchestrator = active_sessions[session_id]["orchestrator"]
        
        # Get current context
        context = orchestrator.conversation_service.get_current_context(session_id)
        
        # Generate enhanced suggestion
        suggestion = await enhanced_agent_service.generate_enhanced_suggestion(
            base_context=context,
            agent_type=context.current_stage,
            scenario_key=scenario_key
        )
        
        return {
            "session_id": session_id,
            "suggestion": suggestion,
            "enhanced": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced suggestion: {str(e)}")


# Learning health check endpoint
@app.get("/learning/health")
async def learning_health_check():
    """Check health of all learning services"""
    try:
        health_status = {
            "feedback_service": feedback_service.is_service_available(),
            "learning_analysis_service": learning_analysis_service.is_service_available(),
            "enhanced_agent_service": enhanced_agent_service.is_service_available(),
            "meeting_review_service": meeting_review_service.is_service_available(),
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if all services are healthy
        all_healthy = all(health_status[service] for service in [
            "feedback_service", "learning_analysis_service", 
            "enhanced_agent_service", "meeting_review_service"
        ])
        
        health_status["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# WebSocket Endpoints

@app.websocket("/ws/audio/{session_id}")
async def websocket_audio(websocket: WebSocket, session_id: str):
    """WebSocket for real-time audio processing"""
    await websocket.accept()
    
    if session_id not in active_sessions:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    orchestrator = active_sessions[session_id]
    websocket_connections[session_id].append(websocket)
    
    try:
        logger.info(f"Audio WebSocket connected for session {session_id}")
        
        # Initialize Assembly AI connection
        await orchestrator.start_audio_processing(websocket)
        
        while True:
            # Receive audio data from client
            data = await websocket.receive_bytes()
            
            # Process audio through Assembly AI
            await orchestrator.process_audio_data(data)
            
    except WebSocketDisconnect:
        logger.info(f"Audio WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Audio WebSocket error for session {session_id}: {e}")
    finally:
        # Cleanup
        if websocket in websocket_connections.get(session_id, []):
            websocket_connections[session_id].remove(websocket)
        await orchestrator.stop_audio_processing()

@app.websocket("/ws/suggestions/{session_id}")
async def websocket_suggestions(websocket: WebSocket, session_id: str):
    """WebSocket for real-time AI suggestions"""
    await websocket.accept()
    
    if session_id not in active_sessions:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    orchestrator = active_sessions[session_id]
    websocket_connections[session_id].append(websocket)
    
    try:
        logger.info(f"Suggestions WebSocket connected for session {session_id}")
        
        # Send initial suggestion
        initial_suggestion = await orchestrator.generate_next_suggestion()
        await websocket.send_json({
            "type": "suggestion",
            "data": initial_suggestion.dict()
        })
        
        # Keep connection alive and send updates
        while True:
            # Wait for updates from orchestrator
            await asyncio.sleep(1)
            
            # Check if there's a new suggestion
            if orchestrator.has_new_suggestion():
                suggestion = await orchestrator.get_latest_suggestion()
                await websocket.send_json({
                    "type": "suggestion",
                    "data": suggestion.dict()
                })
            
    except WebSocketDisconnect:
        logger.info(f"Suggestions WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Suggestions WebSocket error for session {session_id}: {e}")
    finally:
        # Cleanup
        if websocket in websocket_connections.get(session_id, []):
            websocket_connections[session_id].remove(websocket)

# Utility Functions

async def cleanup_session(session_id: str):
    """Clean up session resources"""
    if session_id in active_sessions:
        orchestrator = active_sessions[session_id]
        await orchestrator.cleanup()
        del active_sessions[session_id]
    
    if session_id in websocket_connections:
        # Close all WebSocket connections
        for websocket in websocket_connections[session_id]:
            try:
                await websocket.close()
            except:
                pass
        del websocket_connections[session_id]

async def broadcast_to_session(session_id: str, message: dict):
    """Broadcast message to all WebSocket connections for a session"""
    if session_id not in websocket_connections:
        return
    
    for websocket in websocket_connections[session_id]:
        try:
            await websocket.send_json(message)
        except:
            # Remove disconnected websockets
            websocket_connections[session_id].remove(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.ENVIRONMENT == "development"
    ) 