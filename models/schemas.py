from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
import uuid


# Session Models

class SessionCreate(BaseModel):
    """Request model for creating a new session"""
    user_id: str
    customer_name: Optional[str] = None
    customer_company: Optional[str] = None
    product_focus: Optional[str] = None
    language: str = "en"


class SessionResponse(BaseModel):
    """Response model for session creation"""
    session_id: str
    status: str
    start_time: datetime
    current_stage: str
    configuration: Dict[str, Any]


class SessionStatus(BaseModel):
    """Model for session status information"""
    session_id: str
    status: str
    current_stage: str
    start_time: datetime
    last_activity: datetime
    message_count: int


# Message Models

class Message(BaseModel):
    """Model for conversation messages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker: Literal["seller", "customer"]
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    stage: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerProfile(BaseModel):
    """Model for customer profile data"""
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    pain_points: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    budget_range: Optional[str] = None
    decision_authority: Optional[str] = None
    timeline: Optional[str] = None
    sentiment: Optional[str] = None


# Suggestion Models

class Suggestion(BaseModel):
    """Model for AI-generated suggestions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    text: str
    type: Literal["question", "statement", "objection_response", "closing"]
    confidence: float = Field(ge=0.0, le=1.0)
    stage: str
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    alternatives: List[str] = Field(default_factory=list)


class SuggestionResponse(BaseModel):
    """Response model for suggestion requests"""
    suggestion: Suggestion
    context: Dict[str, Any] = Field(default_factory=dict)
    next_actions: List[str] = Field(default_factory=list)


# Conversation State Models

class ConversationState(BaseModel):
    """Model for current conversation state"""
    session_id: str
    current_stage: str
    customer_profile: CustomerProfile
    conversation_history: List[Message]
    context_stack: List[Dict[str, Any]] = Field(default_factory=list)
    last_suggestion: Optional[Suggestion] = None
    stage_progress: Dict[str, float] = Field(default_factory=dict)


# Request Models

class InterruptRequest(BaseModel):
    """Request model for handling interruptions"""
    speaker: Literal["seller", "customer"]
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = Field(default_factory=dict)


class AdvanceStageRequest(BaseModel):
    """Request model for advancing conversation stage"""
    target_stage: str
    reason: Optional[str] = None
    force: bool = False


class AudioData(BaseModel):
    """Model for audio data processing"""
    session_id: str
    audio_chunk: bytes
    sample_rate: int = 16000
    channels: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Analytics Models

class ConversationSummary(BaseModel):
    """Model for conversation summary and analysis"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    message_count: int
    customer_profile: CustomerProfile
    stages_covered: List[str]
    key_topics: List[str] = Field(default_factory=list)
    objections_raised: List[str] = Field(default_factory=list)
    outcome: Optional[str] = None
    next_steps: List[str] = Field(default_factory=list)
    sentiment_analysis: Dict[str, float] = Field(default_factory=dict)
    ai_suggestions_used: int = 0


class PerformanceMetrics(BaseModel):
    """Model for performance metrics"""
    session_id: str
    response_times: List[float] = Field(default_factory=list)
    avg_response_time: float
    suggestion_accuracy: float
    customer_engagement: float
    stage_progression_rate: float
    interruption_count: int
    successful_transitions: int
    total_transitions: int
    conversation_flow_score: float


# Stage Models

class SalesStage(BaseModel):
    """Model for sales stage information"""
    name: str
    description: str
    objectives: List[str]
    key_questions: List[str]
    success_criteria: List[str]
    next_stages: List[str]


class StageProgress(BaseModel):
    """Model for tracking stage progress"""
    stage_name: str
    completion_percentage: float
    objectives_met: List[str]
    objectives_pending: List[str]
    estimated_time_remaining: Optional[int] = None  # minutes


# Agent Models

class AgentResponse(BaseModel):
    """Model for agent responses"""
    agent_type: str
    confidence: float
    suggestions: List[str]
    reasoning: str
    context_updates: Dict[str, Any] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)


class AgentContext(BaseModel):
    """Model for agent context"""
    current_stage: str
    customer_profile: CustomerProfile
    recent_messages: List[Message]
    conversation_history: List[Message]
    context_stack: List[Dict[str, Any]]
    session_metadata: Dict[str, Any] = Field(default_factory=dict)


# Error Models

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


# WebSocket Models

class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


class AudioStreamConfig(BaseModel):
    """Model for audio stream configuration"""
    sample_rate: int = 16000
    channels: int = 1
    language: str = "en"
    speaker_diarization: bool = True
    real_time_processing: bool = True
    buffer_size: int = 4096


# Configuration Models

class AgentConfig(BaseModel):
    """Model for agent configuration"""
    agent_type: str
    enabled: bool = True
    priority: int = 1
    response_timeout: int = 5
    max_retries: int = 3
    custom_prompts: Dict[str, str] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SessionConfig(BaseModel):
    """Model for session configuration"""
    languages: List[str] = ["en", "tr"]
    speaker_diarization: bool = True
    real_time_suggestions: bool = True
    max_session_duration: int = 7200  # 2 hours
    auto_advance_stages: bool = False
    suggestion_delay: int = 2  # seconds
    agents: List[AgentConfig] = Field(default_factory=list) 