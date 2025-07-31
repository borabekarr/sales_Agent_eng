from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
import uuid


# Feedback Models
class SuggestionFeedback(BaseModel):
    """Model for tracking AI suggestion feedback"""
    session_id: str = Field(..., description="Session identifier")
    conversation_stage: str = Field(..., description="Current conversation stage")
    ai_suggestion: str = Field(..., description="The AI suggestion that was given")
    user_action: Literal["accepted", "modified", "rejected", "improved"] = Field(..., description="Action taken by user")
    user_feedback: Optional[str] = Field(None, description="User's improvement notes")
    actual_words_used: Optional[str] = Field(None, description="What the user actually said")
    customer_reaction: Literal["positive", "negative", "neutral", "objection"] = Field(default="neutral")
    effectiveness_score: int = Field(default=3, ge=1, le=5, description="Effectiveness rating 1-5")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    improvement_notes: Optional[str] = Field(None, description="Specific improvement suggestions")
    timestamp: datetime = Field(default_factory=datetime.now)


class CustomerReaction(BaseModel):
    """Model for tracking customer reactions"""
    session_id: str
    reaction: Literal["positive", "negative", "neutral", "objection"]
    reaction_text: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Optional[str] = None


class ConversationFeedback(BaseModel):
    """Comprehensive conversation feedback model for Supabase"""
    id: Optional[int] = None
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    conversation_stage: str
    ai_suggestion: str
    user_action: str
    user_feedback: Optional[str] = None
    actual_words_used: Optional[str] = None
    customer_reaction: str = "neutral"
    effectiveness_score: int = 3
    context_data: Dict[str, Any] = Field(default_factory=dict)
    improvement_notes: Optional[str] = None


# Performance Models
class AgentPerformance(BaseModel):
    """Model for tracking agent performance metrics"""
    id: Optional[int] = None
    agent_type: str = Field(..., description="Type of agent (opening, discovery, etc.)")
    scenario_key: str = Field(..., description="Scenario identifier")
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    avg_effectiveness: float = Field(default=0.0)
    last_updated: datetime = Field(default_factory=datetime.now)
    improvement_patterns: Dict[str, Any] = Field(default_factory=dict)


class LearningInsight(BaseModel):
    """Model for storing learning insights"""
    id: Optional[int] = None
    insight_type: str = Field(..., description="Type of insight")
    pattern_description: str = Field(..., description="Description of the pattern")
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    applied_to_system: bool = Field(default=False)


# Analysis Models
class ConversationAnalysis(BaseModel):
    """Model for post-meeting conversation analysis"""
    session_id: str
    full_transcript: str
    analysis_type: str = "post_meeting"
    successful_strategies: List[str] = Field(default_factory=list)
    failed_strategies: List[str] = Field(default_factory=list)
    customer_insights: Dict[str, Any] = Field(default_factory=dict)
    agent_improvements: Dict[str, List[str]] = Field(default_factory=dict)
    knowledge_base_updates: List[str] = Field(default_factory=list)
    overall_effectiveness: float = Field(default=0.0)
    meeting_outcome: Optional[str] = None
    analysis_timestamp: datetime = Field(default_factory=datetime.now)


class LearningPattern(BaseModel):
    """Model for identified learning patterns"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str = Field(..., description="Type of pattern identified")
    description: str = Field(..., description="Pattern description")
    success_rate: float = Field(..., description="Success rate of this pattern")
    usage_count: int = Field(default=1)
    context_requirements: Dict[str, Any] = Field(default_factory=dict)
    example_conversations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_validated: datetime = Field(default_factory=datetime.now)


# Enhanced Agent Context
class EnhancedAgentContext(BaseModel):
    """Enhanced agent context with learning insights"""
    base_context: Dict[str, Any]
    learning_insights: List[LearningInsight] = Field(default_factory=list)
    successful_patterns: List[str] = Field(default_factory=list)
    failed_patterns: List[str] = Field(default_factory=list)
    industry_specific_insights: Dict[str, Any] = Field(default_factory=dict)
    recent_improvements: List[str] = Field(default_factory=list)
    confidence_modifiers: Dict[str, float] = Field(default_factory=dict)


# Meeting Review Models
class MeetingReview(BaseModel):
    """Model for meeting review results"""
    session_id: str
    review_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    overall_score: float = Field(..., ge=0.0, le=10.0)
    stage_scores: Dict[str, float] = Field(default_factory=dict)
    key_successes: List[str] = Field(default_factory=list)
    key_failures: List[str] = Field(default_factory=list)
    improvement_recommendations: List[str] = Field(default_factory=list)
    customer_sentiment_journey: List[Dict[str, Any]] = Field(default_factory=list)
    conversion_probability: float = Field(default=0.0)
    next_actions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


# Supabase Table Creation SQL
SUPABASE_TABLES_SQL = """
-- Conversation Feedback Table
CREATE TABLE IF NOT EXISTS conversation_feedback (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    conversation_stage VARCHAR(50) NOT NULL,
    ai_suggestion TEXT NOT NULL,
    user_action VARCHAR(50) NOT NULL CHECK (user_action IN ('accepted', 'modified', 'rejected', 'improved')),
    user_feedback TEXT,
    actual_words_used TEXT,
    customer_reaction VARCHAR(50) DEFAULT 'neutral' CHECK (customer_reaction IN ('positive', 'negative', 'neutral', 'objection')),
    effectiveness_score INTEGER DEFAULT 3 CHECK (effectiveness_score >= 1 AND effectiveness_score <= 5),
    context_data JSONB DEFAULT '{}',
    improvement_notes TEXT
);

-- Agent Performance Table
CREATE TABLE IF NOT EXISTS agent_performance (
    id BIGSERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    scenario_key VARCHAR(100) NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_effectiveness FLOAT DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT NOW(),
    improvement_patterns JSONB DEFAULT '{}',
    UNIQUE(agent_type, scenario_key)
);

-- Learning Insights Table
CREATE TABLE IF NOT EXISTS learning_insights (
    id BIGSERIAL PRIMARY KEY,
    insight_type VARCHAR(50) NOT NULL,
    pattern_description TEXT NOT NULL,
    supporting_data JSONB DEFAULT '{}',
    confidence_score FLOAT DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    created_at TIMESTAMP DEFAULT NOW(),
    applied_to_system BOOLEAN DEFAULT FALSE
);

-- Conversation Analysis Table
CREATE TABLE IF NOT EXISTS conversation_analysis (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    full_transcript TEXT NOT NULL,
    analysis_type VARCHAR(50) DEFAULT 'post_meeting',
    successful_strategies JSONB DEFAULT '[]',
    failed_strategies JSONB DEFAULT '[]',
    customer_insights JSONB DEFAULT '{}',
    agent_improvements JSONB DEFAULT '{}',
    knowledge_base_updates JSONB DEFAULT '[]',
    overall_effectiveness FLOAT DEFAULT 0.0,
    meeting_outcome VARCHAR(100),
    analysis_timestamp TIMESTAMP DEFAULT NOW()
);

-- Learning Patterns Table
CREATE TABLE IF NOT EXISTS learning_patterns (
    id BIGSERIAL PRIMARY KEY,
    pattern_id VARCHAR(100) UNIQUE NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    success_rate FLOAT NOT NULL,
    usage_count INTEGER DEFAULT 1,
    context_requirements JSONB DEFAULT '{}',
    example_conversations JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    last_validated TIMESTAMP DEFAULT NOW()
);

-- Meeting Reviews Table
CREATE TABLE IF NOT EXISTS meeting_reviews (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    review_id VARCHAR(100) UNIQUE NOT NULL,
    overall_score FLOAT CHECK (overall_score >= 0.0 AND overall_score <= 10.0),
    stage_scores JSONB DEFAULT '{}',
    key_successes JSONB DEFAULT '[]',
    key_failures JSONB DEFAULT '[]',
    improvement_recommendations JSONB DEFAULT '[]',
    customer_sentiment_journey JSONB DEFAULT '[]',
    conversion_probability FLOAT DEFAULT 0.0,
    next_actions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_conversation_feedback_session ON conversation_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_feedback_stage ON conversation_feedback(conversation_stage);
CREATE INDEX IF NOT EXISTS idx_conversation_feedback_timestamp ON conversation_feedback(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_performance_type ON agent_performance(agent_type);
CREATE INDEX IF NOT EXISTS idx_learning_insights_type ON learning_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_conversation_analysis_session ON conversation_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_learning_patterns_type ON learning_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_meeting_reviews_session ON meeting_reviews(session_id);

-- RLS (Row Level Security) Policies - Enable when authentication is implemented
-- ALTER TABLE conversation_feedback ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_performance ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE learning_insights ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_analysis ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE learning_patterns ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE meeting_reviews ENABLE ROW LEVEL SECURITY;
""" 