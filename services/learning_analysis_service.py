import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from services.gemini_api import GeminiAPIService
from services.feedback_service import FeedbackService
from utils.logging import LoggerMixin
from models.learning_schemas import (
    ConversationAnalysis, MeetingReview, LearningInsight, LearningPattern
)


class LearningAnalysisService(LoggerMixin):
    """Service for analyzing conversations and generating learning insights using Gemini 2.5 Pro"""
    
    def __init__(self):
        self.gemini_service = GeminiAPIService()
        self.feedback_service = FeedbackService()
        
        # Analysis prompt templates
        self.analysis_prompts = {
            "post_meeting": self._get_post_meeting_analysis_prompt(),
            "pattern_identification": self._get_pattern_identification_prompt(),
            "improvement_recommendations": self._get_improvement_recommendations_prompt(),
            "customer_insights": self._get_customer_insights_prompt()
        }
        
        self.log_info("LearningAnalysisService initialized with Gemini 2.5 Pro")
    
    async def analyze_full_conversation(
        self, 
        session_id: str, 
        full_transcript: str,
        customer_profile: Optional[Dict] = None
    ) -> ConversationAnalysis:
        """Comprehensive conversation analysis using Gemini 2.5 Pro"""
        try:
            self.log_info("Starting full conversation analysis", session_id=session_id)
            
            # Build comprehensive analysis prompt
            analysis_prompt = f"""
            You are an expert sales conversation analyst with advanced reasoning capabilities. Analyze this complete sales conversation transcript and provide detailed insights.

            CONVERSATION TRANSCRIPT:
            {full_transcript}

            CUSTOMER PROFILE:
            {json.dumps(customer_profile or {}, indent=2)}

            ANALYSIS REQUIREMENTS:
            Provide a comprehensive analysis in the following JSON format:

            {{
                "successful_strategies": [
                    "List specific phrases, approaches, or techniques that worked well",
                    "Include exact quotes from the conversation that were effective"
                ],
                "failed_strategies": [
                    "List specific phrases, approaches, or techniques that didn't work",
                    "Include exact quotes that caused negative reactions or objections"
                ],
                "customer_insights": {{
                    "pain_points_identified": ["List discovered pain points"],
                    "buying_signals": ["List positive buying signals shown"],
                    "resistance_points": ["List areas of resistance or hesitation"],
                    "decision_making_style": "analytical/emotional/collaborative/quick",
                    "communication_preference": "direct/detailed/relationship-focused",
                    "industry_specific_concerns": ["Industry-specific issues mentioned"]
                }},
                "agent_improvements": {{
                    "opening_agent": ["Specific improvements for opening stage"],
                    "discovery_agent": ["Specific improvements for discovery stage"],
                    "pitch_agent": ["Specific improvements for pitch stage"],
                    "objection_agent": ["Specific improvements for objection handling"],
                    "closing_agent": ["Specific improvements for closing stage"]
                }},
                "knowledge_base_updates": [
                    "New patterns to add to knowledge base",
                    "Updated response templates",
                    "Industry-specific insights to remember"
                ],
                "overall_effectiveness": 7.5,
                "meeting_outcome": "positive/neutral/negative/needs_follow_up",
                "key_learning_moments": [
                    {{
                        "moment": "Specific moment in conversation",
                        "what_worked": "What was effective",
                        "what_failed": "What didn't work",
                        "improvement": "How to improve next time"
                    }}
                ],
                "conversation_flow_analysis": {{
                    "stage_transitions": "How well did stages flow together",
                    "timing_issues": "Any timing or pacing problems",
                    "missed_opportunities": "Opportunities that were missed"
                }},
                "psychological_insights": {{
                    "customer_emotional_journey": ["How customer emotions changed"],
                    "trust_building_effectiveness": "How well trust was established",
                    "authority_establishment": "How well authority was demonstrated"
                }}
            }}

            FOCUS ON:
            1. Exact phrases and responses that worked or failed
            2. Timing and context of successful/unsuccessful moments
            3. Customer reactions and emotional responses
            4. Missed opportunities for better responses
            5. Specific actionable improvements for each agent
            6. Patterns that can be generalized to other conversations
            """
            
            # Call Gemini 2.5 Pro for analysis
            response = await self.gemini_service.generate_conversation_summary(
                conversation_history=[], # Empty as we're using custom prompt
                customer_profile=None  # Included in prompt
            )
            
            # If the standard method doesn't work with our custom prompt, use direct API call
            if not response or not response.get("key_topics"):
                response = await self._direct_gemini_analysis(analysis_prompt)
            
            # Parse and structure the response
            analysis = ConversationAnalysis(
                session_id=session_id,
                full_transcript=full_transcript,
                analysis_type="post_meeting",
                successful_strategies=response.get("successful_strategies", []),
                failed_strategies=response.get("failed_strategies", []),
                customer_insights=response.get("customer_insights", {}),
                agent_improvements=response.get("agent_improvements", {}),
                knowledge_base_updates=response.get("knowledge_base_updates", []),
                overall_effectiveness=response.get("overall_effectiveness", 5.0),
                meeting_outcome=response.get("meeting_outcome", "neutral")
            )
            
            # Store the analysis
            await self._store_conversation_analysis(analysis)
            
            self.log_info(
                "Completed conversation analysis",
                session_id=session_id,
                effectiveness=analysis.overall_effectiveness,
                outcome=analysis.meeting_outcome
            )
            
            return analysis
            
        except Exception as e:
            self.log_error("Failed to analyze conversation", session_id=session_id, error=str(e))
            # Return basic analysis on error
            return ConversationAnalysis(
                session_id=session_id,
                full_transcript=full_transcript,
                overall_effectiveness=5.0,
                meeting_outcome="error_in_analysis"
            )
    
    async def generate_meeting_review(
        self, 
        session_id: str, 
        conversation_analysis: ConversationAnalysis
    ) -> MeetingReview:
        """Generate comprehensive meeting review with scores and recommendations"""
        try:
            # Calculate stage-specific scores
            stage_scores = await self._calculate_stage_scores(session_id, conversation_analysis)
            
            # Generate improvement recommendations
            recommendations = await self._generate_improvement_recommendations(conversation_analysis)
            
            # Calculate conversion probability
            conversion_probability = await self._calculate_conversion_probability(conversation_analysis)
            
            # Generate next actions
            next_actions = await self._generate_next_actions(conversation_analysis)
            
            meeting_review = MeetingReview(
                session_id=session_id,
                overall_score=conversation_analysis.overall_effectiveness,
                stage_scores=stage_scores,
                key_successes=conversation_analysis.successful_strategies[:5],
                key_failures=conversation_analysis.failed_strategies[:5],
                improvement_recommendations=recommendations,
                customer_sentiment_journey=self._extract_sentiment_journey(conversation_analysis),
                conversion_probability=conversion_probability,
                next_actions=next_actions
            )
            
            # Store the review
            await self._store_meeting_review(meeting_review)
            
            self.log_info(
                "Generated meeting review",
                session_id=session_id,
                overall_score=meeting_review.overall_score,
                conversion_probability=conversion_probability
            )
            
            return meeting_review
            
        except Exception as e:
            self.log_error("Failed to generate meeting review", session_id=session_id, error=str(e))
            # Return basic review on error
            return MeetingReview(
                session_id=session_id,
                overall_score=conversation_analysis.overall_effectiveness,
                stage_scores={},
                key_successes=[],
                key_failures=[],
                improvement_recommendations=["Error generating recommendations"],
                conversion_probability=0.5,
                next_actions=["Review conversation manually"]
            )
    
    async def identify_learning_patterns(
        self, 
        conversations: List[ConversationAnalysis],
        pattern_type: str = "general"
    ) -> List[LearningPattern]:
        """Identify learning patterns across multiple conversations"""
        try:
            self.log_info("Identifying learning patterns", conversation_count=len(conversations))
            
            # Build pattern analysis prompt
            pattern_prompt = f"""
            You are an expert pattern recognition analyst for sales conversations. Analyze these {len(conversations)} conversation analyses to identify recurring successful and unsuccessful patterns.

            CONVERSATION ANALYSES:
            {json.dumps([conv.dict() for conv in conversations], indent=2)}

            PATTERN IDENTIFICATION REQUIREMENTS:
            Identify patterns in the following JSON format:

            {{
                "successful_patterns": [
                    {{
                        "pattern_type": "opening_technique/discovery_question/objection_response/closing_approach",
                        "description": "Detailed description of the pattern",
                        "success_rate": 0.85,
                        "usage_count": 12,
                        "context_requirements": {{
                            "customer_type": "technical/emotional/analytical",
                            "industry": "healthcare/technology/finance",
                            "conversation_stage": "opening/discovery/pitch/objection/closing"
                        }},
                        "example_phrases": ["Exact phrase 1", "Exact phrase 2"],
                        "effectiveness_indicators": ["What indicates this pattern works"]
                    }}
                ],
                "failure_patterns": [
                    {{
                        "pattern_type": "string",
                        "description": "What consistently doesn't work",
                        "failure_rate": 0.75,
                        "common_contexts": "When this pattern typically fails",
                        "alternative_approaches": ["Better approaches to use instead"]
                    }}
                ],
                "improvement_insights": [
                    {{
                        "insight": "Specific insight about what improves performance",
                        "supporting_evidence": "Evidence from the conversations",
                        "implementation": "How to implement this insight"
                    }}
                ]
            }}

            FOCUS ON:
            1. Patterns that appear in multiple conversations
            2. High success rate techniques
            3. Common failure modes to avoid
            4. Context-dependent effectiveness
            5. Industry or customer-type specific patterns
            """
            
            # Call Gemini for pattern analysis
            response = await self._direct_gemini_analysis(pattern_prompt)
            
            # Convert to LearningPattern objects
            patterns = []
            
            for pattern_data in response.get("successful_patterns", []):
                pattern = LearningPattern(
                    pattern_type=pattern_data.get("pattern_type", "general"),
                    description=pattern_data.get("description", ""),
                    success_rate=pattern_data.get("success_rate", 0.5),
                    usage_count=pattern_data.get("usage_count", 1),
                    context_requirements=pattern_data.get("context_requirements", {}),
                    example_conversations=[conv.session_id for conv in conversations]
                )
                patterns.append(pattern)
            
            # Store patterns
            for pattern in patterns:
                await self._store_learning_pattern(pattern)
            
            self.log_info("Identified learning patterns", pattern_count=len(patterns))
            
            return patterns
            
        except Exception as e:
            self.log_error("Failed to identify learning patterns", error=str(e))
            return []
    
    async def generate_agent_specific_insights(
        self, 
        agent_type: str, 
        recent_analyses: List[ConversationAnalysis]
    ) -> Dict[str, Any]:
        """Generate specific insights for an individual agent"""
        try:
            # Filter data relevant to this agent
            agent_data = []
            for analysis in recent_analyses:
                agent_improvements = analysis.agent_improvements.get(agent_type, [])
                if agent_improvements:
                    agent_data.append({
                        "session_id": analysis.session_id,
                        "improvements": agent_improvements,
                        "successful_strategies": analysis.successful_strategies,
                        "failed_strategies": analysis.failed_strategies,
                        "effectiveness": analysis.overall_effectiveness
                    })
            
            if not agent_data:
                return {"insights": [], "recommendations": []}
            
            # Build agent-specific analysis prompt
            agent_prompt = f"""
            You are analyzing performance data specifically for the {agent_type} sales agent. Generate specific insights and recommendations.

            AGENT PERFORMANCE DATA:
            {json.dumps(agent_data, indent=2)}

            AGENT-SPECIFIC ANALYSIS:
            {{
                "performance_trends": {{
                    "effectiveness_trend": "improving/declining/stable",
                    "common_success_factors": ["What consistently works for this agent"],
                    "common_failure_factors": ["What consistently doesn't work"]
                }},
                "specific_recommendations": [
                    "Actionable recommendation 1",
                    "Actionable recommendation 2"
                ],
                "prompt_improvements": [
                    "Specific prompt modifications to improve performance",
                    "New instructions to add to the agent prompt"
                ],
                "training_priorities": [
                    "Skills or techniques this agent should focus on improving"
                ]
            }}
            """
            
            insights = await self._direct_gemini_analysis(agent_prompt)
            
            self.log_info(
                "Generated agent-specific insights",
                agent_type=agent_type,
                data_points=len(agent_data)
            )
            
            return insights
            
        except Exception as e:
            self.log_error("Failed to generate agent insights", agent_type=agent_type, error=str(e))
            return {"insights": [], "recommendations": []}
    
    async def _direct_gemini_analysis(self, prompt: str) -> Dict[str, Any]:
        """Direct call to Gemini API for analysis"""
        try:
            import google.generativeai as genai
            
            # Configure generation parameters for analysis
            generation_config = genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent analysis
                top_p=0.9,
                top_k=40,
                max_output_tokens=2000,
                response_mime_type="application/json"
            )
            
            # Use the main model for comprehensive analysis
            response = await asyncio.to_thread(
                self.gemini_service.main_model.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            # Parse JSON response
            response_text = response.text if response.text else "{}"
            return self.gemini_service._extract_json_from_response(response_text)
            
        except Exception as e:
            self.log_error("Direct Gemini analysis failed", error=str(e))
            return {}
    
    async def _calculate_stage_scores(
        self, 
        session_id: str, 
        analysis: ConversationAnalysis
    ) -> Dict[str, float]:
        """Calculate effectiveness scores for each conversation stage"""
        # Get feedback data for this session
        try:
            # Mock implementation - would use real feedback data
            stage_scores = {
                "opening": 7.5,
                "discovery": 8.0,
                "pitch": 6.5,
                "objection": 7.0,
                "closing": 6.0
            }
            
            # Adjust based on analysis data
            for stage, improvements in analysis.agent_improvements.items():
                if improvements:  # If there are improvements needed, lower the score
                    stage_scores[stage] = max(stage_scores.get(stage, 5.0) - 1.0, 1.0)
            
            return stage_scores
            
        except Exception as e:
            self.log_error("Failed to calculate stage scores", error=str(e))
            return {}
    
    async def _generate_improvement_recommendations(
        self, 
        analysis: ConversationAnalysis
    ) -> List[str]:
        """Generate specific improvement recommendations"""
        recommendations = []
        
        # Add agent-specific recommendations
        for agent, improvements in analysis.agent_improvements.items():
            for improvement in improvements[:2]:  # Top 2 per agent
                recommendations.append(f"[{agent.upper()}] {improvement}")
        
        # Add general recommendations based on failed strategies
        for failed_strategy in analysis.failed_strategies[:3]:
            recommendations.append(f"AVOID: {failed_strategy}")
        
        return recommendations[:10]  # Limit to top 10
    
    async def _calculate_conversion_probability(
        self, 
        analysis: ConversationAnalysis
    ) -> float:
        """Calculate probability of conversion based on conversation analysis"""
        base_probability = analysis.overall_effectiveness / 10.0
        
        # Adjust based on meeting outcome
        outcome_modifiers = {
            "positive": 0.2,
            "neutral": 0.0,
            "negative": -0.3,
            "needs_follow_up": 0.1
        }
        
        modifier = outcome_modifiers.get(analysis.meeting_outcome, 0.0)
        probability = max(0.0, min(1.0, base_probability + modifier))
        
        return round(probability, 2)
    
    async def _generate_next_actions(self, analysis: ConversationAnalysis) -> List[str]:
        """Generate recommended next actions based on analysis"""
        actions = []
        
        if analysis.meeting_outcome == "positive":
            actions.extend([
                "Send follow-up email within 24 hours",
                "Prepare proposal based on discussed requirements",
                "Schedule decision-maker meeting if needed"
            ])
        elif analysis.meeting_outcome == "needs_follow_up":
            actions.extend([
                "Address remaining objections identified",
                "Provide additional information requested",
                "Schedule follow-up call within 1 week"
            ])
        elif analysis.meeting_outcome == "negative":
            actions.extend([
                "Analyze what went wrong in the conversation",
                "Consider different approach for next contact",
                "Update customer profile with lessons learned"
            ])
        
        return actions
    
    def _extract_sentiment_journey(self, analysis: ConversationAnalysis) -> List[Dict[str, Any]]:
        """Extract customer sentiment journey from analysis"""
        # Mock implementation - would be more sophisticated in real implementation
        return [
            {"stage": "opening", "sentiment": "neutral", "confidence": 0.8},
            {"stage": "discovery", "sentiment": "interested", "confidence": 0.7},
            {"stage": "pitch", "sentiment": "positive", "confidence": 0.9},
            {"stage": "objection", "sentiment": "hesitant", "confidence": 0.6},
            {"stage": "closing", "sentiment": "considering", "confidence": 0.8}
        ]
    
    async def _store_conversation_analysis(self, analysis: ConversationAnalysis):
        """Store conversation analysis in database"""
        # Implementation would store in Supabase
        self.log_info("Stored conversation analysis", session_id=analysis.session_id)
    
    async def _store_meeting_review(self, review: MeetingReview):
        """Store meeting review in database"""
        # Implementation would store in Supabase
        self.log_info("Stored meeting review", session_id=review.session_id)
    
    async def _store_learning_pattern(self, pattern: LearningPattern):
        """Store learning pattern in database"""
        # Implementation would store in Supabase
        self.log_info("Stored learning pattern", pattern_type=pattern.pattern_type)
    
    def _get_post_meeting_analysis_prompt(self) -> str:
        """Get template for post-meeting analysis"""
        return "Analyze this sales conversation for effectiveness and learning opportunities..."
    
    def _get_pattern_identification_prompt(self) -> str:
        """Get template for pattern identification"""
        return "Identify patterns across multiple sales conversations..."
    
    def _get_improvement_recommendations_prompt(self) -> str:
        """Get template for improvement recommendations"""
        return "Generate specific improvement recommendations based on analysis..."
    
    def _get_customer_insights_prompt(self) -> str:
        """Get template for customer insights analysis"""
        return "Analyze customer behavior and preferences from conversation..."
    
    def is_service_available(self) -> bool:
        """Check if learning analysis service is available"""
        return self.gemini_service.is_service_available() 