import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from services.learning_analysis_service import LearningAnalysisService
from services.feedback_service import FeedbackService
from services.enhanced_agent_service import EnhancedAgentService
from utils.logging import LoggerMixin
from models.learning_schemas import (
    ConversationAnalysis, MeetingReview, LearningInsight, LearningPattern
)


class MeetingReviewService(LoggerMixin):
    """Service for conducting post-meeting analysis and applying learnings to the system"""
    
    def __init__(self):
        self.analysis_service = LearningAnalysisService()
        self.feedback_service = FeedbackService()
        self.enhanced_agent_service = EnhancedAgentService()
        self.processing_queue = asyncio.Queue()
        self.is_processing = False
        
        self.log_info("MeetingReviewService initialized")
    
    async def conduct_full_meeting_review(
        self,
        session_id: str,
        customer_profile: Optional[Dict] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Conduct comprehensive post-meeting review and analysis"""
        try:
            self.log_info("Starting full meeting review", session_id=session_id)
            
            # Step 1: Get conversation transcript
            transcript = await self.feedback_service.get_session_transcript(session_id)
            if not transcript:
                self.log_warning("No transcript found for session", session_id=session_id)
                return {"error": "No conversation data found", "session_id": session_id}
            
            # Step 2: Analyze conversation with Gemini 2.5 Pro
            conversation_analysis = await self.analysis_service.analyze_full_conversation(
                session_id=session_id,
                full_transcript=transcript,
                customer_profile=customer_profile
            )
            
            # Step 3: Generate meeting review
            meeting_review = await self.analysis_service.generate_meeting_review(
                session_id=session_id,
                conversation_analysis=conversation_analysis
            )
            
            # Step 4: Apply learnings to system
            learning_results = await self.apply_learnings_to_system(
                conversation_analysis=conversation_analysis,
                meeting_review=meeting_review
            )
            
            # Step 5: Generate actionable insights
            actionable_insights = await self._generate_actionable_insights(
                conversation_analysis,
                meeting_review
            )
            
            # Step 6: Update agent performance metrics
            await self._update_system_performance_metrics(
                session_id,
                conversation_analysis,
                meeting_review
            )
            
            review_results = {
                "session_id": session_id,
                "review_completed_at": datetime.now().isoformat(),
                "overall_score": meeting_review.overall_score,
                "conversion_probability": meeting_review.conversion_probability,
                "meeting_outcome": conversation_analysis.meeting_outcome,
                "key_insights": {
                    "successful_strategies": conversation_analysis.successful_strategies[:5],
                    "improvement_areas": conversation_analysis.failed_strategies[:3],
                    "agent_specific_improvements": conversation_analysis.agent_improvements
                },
                "actionable_insights": actionable_insights,
                "learning_application_results": learning_results,
                "next_actions": meeting_review.next_actions,
                "stage_performance": meeting_review.stage_scores,
                "customer_sentiment_journey": meeting_review.customer_sentiment_journey
            }
            
            self.log_info(
                "Completed full meeting review",
                session_id=session_id,
                overall_score=meeting_review.overall_score,
                insights_generated=len(actionable_insights)
            )
            
            return review_results
            
        except Exception as e:
            self.log_error("Failed to conduct meeting review", session_id=session_id, error=str(e))
            return {
                "error": f"Meeting review failed: {str(e)}",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def apply_learnings_to_system(
        self,
        conversation_analysis: ConversationAnalysis,
        meeting_review: MeetingReview
    ) -> Dict[str, Any]:
        """Apply learning insights to improve system performance"""
        try:
            self.log_info("Applying learnings to system", session_id=conversation_analysis.session_id)
            
            application_results = {
                "learning_insights_created": 0,
                "agent_improvements_applied": 0,
                "patterns_updated": 0,
                "knowledge_base_updates": 0,
                "system_updates_applied": []
            }
            
            # Apply agent-specific improvements
            for agent_type, improvements in conversation_analysis.agent_improvements.items():
                if improvements:
                    await self._apply_agent_improvements(agent_type, improvements)
                    application_results["agent_improvements_applied"] += len(improvements)
                    application_results["system_updates_applied"].append(f"Updated {agent_type} agent")
            
            # Create learning insights
            insights_created = await self._create_learning_insights(conversation_analysis, meeting_review)
            application_results["learning_insights_created"] = insights_created
            
            # Update knowledge base
            if conversation_analysis.knowledge_base_updates:
                knowledge_updates = await self._update_knowledge_base(
                    conversation_analysis.knowledge_base_updates
                )
                application_results["knowledge_base_updates"] = knowledge_updates
                application_results["system_updates_applied"].append("Updated knowledge base")
            
            # Identify and store new patterns
            if conversation_analysis.successful_strategies:
                patterns_updated = await self._update_learning_patterns(conversation_analysis)
                application_results["patterns_updated"] = patterns_updated
                application_results["system_updates_applied"].append("Updated learning patterns")
            
            # Force refresh of enhanced agent service
            await self.enhanced_agent_service.force_learning_update()
            application_results["system_updates_applied"].append("Refreshed agent learning cache")
            
            self.log_info(
                "Successfully applied learnings to system",
                session_id=conversation_analysis.session_id,
                updates_applied=len(application_results["system_updates_applied"])
            )
            
            return application_results
            
        except Exception as e:
            self.log_error("Failed to apply learnings to system", error=str(e))
            return {"error": str(e)}
    
    async def queue_meeting_for_review(
        self,
        session_id: str,
        customer_profile: Optional[Dict] = None,
        priority: str = "normal"
    ):
        """Queue a meeting for asynchronous review"""
        try:
            review_task = {
                "session_id": session_id,
                "customer_profile": customer_profile,
                "priority": priority,
                "queued_at": datetime.now().isoformat()
            }
            
            await self.processing_queue.put(review_task)
            
            self.log_info("Queued meeting for review", session_id=session_id, priority=priority)
            
            # Start processing if not already running
            if not self.is_processing:
                asyncio.create_task(self._process_review_queue())
            
        except Exception as e:
            self.log_error("Failed to queue meeting for review", session_id=session_id, error=str(e))
    
    async def get_learning_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Get summary of learning activities over the past N days"""
        try:
            # Mock implementation - would query real database
            summary = {
                "period": f"Last {days_back} days",
                "meetings_analyzed": 15,
                "insights_generated": 42,
                "agent_improvements_applied": 28,
                "average_meeting_score": 7.3,
                "conversion_rate_improvement": 0.08,
                "top_successful_strategies": [
                    "Using 'Start with No' technique in opening",
                    "Pain amplification through follow-up questions",
                    "Industry-specific value propositions"
                ],
                "top_improvement_areas": [
                    "Objection handling response timing",
                    "Closing technique confidence",
                    "Discovery question depth"
                ],
                "agent_performance_trends": {
                    "opening": {"trend": "improving", "score": 8.1},
                    "discovery": {"trend": "stable", "score": 7.8},
                    "pitch": {"trend": "improving", "score": 7.5},
                    "objection": {"trend": "declining", "score": 6.9},
                    "closing": {"trend": "stable", "score": 7.2}
                },
                "pattern_effectiveness": {
                    "total_patterns_identified": 12,
                    "high_success_patterns": 8,
                    "patterns_requiring_adjustment": 2
                }
            }
            
            return summary
            
        except Exception as e:
            self.log_error("Failed to get learning summary", error=str(e))
            return {"error": str(e)}
    
    async def generate_system_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive system optimization report"""
        try:
            # Get recent conversation analyses
            # Mock implementation - would query real database
            
            optimization_report = {
                "report_generated_at": datetime.now().isoformat(),
                "system_performance": {
                    "overall_effectiveness": 7.4,
                    "trend": "improving",
                    "total_conversations_analyzed": 156,
                    "learning_system_impact": "+12% effectiveness improvement"
                },
                "agent_rankings": [
                    {"agent": "discovery", "score": 8.2, "improvement": "+0.5"},
                    {"agent": "opening", "score": 8.1, "improvement": "+0.3"},
                    {"agent": "pitch", "score": 7.5, "improvement": "+0.2"},
                    {"agent": "closing", "score": 7.2, "improvement": "+0.1"},
                    {"agent": "objection", "score": 6.9, "improvement": "-0.2"}
                ],
                "priority_optimizations": [
                    {
                        "area": "Objection Handling",
                        "current_score": 6.9,
                        "improvement_potential": "+1.2 points",
                        "recommended_actions": [
                            "Implement advanced looping techniques",
                            "Add industry-specific objection responses",
                            "Improve timing of objection anticipation"
                        ]
                    },
                    {
                        "area": "Closing Techniques",
                        "current_score": 7.2,
                        "improvement_potential": "+0.8 points", 
                        "recommended_actions": [
                            "Enhance confidence in closing language",
                            "Better recognition of buying signals",
                            "More varied closing approaches"
                        ]
                    }
                ],
                "learning_insights_impact": {
                    "total_insights_applied": 142,
                    "successful_pattern_adoptions": 89,
                    "failed_pattern_eliminations": 23,
                    "customer_satisfaction_improvement": "+15%"
                },
                "recommendations": [
                    "Focus objection handling training on advanced techniques",
                    "Implement more aggressive learning cycles for underperforming agents",
                    "Expand industry-specific pattern recognition",
                    "Increase feedback collection frequency during live conversations"
                ]
            }
            
            return optimization_report
            
        except Exception as e:
            self.log_error("Failed to generate optimization report", error=str(e))
            return {"error": str(e)}
    
    async def _process_review_queue(self):
        """Process queued meeting reviews asynchronously"""
        self.is_processing = True
        try:
            while True:
                try:
                    # Get next review task with timeout
                    review_task = await asyncio.wait_for(
                        self.processing_queue.get(),
                        timeout=5.0
                    )
                    
                    # Process the review
                    await self.conduct_full_meeting_review(
                        session_id=review_task["session_id"],
                        customer_profile=review_task.get("customer_profile"),
                        priority=review_task.get("priority", "normal")
                    )
                    
                    # Mark task as done
                    self.processing_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # No more tasks in queue
                    break
                except Exception as e:
                    self.log_error("Error processing review queue item", error=str(e))
                    continue
                    
        finally:
            self.is_processing = False
    
    async def _generate_actionable_insights(
        self,
        analysis: ConversationAnalysis,
        review: MeetingReview
    ) -> List[Dict[str, Any]]:
        """Generate specific actionable insights from analysis"""
        insights = []
        
        # High-impact improvements
        if analysis.overall_effectiveness < 7.0:
            insights.append({
                "type": "urgent_improvement",
                "title": "Conversation Effectiveness Below Target",
                "description": f"Score of {analysis.overall_effectiveness}/10 indicates significant improvement opportunities",
                "actions": review.improvement_recommendations[:3],
                "priority": "high"
            })
        
        # Agent-specific insights
        for agent, improvements in analysis.agent_improvements.items():
            if improvements:
                insights.append({
                    "type": "agent_improvement",
                    "title": f"{agent.title()} Agent Enhancement",
                    "description": f"Specific improvements identified for {agent} stage",
                    "actions": improvements[:2],
                    "priority": "medium"
                })
        
        # Customer-specific insights
        if analysis.customer_insights:
            insights.append({
                "type": "customer_insight",
                "title": "Customer Profile Enhancement",
                "description": "New insights about customer preferences and communication style",
                "actions": [
                    "Update customer profile with new insights",
                    "Adjust communication approach for future interactions"
                ],
                "priority": "medium"
            })
        
        return insights
    
    async def _apply_agent_improvements(self, agent_type: str, improvements: List[str]):
        """Apply specific improvements to an agent"""
        try:
            # Create learning insights for each improvement
            for improvement in improvements:
                insight = LearningInsight(
                    insight_type=f"{agent_type}_improvement",
                    pattern_description=improvement,
                    supporting_data={"agent_type": agent_type},
                    confidence_score=0.8,
                    applied_to_system=True
                )
                
                await self.feedback_service.store_learning_insight(insight)
            
            self.log_info(
                "Applied agent improvements",
                agent_type=agent_type,
                improvement_count=len(improvements)
            )
            
        except Exception as e:
            self.log_error("Failed to apply agent improvements", agent_type=agent_type, error=str(e))
    
    async def _create_learning_insights(
        self,
        analysis: ConversationAnalysis,
        review: MeetingReview
    ) -> int:
        """Create learning insights from analysis"""
        insights_created = 0
        
        try:
            # Create insights from successful strategies
            for strategy in analysis.successful_strategies[:3]:
                insight = LearningInsight(
                    insight_type="successful_strategy",
                    pattern_description=strategy,
                    supporting_data={
                        "session_id": analysis.session_id,
                        "effectiveness": analysis.overall_effectiveness,
                        "context": "post_meeting_analysis"
                    },
                    confidence_score=0.9
                )
                
                await self.feedback_service.store_learning_insight(insight)
                insights_created += 1
            
            # Create insights from failed strategies
            for failure in analysis.failed_strategies[:2]:
                insight = LearningInsight(
                    insight_type="failed_strategy",
                    pattern_description=f"AVOID: {failure}",
                    supporting_data={
                        "session_id": analysis.session_id,
                        "effectiveness": analysis.overall_effectiveness,
                        "context": "post_meeting_analysis"
                    },
                    confidence_score=0.8
                )
                
                await self.feedback_service.store_learning_insight(insight)
                insights_created += 1
            
            return insights_created
            
        except Exception as e:
            self.log_error("Failed to create learning insights", error=str(e))
            return 0
    
    async def _update_knowledge_base(self, updates: List[str]) -> int:
        """Update knowledge base with new insights"""
        # Mock implementation - would update actual knowledge base
        self.log_info("Updated knowledge base", update_count=len(updates))
        return len(updates)
    
    async def _update_learning_patterns(self, analysis: ConversationAnalysis) -> int:
        """Update learning patterns based on analysis"""
        patterns_updated = 0
        
        try:
            # Create patterns from successful strategies
            for strategy in analysis.successful_strategies:
                pattern = LearningPattern(
                    pattern_type="successful_response",
                    description=strategy,
                    success_rate=0.8,  # Would be calculated from historical data
                    context_requirements={
                        "effectiveness_threshold": 7.0,
                        "meeting_outcome": analysis.meeting_outcome
                    }
                )
                
                # Store pattern (mock implementation)
                patterns_updated += 1
            
            self.log_info("Updated learning patterns", pattern_count=patterns_updated)
            return patterns_updated
            
        except Exception as e:
            self.log_error("Failed to update learning patterns", error=str(e))
            return 0
    
    async def _update_system_performance_metrics(
        self,
        session_id: str,
        analysis: ConversationAnalysis,
        review: MeetingReview
    ):
        """Update overall system performance metrics"""
        try:
            # Update agent performance metrics
            for agent_type in ["opening", "discovery", "pitch", "objection", "closing"]:
                stage_score = review.stage_scores.get(agent_type, 5.0)
                is_success = stage_score >= 7.0
                
                # Mock update to agent performance
                self.log_info(
                    "Updated agent performance metrics",
                    agent_type=agent_type,
                    score=stage_score,
                    success=is_success
                )
            
        except Exception as e:
            self.log_error("Failed to update system performance metrics", error=str(e))
    
    def is_service_available(self) -> bool:
        """Check if meeting review service is available"""
        return (
            self.analysis_service.is_service_available() and
            self.feedback_service.is_service_available() and
            self.enhanced_agent_service.is_service_available()
        ) 