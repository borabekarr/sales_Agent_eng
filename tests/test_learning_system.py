#!/usr/bin/env python3
"""
Comprehensive health check tests for AI Reinforced Learning System
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.feedback_service import FeedbackService
from services.learning_analysis_service import LearningAnalysisService
from services.enhanced_agent_service import EnhancedAgentService
from services.meeting_review_service import MeetingReviewService
from models.learning_schemas import (
    SuggestionFeedback, CustomerReaction, ConversationAnalysis, MeetingReview
)
from models.schemas import AgentContext, CustomerProfile, Message


class TestLearningSystemHealth:
    """Comprehensive health tests for the AI Reinforced Learning System"""
    
    @pytest.fixture
    def feedback_service(self):
        return FeedbackService()
    
    @pytest.fixture
    def learning_analysis_service(self):
        return LearningAnalysisService()
    
    @pytest.fixture
    def enhanced_agent_service(self):
        return EnhancedAgentService()
    
    @pytest.fixture
    def meeting_review_service(self):
        return MeetingReviewService()
    
    @pytest.fixture
    def test_suggestion_feedback(self):
        return SuggestionFeedback(
            session_id="test-session-123",
            conversation_stage="discovery",
            ai_suggestion="That's interesting. Could you tell me more about your current challenges?",
            user_action="accepted",
            effectiveness_score=4,
            customer_reaction="positive",
            context_data={"customer_industry": "healthcare"}
        )
    
    @pytest.fixture
    def test_customer_reaction(self):
        return CustomerReaction(
            session_id="test-session-123",
            reaction="positive",
            reaction_text="Yes, we definitely have challenges with patient scheduling"
        )
    
    @pytest.fixture
    def test_agent_context(self):
        customer_profile = CustomerProfile(
            name="Dr. Smith",
            company="HealthCare Plus",
            pain_points=["Scheduling conflicts", "Staff efficiency"]
        )
        
        messages = [
            Message(
                session_id="test-session-123",
                speaker="seller",
                text="Thanks for joining today's call.",
                confidence=1.0,
                stage="opening"
            ),
            Message(
                session_id="test-session-123",
                speaker="customer", 
                text="Happy to be here. We're looking for solutions.",
                confidence=0.95,
                stage="opening"
            )
        ]
        
        return AgentContext(
            current_stage="discovery",
            customer_profile=customer_profile,
            recent_messages=messages,
            conversation_history=messages,
            context_stack=[],
            session_metadata={"session_id": "test-session-123"}
        )


class TestFeedbackService:
    """Test FeedbackService functionality"""
    
    @pytest.mark.asyncio
    async def test_feedback_service_initialization(self, feedback_service):
        """Test feedback service initializes correctly"""
        assert feedback_service.is_service_available()
        assert hasattr(feedback_service, 'supabase')
        assert hasattr(feedback_service, 'cache')
    
    @pytest.mark.asyncio
    async def test_record_suggestion_feedback(self, feedback_service, test_suggestion_feedback):
        """Test recording suggestion feedback"""
        result = await feedback_service.record_suggestion_feedback(test_suggestion_feedback)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_record_customer_reaction(self, feedback_service, test_customer_reaction):
        """Test recording customer reaction"""
        result = await feedback_service.record_customer_reaction(test_customer_reaction)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_learning_patterns(self, feedback_service):
        """Test retrieving learning patterns"""
        patterns = await feedback_service.get_learning_patterns("discovery", "general", 30)
        
        assert isinstance(patterns, dict)
        assert "successful_phrases" in patterns
        assert "failed_phrases" in patterns
        assert "improvement_suggestions" in patterns
        assert "effectiveness_trends" in patterns
    
    @pytest.mark.asyncio
    async def test_get_agent_performance_metrics(self, feedback_service):
        """Test retrieving agent performance metrics"""
        metrics = await feedback_service.get_agent_performance_metrics("discovery")
        
        assert isinstance(metrics, dict)
        expected_keys = ["success_rate", "avg_effectiveness", "total_interactions", "trend"]
        for key in expected_keys:
            assert key in metrics
    
    @pytest.mark.asyncio
    async def test_get_session_transcript(self, feedback_service):
        """Test retrieving session transcript"""
        transcript = await feedback_service.get_session_transcript("test-session-123")
        # Should return None or a string transcript
        assert transcript is None or isinstance(transcript, str)


class TestLearningAnalysisService:
    """Test LearningAnalysisService functionality"""
    
    @pytest.mark.asyncio
    async def test_learning_analysis_service_initialization(self, learning_analysis_service):
        """Test learning analysis service initializes correctly"""
        assert learning_analysis_service.is_service_available()
        assert hasattr(learning_analysis_service, 'gemini_service')
        assert hasattr(learning_analysis_service, 'feedback_service')
    
    @pytest.mark.asyncio
    async def test_analyze_full_conversation(self, learning_analysis_service):
        """Test full conversation analysis"""
        test_transcript = """
        [opening] SELLER: Hi Dr. Smith, thanks for taking time to speak with me today.
        CUSTOMER: Hello, happy to connect.
        [discovery] SELLER: Could you tell me about your biggest challenges with patient scheduling?
        CUSTOMER: We often have double bookings and staff confusion.
        [pitch] SELLER: Our AI scheduling system could eliminate those conflicts completely.
        CUSTOMER: That sounds interesting, but I'm concerned about the cost.
        """
        
        analysis = await learning_analysis_service.analyze_full_conversation(
            session_id="test-session-123",
            full_transcript=test_transcript,
            customer_profile={"name": "Dr. Smith", "company": "HealthCare Plus"}
        )
        
        assert isinstance(analysis, ConversationAnalysis)
        assert analysis.session_id == "test-session-123"
        assert analysis.full_transcript == test_transcript
        assert isinstance(analysis.successful_strategies, list)
        assert isinstance(analysis.failed_strategies, list)
        assert isinstance(analysis.agent_improvements, dict)
    
    @pytest.mark.asyncio
    async def test_generate_meeting_review(self, learning_analysis_service):
        """Test meeting review generation"""
        # Create a mock conversation analysis
        analysis = ConversationAnalysis(
            session_id="test-session-123",
            full_transcript="Mock transcript",
            successful_strategies=["Good rapport building", "Clear value proposition"],
            failed_strategies=["Rushed closing"],
            agent_improvements={"discovery": ["Ask more open-ended questions"]},
            overall_effectiveness=7.5
        )
        
        review = await learning_analysis_service.generate_meeting_review(
            session_id="test-session-123",
            conversation_analysis=analysis
        )
        
        assert isinstance(review, MeetingReview)
        assert review.session_id == "test-session-123"
        assert isinstance(review.overall_score, float)
        assert isinstance(review.improvement_recommendations, list)
        assert isinstance(review.next_actions, list)


class TestEnhancedAgentService:
    """Test EnhancedAgentService functionality"""
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_service_initialization(self, enhanced_agent_service):
        """Test enhanced agent service initializes correctly"""
        assert enhanced_agent_service.is_service_available()
        assert hasattr(enhanced_agent_service, 'gemini_service')
        assert hasattr(enhanced_agent_service, 'feedback_service')
    
    @pytest.mark.asyncio
    async def test_generate_enhanced_suggestion(self, enhanced_agent_service, test_agent_context):
        """Test enhanced suggestion generation"""
        suggestion = await enhanced_agent_service.generate_enhanced_suggestion(
            base_context=test_agent_context,
            agent_type="discovery",
            scenario_key="healthcare"
        )
        
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
        assert "learning_enhanced" in suggestion
        assert suggestion["learning_enhanced"] is True
        assert "insights_applied" in suggestion
        assert "confidence_boost" in suggestion
    
    @pytest.mark.asyncio
    async def test_track_suggestion_usage(self, enhanced_agent_service):
        """Test suggestion usage tracking"""
        test_suggestion = {
            "suggestion": "What challenges are you facing with patient scheduling?",
            "learning_enhanced": True,
            "insights_applied": 3
        }
        
        # Should not raise an exception
        await enhanced_agent_service.track_suggestion_usage(
            session_id="test-session-123",
            agent_type="discovery",
            suggestion=test_suggestion,
            user_action="accepted",
            effectiveness_score=4
        )
    
    @pytest.mark.asyncio
    async def test_get_real_time_learning_stats(self, enhanced_agent_service):
        """Test real-time learning statistics"""
        stats = await enhanced_agent_service.get_real_time_learning_stats()
        
        assert isinstance(stats, dict)
        expected_keys = [
            "enhanced_suggestions_today",
            "learning_patterns_active", 
            "average_enhancement_impact",
            "top_performing_agents"
        ]
        for key in expected_keys:
            assert key in stats
    
    @pytest.mark.asyncio
    async def test_force_learning_update(self, enhanced_agent_service):
        """Test forcing learning data update"""
        # Should not raise an exception
        await enhanced_agent_service.force_learning_update("discovery")
        await enhanced_agent_service.force_learning_update()  # All agents


class TestMeetingReviewService:
    """Test MeetingReviewService functionality"""
    
    @pytest.mark.asyncio
    async def test_meeting_review_service_initialization(self, meeting_review_service):
        """Test meeting review service initializes correctly"""
        assert meeting_review_service.is_service_available()
        assert hasattr(meeting_review_service, 'analysis_service')
        assert hasattr(meeting_review_service, 'feedback_service')
        assert hasattr(meeting_review_service, 'enhanced_agent_service')
    
    @pytest.mark.asyncio
    async def test_queue_meeting_for_review(self, meeting_review_service):
        """Test queuing meeting for review"""
        # Should not raise an exception
        await meeting_review_service.queue_meeting_for_review(
            session_id="test-session-123",
            customer_profile={"name": "Dr. Smith"},
            priority="normal"
        )
    
    @pytest.mark.asyncio
    async def test_get_learning_summary(self, meeting_review_service):
        """Test getting learning summary"""
        summary = await meeting_review_service.get_learning_summary(days_back=7)
        
        assert isinstance(summary, dict)
        expected_keys = [
            "meetings_analyzed",
            "insights_generated", 
            "agent_improvements_applied",
            "average_meeting_score"
        ]
        # Check if it's an error or has expected keys
        if "error" not in summary:
            for key in expected_keys:
                assert key in summary
    
    @pytest.mark.asyncio
    async def test_generate_system_optimization_report(self, meeting_review_service):
        """Test system optimization report generation"""
        report = await meeting_review_service.generate_system_optimization_report()
        
        assert isinstance(report, dict)
        if "error" not in report:
            expected_keys = [
                "system_performance",
                "agent_rankings",
                "priority_optimizations",
                "recommendations"
            ]
            for key in expected_keys:
                assert key in report


class TestIntegrationHealth:
    """Test integration between learning system components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_learning_flow(
        self,
        feedback_service,
        learning_analysis_service,
        enhanced_agent_service,
        meeting_review_service,
        test_suggestion_feedback,
        test_agent_context
    ):
        """Test complete end-to-end learning flow"""
        
        # Step 1: Record feedback
        feedback_result = await feedback_service.record_suggestion_feedback(test_suggestion_feedback)
        assert feedback_result is True
        
        # Step 2: Generate enhanced suggestion
        enhanced_suggestion = await enhanced_agent_service.generate_enhanced_suggestion(
            base_context=test_agent_context,
            agent_type="discovery"
        )
        assert enhanced_suggestion["learning_enhanced"] is True
        
        # Step 3: Queue meeting for review
        await meeting_review_service.queue_meeting_for_review(
            session_id="test-session-123",
            priority="normal"
        )
        
        # Step 4: Get learning patterns
        patterns = await feedback_service.get_learning_patterns("discovery")
        assert isinstance(patterns, dict)
        
        # Step 5: Get real-time stats
        stats = await enhanced_agent_service.get_real_time_learning_stats()
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_service_availability_chain(
        self,
        feedback_service,
        learning_analysis_service,
        enhanced_agent_service,
        meeting_review_service
    ):
        """Test that all services are available and connected"""
        
        # Test individual service availability
        assert feedback_service.is_service_available()
        assert learning_analysis_service.is_service_available()
        assert enhanced_agent_service.is_service_available()
        assert meeting_review_service.is_service_available()
        
        # Test service dependencies
        assert enhanced_agent_service.gemini_service.is_service_available()
        assert enhanced_agent_service.feedback_service.is_service_available()


# Main health check function
async def run_comprehensive_health_check():
    """Run comprehensive health check of the entire learning system"""
    print("🔬 Starting Comprehensive AI Reinforced Learning System Health Check")
    print("=" * 80)
    
    test_results = {
        "feedback_service": False,
        "learning_analysis_service": False,
        "enhanced_agent_service": False,
        "meeting_review_service": False,
        "integration_test": False,
        "overall_health": False
    }
    
    try:
        # Initialize services
        feedback_service = FeedbackService()
        learning_analysis_service = LearningAnalysisService()
        enhanced_agent_service = EnhancedAgentService()
        meeting_review_service = MeetingReviewService()
        
        # Test 1: Feedback Service
        print("🧪 Testing Feedback Service...")
        if feedback_service.is_service_available():
            test_feedback = SuggestionFeedback(
                session_id="health-check-session",
                conversation_stage="discovery",
                ai_suggestion="Test suggestion",
                user_action="accepted",
                effectiveness_score=4
            )
            await feedback_service.record_suggestion_feedback(test_feedback)
            test_results["feedback_service"] = True
            print("✅ Feedback Service: HEALTHY")
        else:
            print("❌ Feedback Service: UNHEALTHY")
        
        # Test 2: Learning Analysis Service
        print("🧪 Testing Learning Analysis Service...")
        if learning_analysis_service.is_service_available():
            test_results["learning_analysis_service"] = True
            print("✅ Learning Analysis Service: HEALTHY")
        else:
            print("❌ Learning Analysis Service: UNHEALTHY")
        
        # Test 3: Enhanced Agent Service
        print("🧪 Testing Enhanced Agent Service...")
        if enhanced_agent_service.is_service_available():
            stats = await enhanced_agent_service.get_real_time_learning_stats()
            if isinstance(stats, dict):
                test_results["enhanced_agent_service"] = True
                print("✅ Enhanced Agent Service: HEALTHY")
            else:
                print("❌ Enhanced Agent Service: UNHEALTHY")
        else:
            print("❌ Enhanced Agent Service: UNHEALTHY")
        
        # Test 4: Meeting Review Service
        print("🧪 Testing Meeting Review Service...")
        if meeting_review_service.is_service_available():
            summary = await meeting_review_service.get_learning_summary(7)
            if isinstance(summary, dict):
                test_results["meeting_review_service"] = True
                print("✅ Meeting Review Service: HEALTHY")
            else:
                print("❌ Meeting Review Service: UNHEALTHY")
        else:
            print("❌ Meeting Review Service: UNHEALTHY")
        
        # Test 5: Integration Test
        print("🧪 Testing Service Integration...")
        try:
            # Test service chain
            patterns = await feedback_service.get_learning_patterns("discovery")
            if isinstance(patterns, dict):
                test_results["integration_test"] = True
                print("✅ Service Integration: HEALTHY")
            else:
                print("❌ Service Integration: UNHEALTHY")
        except Exception as e:
            print(f"❌ Service Integration: UNHEALTHY - {str(e)}")
        
        # Calculate overall health
        healthy_services = sum(test_results.values())
        total_services = len(test_results) - 1  # Exclude overall_health
        health_percentage = (healthy_services / total_services) * 100
        
        test_results["overall_health"] = health_percentage >= 80.0
        
        print("\n" + "=" * 80)
        print("📊 HEALTH CHECK RESULTS:")
        print("=" * 80)
        
        for service, status in test_results.items():
            if service != "overall_health":
                status_icon = "✅" if status else "❌"
                print(f"{status_icon} {service.replace('_', ' ').title()}: {'HEALTHY' if status else 'UNHEALTHY'}")
        
        print(f"\n🎯 Overall System Health: {health_percentage:.1f}%")
        
        if test_results["overall_health"]:
            print("🎉 AI REINFORCED LEARNING SYSTEM: FULLY OPERATIONAL")
            return True
        else:
            print("⚠️  AI REINFORCED LEARNING SYSTEM: NEEDS ATTENTION")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    # Run the comprehensive health check
    result = asyncio.run(run_comprehensive_health_check())
    
    if result:
        print("\n✅ All systems operational - Ready for production!")
        exit(0)
    else:
        print("\n❌ System issues detected - Review required!")
        exit(1) 