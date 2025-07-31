import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from services.gemini_api import GeminiAPIService
from services.feedback_service import FeedbackService
from utils.logging import LoggerMixin
from models.schemas import AgentContext, Message, CustomerProfile
from models.learning_schemas import EnhancedAgentContext
import json


class EnhancedAgentService(LoggerMixin):
    """Enhanced agent service that incorporates learning insights into real-time responses"""
    
    def __init__(self):
        self.gemini_service = GeminiAPIService()
        self.feedback_service = FeedbackService()
        self.learning_cache = {}
        self.cache_ttl = 600  # 10 minutes cache TTL
        
        self.log_info("EnhancedAgentService initialized with learning integration")
    
    async def generate_enhanced_suggestion(
        self,
        base_context: AgentContext,
        agent_type: str,
        scenario_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate suggestion enhanced with learning insights"""
        try:
            # Build enhanced context with learning insights
            enhanced_context = await self._build_enhanced_context(
                base_context, agent_type, scenario_key
            )
            
            # Generate enhanced prompt
            enhanced_prompt = await self._build_enhanced_prompt(
                agent_type, enhanced_context
            )
            
            # Get suggestion from Gemini with enhanced prompt
            suggestion = await self.gemini_service.generate_suggestion(
                context=base_context,
                agent_type=agent_type,
                conversation_history=base_context.recent_messages,
                custom_prompt=enhanced_prompt
            )
            
            # Add learning metadata to response
            suggestion.update({
                "learning_enhanced": True,
                "insights_applied": len(enhanced_context.learning_insights),
                "successful_patterns_used": len(enhanced_context.successful_patterns),
                "confidence_boost": enhanced_context.confidence_modifiers.get(agent_type, 0.0),
                "enhancement_version": "1.0"
            })
            
            self.log_info(
                "Generated enhanced suggestion",
                agent_type=agent_type,
                insights_applied=len(enhanced_context.learning_insights),
                base_confidence=suggestion.get("confidence", 0.0)
            )
            
            return suggestion
            
        except Exception as e:
            self.log_error("Failed to generate enhanced suggestion", agent_type=agent_type, error=str(e))
            # Fallback to base suggestion
            return await self.gemini_service.generate_suggestion(
                context=base_context,
                agent_type=agent_type,
                conversation_history=base_context.recent_messages
            )
    
    async def _build_enhanced_context(
        self,
        base_context: AgentContext,
        agent_type: str,
        scenario_key: Optional[str] = None
    ) -> EnhancedAgentContext:
        """Build enhanced context with learning insights"""
        try:
            # Get learning patterns for this agent
            learning_patterns = await self.feedback_service.get_learning_patterns(
                agent_type=agent_type,
                scenario=scenario_key or "general",
                days_back=30
            )
            
            # Get industry-specific insights
            industry_insights = await self._get_industry_insights(
                base_context.customer_profile,
                agent_type
            )
            
            # Calculate confidence modifiers based on learned patterns
            confidence_modifiers = await self._calculate_confidence_modifiers(
                agent_type, learning_patterns
            )
            
            enhanced_context = EnhancedAgentContext(
                base_context=base_context.dict(),
                learning_insights=[],  # Will be populated with relevant insights
                successful_patterns=learning_patterns.get("successful_phrases", [])[:5],
                failed_patterns=learning_patterns.get("failed_phrases", [])[:3],
                industry_specific_insights=industry_insights,
                recent_improvements=learning_patterns.get("improvement_suggestions", [])[:3],
                confidence_modifiers=confidence_modifiers
            )
            
            return enhanced_context
            
        except Exception as e:
            self.log_error("Failed to build enhanced context", agent_type=agent_type, error=str(e))
            # Return basic enhanced context
            return EnhancedAgentContext(
                base_context=base_context.dict(),
                learning_insights=[],
                successful_patterns=[],
                failed_patterns=[],
                industry_specific_insights={},
                recent_improvements=[],
                confidence_modifiers={}
            )
    
    async def _build_enhanced_prompt(
        self,
        agent_type: str,
        enhanced_context: EnhancedAgentContext
    ) -> str:
        """Build enhanced prompt with learning insights integrated"""
        
        # Get base prompt for the agent type
        base_prompt = self._get_base_agent_prompt(agent_type, enhanced_context.base_context)
        
        # Add learning enhancements
        enhancement_sections = []
        
        # Add successful patterns section
        if enhanced_context.successful_patterns:
            patterns_text = "\n".join([f"- {pattern}" for pattern in enhanced_context.successful_patterns])
            enhancement_sections.append(f"""
SUCCESSFUL PATTERNS TO EMULATE:
Based on recent high-performing conversations, these approaches have been very effective:
{patterns_text}

Use similar language, tone, and approach when appropriate for the current context.
""")
        
        # Add improvement insights section
        if enhanced_context.recent_improvements:
            improvements_text = "\n".join([f"- {improvement}" for improvement in enhanced_context.recent_improvements])
            enhancement_sections.append(f"""
RECENT LEARNING INSIGHTS:
Based on user feedback and conversation analysis, apply these improvements:
{improvements_text}

Incorporate these lessons into your response generation.
""")
        
        # Add patterns to avoid section
        if enhanced_context.failed_patterns:
            failed_text = "\n".join([f"- {pattern}" for pattern in enhanced_context.failed_patterns])
            enhancement_sections.append(f"""
APPROACHES TO AVOID:
These patterns have shown poor performance in recent conversations:
{failed_text}

Avoid similar language, approaches, or techniques.
""")
        
        # Add industry-specific insights
        if enhanced_context.industry_specific_insights:
            industry_text = json.dumps(enhanced_context.industry_specific_insights, indent=2)
            enhancement_sections.append(f"""
INDUSTRY-SPECIFIC INSIGHTS:
Tailor your approach based on these industry-specific learnings:
{industry_text}

Adapt your language and examples to be relevant for this industry context.
""")
        
        # Add confidence modifiers section
        confidence_modifier = enhanced_context.confidence_modifiers.get(agent_type, 0.0)
        if confidence_modifier != 0.0:
            confidence_text = "increased" if confidence_modifier > 0 else "decreased"
            enhancement_sections.append(f"""
PERFORMANCE CONTEXT:
Recent performance analysis indicates {confidence_text} effectiveness for this agent type.
{"Focus on proven techniques and be more assertive." if confidence_modifier > 0 else "Be more cautious and focus on rapport building."}
""")
        
        # Combine base prompt with enhancements
        enhanced_prompt = base_prompt
        if enhancement_sections:
            enhanced_prompt += "\n\n" + "="*50 + "\nLEARNING-ENHANCED INSTRUCTIONS:\n" + "="*50
            enhanced_prompt += "\n".join(enhancement_sections)
            enhanced_prompt += "\n" + "="*50 + "\n"
        
        enhanced_prompt += """
CRITICAL: Your response must incorporate the learning insights above while maintaining the core sales methodology and constraints specified in your base instructions. Prioritize learned successful patterns over generic approaches.
"""
        
        return enhanced_prompt
    
    async def _get_industry_insights(
        self,
        customer_profile: CustomerProfile,
        agent_type: str
    ) -> Dict[str, Any]:
        """Get industry-specific insights for the customer"""
        try:
            customer_industry = getattr(customer_profile, 'company', '') or ''
            
            # Check cache for industry insights
            cache_key = f"industry_{customer_industry}_{agent_type}"
            if cache_key in self.learning_cache:
                cached_data, timestamp = self.learning_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Mock industry insights - would be retrieved from learning database
            industry_insights = {
                "healthcare": {
                    "key_concerns": ["Patient privacy", "Compliance", "ROI measurement"],
                    "effective_language": ["HIPAA-compliant", "patient outcomes", "efficiency gains"],
                    "common_objections": ["Budget constraints", "Staff training time", "Integration complexity"]
                },
                "technology": {
                    "key_concerns": ["Scalability", "Security", "Technical integration"],
                    "effective_language": ["API-first", "cloud-native", "enterprise-grade"],
                    "common_objections": ["Vendor lock-in", "Performance impact", "Technical debt"]
                },
                "finance": {
                    "key_concerns": ["Regulatory compliance", "Risk management", "Cost control"],
                    "effective_language": ["regulatory-compliant", "risk mitigation", "cost optimization"],
                    "common_objections": ["Regulatory approval", "Security concerns", "Implementation time"]
                }
            }.get(customer_industry.lower(), {})
            
            # Cache the results
            self.learning_cache[cache_key] = (industry_insights, datetime.now().timestamp())
            
            return industry_insights
            
        except Exception as e:
            self.log_error("Failed to get industry insights", error=str(e))
            return {}
    
    async def _calculate_confidence_modifiers(
        self,
        agent_type: str,
        learning_patterns: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate confidence modifiers based on recent performance"""
        try:
            # Get agent performance metrics
            performance = await self.feedback_service.get_agent_performance_metrics(agent_type)
            
            # Calculate confidence modifier based on recent trends
            effectiveness_trends = learning_patterns.get("effectiveness_trends", {})
            recent_trend = effectiveness_trends.get("recent_trend", "stable")
            avg_effectiveness = effectiveness_trends.get("average", 5.0)
            
            # Base confidence modifier on performance
            base_modifier = (avg_effectiveness - 5.0) / 5.0  # Normalize around 5.0
            
            # Adjust based on trend
            trend_modifiers = {
                "improving": 0.1,
                "stable": 0.0,
                "declining": -0.1,
                "insufficient_data": 0.0
            }
            
            trend_modifier = trend_modifiers.get(recent_trend, 0.0)
            final_modifier = base_modifier + trend_modifier
            
            return {agent_type: round(final_modifier, 2)}
            
        except Exception as e:
            self.log_error("Failed to calculate confidence modifiers", error=str(e))
            return {agent_type: 0.0}
    
    def _get_base_agent_prompt(self, agent_type: str, base_context: Dict[str, Any]) -> str:
        """Get the base prompt for an agent type"""
        # This would use the existing agent prompts from the GeminiAPIService
        return self.gemini_service._get_agent_prompt(agent_type, self._dict_to_agent_context(base_context))
    
    def _dict_to_agent_context(self, context_dict: Dict[str, Any]) -> AgentContext:
        """Convert dictionary back to AgentContext for compatibility"""
        try:
            return AgentContext(**context_dict)
        except Exception:
            # Fallback for compatibility issues
            return AgentContext(
                current_stage=context_dict.get("current_stage", "discovery"),
                customer_profile=CustomerProfile(),
                recent_messages=[],
                conversation_history=[],
                context_stack=[],
                session_metadata={}
            )
    
    async def track_suggestion_usage(
        self,
        session_id: str,
        agent_type: str,
        suggestion: Dict[str, Any],
        user_action: str,
        effectiveness_score: Optional[int] = None
    ):
        """Track how suggestions are used for learning purposes"""
        try:
            from models.learning_schemas import SuggestionFeedback
            
            feedback = SuggestionFeedback(
                session_id=session_id,
                conversation_stage=agent_type,
                ai_suggestion=suggestion.get("suggestion", ""),
                user_action=user_action,
                effectiveness_score=effectiveness_score or 3,
                context_data={
                    "learning_enhanced": suggestion.get("learning_enhanced", False),
                    "insights_applied": suggestion.get("insights_applied", 0),
                    "confidence_boost": suggestion.get("confidence_boost", 0.0)
                }
            )
            
            await self.feedback_service.record_suggestion_feedback(feedback)
            
            self.log_info(
                "Tracked suggestion usage",
                session_id=session_id,
                agent_type=agent_type,
                user_action=user_action
            )
            
        except Exception as e:
            self.log_error("Failed to track suggestion usage", error=str(e))
    
    async def get_real_time_learning_stats(self) -> Dict[str, Any]:
        """Get real-time learning statistics"""
        try:
            stats = {
                "enhanced_suggestions_today": 0,
                "learning_patterns_active": 0,
                "average_enhancement_impact": 0.0,
                "top_performing_agents": [],
                "recent_improvements_applied": 0
            }
            
            # Mock implementation - would calculate from real data
            stats.update({
                "enhanced_suggestions_today": 45,
                "learning_patterns_active": 12,
                "average_enhancement_impact": 0.15,
                "top_performing_agents": ["discovery", "objection", "closing"],
                "recent_improvements_applied": 8
            })
            
            return stats
            
        except Exception as e:
            self.log_error("Failed to get learning stats", error=str(e))
            return {}
    
    async def force_learning_update(self, agent_type: Optional[str] = None):
        """Force update of learning data (clear caches, refresh patterns)"""
        try:
            # Clear learning cache
            if agent_type:
                # Clear specific agent cache
                keys_to_remove = [k for k in self.learning_cache.keys() if agent_type in k]
                for key in keys_to_remove:
                    del self.learning_cache[key]
            else:
                # Clear all cache
                self.learning_cache.clear()
            
            # Clear feedback service cache
            await self.feedback_service.clear_cache()
            
            self.log_info("Forced learning update", agent_type=agent_type or "all")
            
        except Exception as e:
            self.log_error("Failed to force learning update", error=str(e))
    
    def is_service_available(self) -> bool:
        """Check if enhanced agent service is available"""
        return (
            self.gemini_service.is_service_available() and 
            self.feedback_service.is_service_available()
        ) 