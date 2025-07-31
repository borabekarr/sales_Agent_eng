import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from utils.config import get_settings
from utils.logging import LoggerMixin
from models.learning_schemas import (
    SuggestionFeedback, CustomerReaction, ConversationFeedback,
    AgentPerformance, LearningInsight, LearningPattern
)

# Note: This will be replaced with actual Supabase client when database is set up
class MockSupabaseClient:
    """Mock Supabase client for development - will be replaced with real client"""
    def __init__(self):
        self.data_store = {
            "conversation_feedback": [],
            "agent_performance": [],
            "learning_insights": [],
            "learning_patterns": []
        }
    
    def table(self, table_name: str):
        return MockTable(self.data_store, table_name)

class MockTable:
    def __init__(self, data_store: Dict, table_name: str):
        self.data_store = data_store
        self.table_name = table_name
        self.current_data = None
    
    def insert(self, data: Dict):
        self.data_store[self.table_name].append(data)
        return MockResponse([data])
    
    def select(self, columns: str = "*"):
        self.current_data = self.data_store[self.table_name]
        return self
    
    def eq(self, column: str, value: Any):
        if self.current_data:
            self.current_data = [item for item in self.current_data if item.get(column) == value]
        return self
    
    def gte(self, column: str, value: Any):
        # Mock implementation for date filtering
        return self
    
    def execute(self):
        return MockResponse(self.current_data or [])
    
    def update(self, data: Dict):
        # Mock update implementation
        return self

class MockResponse:
    def __init__(self, data: List):
        self.data = data


class FeedbackService(LoggerMixin):
    """Service for collecting, storing, and analyzing feedback data"""
    
    def __init__(self):
        self.settings = get_settings()
        # Initialize with mock client - will be replaced with real Supabase client
        self.supabase = MockSupabaseClient()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        
        self.log_info("FeedbackService initialized with mock database")
    
    async def record_suggestion_feedback(self, feedback: SuggestionFeedback) -> bool:
        """Record feedback for an AI suggestion"""
        try:
            feedback_data = {
                "session_id": feedback.session_id,
                "timestamp": feedback.timestamp.isoformat(),
                "conversation_stage": feedback.conversation_stage,
                "ai_suggestion": feedback.ai_suggestion,
                "user_action": feedback.user_action,
                "user_feedback": feedback.user_feedback,
                "actual_words_used": feedback.actual_words_used,
                "customer_reaction": feedback.customer_reaction,
                "effectiveness_score": feedback.effectiveness_score,
                "context_data": feedback.context_data,
                "improvement_notes": feedback.improvement_notes
            }
            
            self.supabase.table("conversation_feedback").insert(feedback_data).execute()
            
            # Update agent performance metrics
            await self._update_agent_performance(
                feedback.conversation_stage,
                feedback.effectiveness_score,
                feedback.user_action
            )
            
            self.log_info(
                "Recorded suggestion feedback",
                session_id=feedback.session_id,
                stage=feedback.conversation_stage,
                action=feedback.user_action,
                score=feedback.effectiveness_score
            )
            
            return True
            
        except Exception as e:
            self.log_error("Failed to record suggestion feedback", error=str(e))
            return False
    
    async def record_customer_reaction(self, reaction: CustomerReaction) -> bool:
        """Record customer reaction data"""
        try:
            # Find the most recent AI suggestion for this session
            recent_feedback = self.supabase.table("conversation_feedback").select("*").eq(
                "session_id", reaction.session_id
            ).execute()
            
            if recent_feedback.data:
                # Update the most recent feedback with customer reaction
                latest_feedback = recent_feedback.data[-1]
                updated_data = {
                    "customer_reaction": reaction.reaction,
                    "context_data": {
                        **latest_feedback.get("context_data", {}),
                        "reaction_text": reaction.reaction_text,
                        "reaction_context": reaction.context
                    }
                }
                
                # Mock update for now
                self.log_info(
                    "Customer reaction recorded",
                    session_id=reaction.session_id,
                    reaction=reaction.reaction
                )
            
            return True
            
        except Exception as e:
            self.log_error("Failed to record customer reaction", error=str(e))
            return False
    
    async def get_learning_patterns(
        self, 
        agent_type: str, 
        scenario: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get learning patterns for an agent type"""
        try:
            cache_key = f"patterns_{agent_type}_{scenario}_{days_back}"
            
            # Check cache
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Get feedback data from the last N days
            feedback_data = self.supabase.table("conversation_feedback").select("*").eq(
                "conversation_stage", agent_type
            ).gte("timestamp", f"NOW() - INTERVAL '{days_back} days'").execute()
            
            if not feedback_data.data:
                patterns = {
                    "successful_phrases": [],
                    "failed_phrases": [],
                    "improvement_suggestions": [],
                    "customer_type_preferences": {},
                    "timing_insights": [],
                    "effectiveness_trends": {}
                }
            else:
                patterns = await self._analyze_feedback_patterns(feedback_data.data)
            
            # Cache the results
            self.cache[cache_key] = (patterns, datetime.now().timestamp())
            
            self.log_info(
                "Retrieved learning patterns",
                agent_type=agent_type,
                pattern_count=len(patterns.get("successful_phrases", []))
            )
            
            return patterns
            
        except Exception as e:
            self.log_error("Failed to get learning patterns", agent_type=agent_type, error=str(e))
            return {
                "successful_phrases": [],
                "failed_phrases": [],
                "improvement_suggestions": [],
                "customer_type_preferences": {},
                "timing_insights": [],
                "effectiveness_trends": {}
            }
    
    async def get_agent_performance_metrics(self, agent_type: str) -> Dict[str, Any]:
        """Get comprehensive performance metrics for an agent"""
        try:
            performance_data = self.supabase.table("agent_performance").select("*").eq(
                "agent_type", agent_type
            ).execute()
            
            if not performance_data.data:
                return {
                    "success_rate": 0.0,
                    "avg_effectiveness": 0.0,
                    "total_interactions": 0,
                    "trend": "stable",
                    "last_updated": None
                }
            
            perf = performance_data.data[0]
            total_interactions = perf.get("success_count", 0) + perf.get("failure_count", 0)
            success_rate = (perf.get("success_count", 0) / max(total_interactions, 1)) * 100
            
            return {
                "success_rate": round(success_rate, 2),
                "avg_effectiveness": round(perf.get("avg_effectiveness", 0.0), 2),
                "total_interactions": total_interactions,
                "trend": self._calculate_trend(agent_type),
                "last_updated": perf.get("last_updated"),
                "improvement_patterns": perf.get("improvement_patterns", {})
            }
            
        except Exception as e:
            self.log_error("Failed to get agent performance metrics", agent_type=agent_type, error=str(e))
            return {"error": str(e)}
    
    async def store_learning_insight(self, insight: LearningInsight) -> bool:
        """Store a learning insight"""
        try:
            insight_data = {
                "insight_type": insight.insight_type,
                "pattern_description": insight.pattern_description,
                "supporting_data": insight.supporting_data,
                "confidence_score": insight.confidence_score,
                "created_at": insight.created_at.isoformat(),
                "applied_to_system": insight.applied_to_system
            }
            
            self.supabase.table("learning_insights").insert(insight_data).execute()
            
            self.log_info(
                "Stored learning insight",
                insight_type=insight.insight_type,
                confidence=insight.confidence_score
            )
            
            return True
            
        except Exception as e:
            self.log_error("Failed to store learning insight", error=str(e))
            return False
    
    async def get_session_transcript(self, session_id: str) -> Optional[str]:
        """Get the full conversation transcript for a session"""
        try:
            # Get all feedback entries for this session
            feedback_data = self.supabase.table("conversation_feedback").select("*").eq(
                "session_id", session_id
            ).execute()
            
            if not feedback_data.data:
                return None
            
            # Reconstruct transcript from feedback and actual words used
            transcript_parts = []
            for entry in sorted(feedback_data.data, key=lambda x: x.get("timestamp", "")):
                ai_suggestion = entry.get("ai_suggestion", "")
                actual_words = entry.get("actual_words_used", "")
                stage = entry.get("conversation_stage", "")
                
                if actual_words:
                    transcript_parts.append(f"[{stage}] SELLER: {actual_words}")
                elif ai_suggestion:
                    transcript_parts.append(f"[{stage}] AI_SUGGESTION: {ai_suggestion}")
                
                # Add customer reaction if available
                customer_reaction = entry.get("customer_reaction")
                context_data = entry.get("context_data", {})
                reaction_text = context_data.get("reaction_text")
                
                if reaction_text:
                    transcript_parts.append(f"CUSTOMER: {reaction_text}")
            
            return "\n".join(transcript_parts)
            
        except Exception as e:
            self.log_error("Failed to get session transcript", session_id=session_id, error=str(e))
            return None
    
    async def _analyze_feedback_patterns(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Analyze feedback data to identify patterns"""
        patterns = {
            "successful_phrases": [],
            "failed_phrases": [],
            "improvement_suggestions": [],
            "customer_type_preferences": {},
            "timing_insights": [],
            "effectiveness_trends": {}
        }
        
        # Successful patterns (high effectiveness + positive actions)
        successful = [
            f for f in feedback_data 
            if f.get("effectiveness_score", 0) >= 4 and f.get("user_action") in ["accepted", "improved"]
        ]
        patterns["successful_phrases"] = [f.get("ai_suggestion", "") for f in successful[-10:]]
        
        # Failed patterns (low effectiveness + negative actions)
        failed = [
            f for f in feedback_data 
            if f.get("effectiveness_score", 0) <= 2 or f.get("user_action") == "rejected"
        ]
        patterns["failed_phrases"] = [f.get("ai_suggestion", "") for f in failed[-5:]]
        
        # User improvement suggestions
        improvements = [
            f.get("user_feedback", "") for f in feedback_data 
            if f.get("user_feedback") and f.get("user_action") == "improved"
        ]
        patterns["improvement_suggestions"] = improvements[-10:]
        
        # Calculate effectiveness trends
        if feedback_data:
            avg_effectiveness = sum(f.get("effectiveness_score", 0) for f in feedback_data) / len(feedback_data)
            patterns["effectiveness_trends"] = {
                "average": round(avg_effectiveness, 2),
                "total_samples": len(feedback_data),
                "recent_trend": self._calculate_recent_trend(feedback_data)
            }
        
        return patterns
    
    async def _update_agent_performance(self, agent_type: str, effectiveness_score: int, user_action: str):
        """Update agent performance metrics"""
        try:
            # Determine if this is a success or failure
            is_success = effectiveness_score >= 4 and user_action in ["accepted", "improved"]
            
            # Get existing performance data
            existing = self.supabase.table("agent_performance").select("*").eq(
                "agent_type", agent_type
            ).execute()
            
            if existing.data:
                # Update existing record
                perf = existing.data[0]
                new_success_count = perf.get("success_count", 0) + (1 if is_success else 0)
                new_failure_count = perf.get("failure_count", 0) + (0 if is_success else 1)
                total_interactions = new_success_count + new_failure_count
                
                new_avg_effectiveness = (
                    (perf.get("avg_effectiveness", 0.0) * (total_interactions - 1) + effectiveness_score) 
                    / total_interactions
                )
                
                # Mock update for now
                self.log_info(
                    "Updated agent performance",
                    agent_type=agent_type,
                    success_count=new_success_count,
                    avg_effectiveness=round(new_avg_effectiveness, 2)
                )
            else:
                # Create new record
                new_data = {
                    "agent_type": agent_type,
                    "scenario_key": "general",
                    "success_count": 1 if is_success else 0,
                    "failure_count": 0 if is_success else 1,
                    "avg_effectiveness": float(effectiveness_score),
                    "last_updated": datetime.now().isoformat(),
                    "improvement_patterns": {}
                }
                
                self.supabase.table("agent_performance").insert(new_data).execute()
                
        except Exception as e:
            self.log_error("Failed to update agent performance", agent_type=agent_type, error=str(e))
    
    def _calculate_trend(self, agent_type: str) -> str:
        """Calculate performance trend for an agent"""
        # Mock implementation - would analyze historical data in real implementation
        return "improving"
    
    def _calculate_recent_trend(self, feedback_data: List[Dict]) -> str:
        """Calculate recent effectiveness trend"""
        if len(feedback_data) < 5:
            return "insufficient_data"
        
        # Compare recent vs older effectiveness scores
        recent_scores = [f.get("effectiveness_score", 0) for f in feedback_data[-5:]]
        older_scores = [f.get("effectiveness_score", 0) for f in feedback_data[-10:-5]]
        
        if not older_scores:
            return "new"
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)
        
        if recent_avg > older_avg + 0.3:
            return "improving"
        elif recent_avg < older_avg - 0.3:
            return "declining"
        else:
            return "stable"
    
    def is_service_available(self) -> bool:
        """Check if feedback service is available"""
        return True
    
    async def clear_cache(self):
        """Clear the internal cache"""
        self.cache.clear()
        self.log_info("Feedback service cache cleared") 