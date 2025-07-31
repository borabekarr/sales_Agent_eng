import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models.schemas import (
    Message, CustomerProfile, ConversationSummary, 
    PerformanceMetrics, SalesStage, StageProgress
)
from utils.logging import LoggerMixin


class ConversationService(LoggerMixin):
    """Service for managing conversation state and history"""
    
    def __init__(self):
        self.sales_stages = self._initialize_sales_stages()
        self.stage_transitions = self._initialize_stage_transitions()
    
    def _initialize_sales_stages(self) -> Dict[str, SalesStage]:
        """Initialize sales stage definitions"""
        return {
            "opening": SalesStage(
                name="opening",
                description="Initial rapport building and introduction",
                objectives=[
                    "Establish trust and rapport",
                    "Set meeting agenda",
                    "Understand customer's time constraints",
                    "Create comfortable atmosphere"
                ],
                key_questions=[
                    "How are you doing today?",
                    "What brings you to explore this solution?",
                    "How much time do we have together?",
                    "What would make this conversation valuable for you?"
                ],
                success_criteria=[
                    "Customer is engaged and responsive",
                    "Agenda is set and agreed upon",
                    "Professional rapport established",
                    "Customer shows openness to continue"
                ],
                next_stages=["discovery"]
            ),
            
            "discovery": SalesStage(
                name="discovery",
                description="Understanding customer needs and pain points",
                objectives=[
                    "Identify key pain points",
                    "Understand current solutions",
                    "Qualify budget and timeline",
                    "Determine decision-making process"
                ],
                key_questions=[
                    "What challenges are you facing currently?",
                    "How are you handling this today?",
                    "What would an ideal solution look like?",
                    "Who else is involved in this decision?",
                    "What's your timeline for making a change?"
                ],
                success_criteria=[
                    "Clear understanding of pain points",
                    "Budget range identified",
                    "Decision process understood",
                    "Timeline established"
                ],
                next_stages=["pitch", "objection"]
            ),
            
            "pitch": SalesStage(
                name="pitch",
                description="Presenting solution and value proposition",
                objectives=[
                    "Connect features to identified needs",
                    "Demonstrate clear ROI",
                    "Address specific pain points",
                    "Build value and urgency"
                ],
                key_questions=[
                    "How does this address your specific challenge?",
                    "What impact would this have on your business?",
                    "How does this compare to what you're doing now?",
                    "What questions do you have about the solution?"
                ],
                success_criteria=[
                    "Customer sees clear value",
                    "Questions indicate interest",
                    "Pain points are addressed",
                    "ROI is understood"
                ],
                next_stages=["objection", "closing"]
            ),
            
            "objection": SalesStage(
                name="objection",
                description="Handling concerns and resistance",
                objectives=[
                    "Understand root concerns",
                    "Provide evidence and proof",
                    "Address budget concerns",
                    "Handle timing objections"
                ],
                key_questions=[
                    "What concerns you most about this?",
                    "What would need to change for this to work?",
                    "How can we address that concern?",
                    "What evidence would help you feel confident?"
                ],
                success_criteria=[
                    "Objections are fully addressed",
                    "Customer confidence increases",
                    "Path forward is clear",
                    "Resistance is reduced"
                ],
                next_stages=["pitch", "closing", "discovery"]
            ),
            
            "closing": SalesStage(
                name="closing",
                description="Finalizing deal and next steps",
                objectives=[
                    "Summarize value and fit",
                    "Ask for commitment",
                    "Plan implementation",
                    "Set clear next steps"
                ],
                key_questions=[
                    "Are you ready to move forward?",
                    "What questions do you still have?",
                    "When would you like to get started?",
                    "What does the approval process look like?"
                ],
                success_criteria=[
                    "Commitment is made",
                    "Next steps are clear",
                    "Timeline is established",
                    "Implementation planned"
                ],
                next_stages=[]
            )
        }
    
    def _initialize_stage_transitions(self) -> Dict[str, List[str]]:
        """Initialize valid stage transitions"""
        return {
            "opening": ["discovery"],
            "discovery": ["pitch", "objection"],
            "pitch": ["objection", "closing"],
            "objection": ["pitch", "closing", "discovery"],
            "closing": []
        }
    
    async def add_message(
        self, 
        session_id: str, 
        speaker: str, 
        text: str, 
        confidence: float = 1.0,
        stage: str = "discovery",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a new message to conversation history"""
        message = Message(
            session_id=session_id,
            speaker=speaker,
            text=text,
            confidence=confidence,
            stage=stage,
            metadata=metadata or {}
        )
        
        self.log_info(
            "Added conversation message",
            session_id=session_id,
            speaker=speaker,
            stage=stage,
            text_length=len(text)
        )
        
        return message
    
    async def update_customer_profile(
        self,
        profile: CustomerProfile,
        new_insights: Dict[str, Any]
    ) -> CustomerProfile:
        """Update customer profile with new insights"""
        updates = {}
        
        # Update basic info
        if "name" in new_insights and new_insights["name"]:
            updates["name"] = new_insights["name"]
        if "company" in new_insights and new_insights["company"]:
            updates["company"] = new_insights["company"]
        if "role" in new_insights and new_insights["role"]:
            updates["role"] = new_insights["role"]
        
        # Update lists (append unique items)
        if "pain_points" in new_insights:
            existing_pain_points = set(profile.pain_points)
            new_pain_points = [p for p in new_insights["pain_points"] if p not in existing_pain_points]
            updates["pain_points"] = profile.pain_points + new_pain_points
        
        if "interests" in new_insights:
            existing_interests = set(profile.interests)
            new_interests = [i for i in new_insights["interests"] if i not in existing_interests]
            updates["interests"] = profile.interests + new_interests
        
        # Update other fields
        for field in ["budget_range", "decision_authority", "timeline", "sentiment"]:
            if field in new_insights and new_insights[field]:
                updates[field] = new_insights[field]
        
        # Create updated profile
        updated_profile = profile.copy(update=updates)
        
        self.log_info(
            "Updated customer profile",
            updates=list(updates.keys()),
            pain_points_count=len(updated_profile.pain_points),
            interests_count=len(updated_profile.interests)
        )
        
        return updated_profile
    
    async def determine_next_stage(
        self,
        current_stage: str,
        conversation_history: List[Message],
        customer_profile: CustomerProfile
    ) -> Dict[str, Any]:
        """Determine if stage transition is appropriate"""
        stage_info = self.sales_stages.get(current_stage)
        if not stage_info:
            return {"should_advance": False, "reason": "Invalid current stage"}
        
        # Analyze recent messages for stage completion signals
        recent_messages = conversation_history[-5:] if len(conversation_history) >= 5 else conversation_history
        
        # Check stage completion
        completion_score = await self._calculate_stage_completion(
            current_stage, recent_messages, customer_profile
        )
        
        # Determine if ready to advance
        should_advance = completion_score >= 0.7
        
        if should_advance:
            # Suggest next stage
            possible_next_stages = stage_info.next_stages
            if possible_next_stages:
                # Simple logic: choose first available next stage
                # In a real implementation, this would be more sophisticated
                next_stage = possible_next_stages[0]
                
                # Special logic for stage selection
                if current_stage == "discovery" and len(customer_profile.pain_points) >= 2:
                    next_stage = "pitch"
                elif current_stage == "pitch" and any("concern" in msg.text.lower() or "but" in msg.text.lower() 
                                                     for msg in recent_messages if msg.speaker == "customer"):
                    next_stage = "objection"
                
                return {
                    "should_advance": True,
                    "next_stage": next_stage,
                    "completion_score": completion_score,
                    "reason": f"Stage objectives met (score: {completion_score:.2f})"
                }
        
        return {
            "should_advance": False,
            "completion_score": completion_score,
            "reason": f"Stage not complete (score: {completion_score:.2f})"
        }
    
    async def _calculate_stage_completion(
        self,
        stage: str,
        recent_messages: List[Message],
        customer_profile: CustomerProfile
    ) -> float:
        """Calculate stage completion score"""
        if stage == "opening":
            # Check for rapport and agenda setting
            has_greeting = any("hello" in msg.text.lower() or "hi" in msg.text.lower() 
                              for msg in recent_messages)
            has_engagement = len([msg for msg in recent_messages if msg.speaker == "customer"]) >= 2
            return 0.8 if has_greeting and has_engagement else 0.3
        
        elif stage == "discovery":
            # Check for pain points and qualification
            pain_points_score = min(len(customer_profile.pain_points) * 0.3, 1.0)
            qualification_score = 0.5 if customer_profile.budget_range or customer_profile.timeline else 0
            return (pain_points_score + qualification_score) / 2
        
        elif stage == "pitch":
            # Check for value presentation and customer interest
            value_words = ["value", "benefit", "solution", "help", "improve"]
            has_value_prop = any(word in " ".join([msg.text.lower() for msg in recent_messages]) 
                               for word in value_words)
            customer_questions = len([msg for msg in recent_messages 
                                    if msg.speaker == "customer" and "?" in msg.text])
            return 0.7 if has_value_prop and customer_questions >= 1 else 0.4
        
        elif stage == "objection":
            # Check for objection resolution
            objection_words = ["concern", "worry", "but", "however", "issue"]
            resolution_words = ["understand", "address", "solution", "resolve"]
            
            has_objections = any(word in " ".join([msg.text.lower() for msg in recent_messages]) 
                               for word in objection_words)
            has_resolution = any(word in " ".join([msg.text.lower() for msg in recent_messages]) 
                               for word in resolution_words)
            
            return 0.8 if has_objections and has_resolution else 0.3
        
        elif stage == "closing":
            # Check for commitment and next steps
            commitment_words = ["yes", "agree", "proceed", "forward", "start"]
            has_commitment = any(word in " ".join([msg.text.lower() for msg in recent_messages 
                                                 if msg.speaker == "customer"]) 
                               for word in commitment_words)
            return 0.9 if has_commitment else 0.2
        
        return 0.5  # Default score
    
    async def calculate_conversation_metrics(
        self,
        session_id: str,
        conversation_history: List[Message],
        start_time: datetime
    ) -> PerformanceMetrics:
        """Calculate performance metrics for conversation"""
        if not conversation_history:
            return PerformanceMetrics(
                session_id=session_id,
                avg_response_time=0,
                suggestion_accuracy=0,
                customer_engagement=0,
                stage_progression_rate=0,
                interruption_count=0,
                successful_transitions=0,
                total_transitions=0,
                conversation_flow_score=0
            )
        
        # Calculate response times
        response_times = []
        customer_messages = [msg for msg in conversation_history if msg.speaker == "customer"]
        seller_messages = [msg for msg in conversation_history if msg.speaker == "seller"]
        
        for i in range(1, len(conversation_history)):
            prev_msg = conversation_history[i-1]
            curr_msg = conversation_history[i]
            
            if (prev_msg.speaker == "customer" and curr_msg.speaker == "seller"):
                time_diff = (curr_msg.timestamp - prev_msg.timestamp).total_seconds()
                if time_diff <= 60:  # Only count reasonable response times
                    response_times.append(time_diff)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate customer engagement
        customer_message_count = len(customer_messages)
        total_message_count = len(conversation_history)
        customer_engagement = customer_message_count / total_message_count if total_message_count > 0 else 0
        
        # Calculate stage transitions
        stages_seen = set(msg.stage for msg in conversation_history)
        stage_progression_rate = len(stages_seen) / 5  # 5 total stages
        
        # Count interruptions (messages that come quickly after each other from same speaker)
        interruption_count = 0
        for i in range(1, len(conversation_history)):
            prev_msg = conversation_history[i-1]
            curr_msg = conversation_history[i]
            
            if (prev_msg.speaker == curr_msg.speaker and 
                (curr_msg.timestamp - prev_msg.timestamp).total_seconds() < 3):
                interruption_count += 1
        
        # Simple conversation flow score
        conversation_duration = (datetime.utcnow() - start_time).total_seconds() / 60  # minutes
        optimal_duration = 30  # 30 minutes optimal
        duration_score = 1.0 - abs(conversation_duration - optimal_duration) / optimal_duration
        duration_score = max(0, min(1, duration_score))
        
        flow_score = (customer_engagement + stage_progression_rate + duration_score) / 3
        
        return PerformanceMetrics(
            session_id=session_id,
            response_times=response_times,
            avg_response_time=avg_response_time,
            suggestion_accuracy=0.8,  # Would be calculated based on actual usage
            customer_engagement=customer_engagement,
            stage_progression_rate=stage_progression_rate,
            interruption_count=interruption_count,
            successful_transitions=len(stages_seen) - 1,
            total_transitions=len(stages_seen),
            conversation_flow_score=flow_score
        )
    
    async def generate_conversation_summary(
        self,
        session_id: str,
        conversation_history: List[Message],
        customer_profile: CustomerProfile,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> ConversationSummary:
        """Generate comprehensive conversation summary"""
        end_time = end_time or datetime.utcnow()
        duration = (end_time - start_time).total_seconds() / 60  # minutes
        
        # Extract key topics
        all_text = " ".join([msg.text for msg in conversation_history])
        key_topics = self._extract_key_topics(all_text)
        
        # Identify objections
        objections = []
        objection_indicators = ["concern", "worry", "but", "however", "issue", "problem"]
        for msg in conversation_history:
            if (msg.speaker == "customer" and 
                any(indicator in msg.text.lower() for indicator in objection_indicators)):
                objections.append(msg.text[:100] + "..." if len(msg.text) > 100 else msg.text)
        
        # Determine outcome
        outcome = self._determine_outcome(conversation_history, customer_profile)
        
        # Generate next steps
        next_steps = self._generate_next_steps(conversation_history, customer_profile, outcome)
        
        # Analyze sentiment
        sentiment_analysis = self._analyze_conversation_sentiment(conversation_history)
        
        # Count stages covered
        stages_covered = list(set(msg.stage for msg in conversation_history))
        
        return ConversationSummary(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            message_count=len(conversation_history),
            customer_profile=customer_profile,
            stages_covered=stages_covered,
            key_topics=key_topics,
            objections_raised=objections,
            outcome=outcome,
            next_steps=next_steps,
            sentiment_analysis=sentiment_analysis,
            ai_suggestions_used=0  # Would be tracked separately
        )
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from conversation text"""
        # Simple keyword extraction - in production, use NLP
        business_keywords = [
            "sales", "revenue", "growth", "customers", "market", "competition",
            "efficiency", "productivity", "cost", "budget", "ROI", "solution",
            "implementation", "integration", "features", "benefits", "value"
        ]
        
        text_lower = text.lower()
        found_topics = [keyword for keyword in business_keywords if keyword in text_lower]
        return list(set(found_topics))[:10]  # Return top 10 unique topics
    
    def _determine_outcome(self, conversation_history: List[Message], customer_profile: CustomerProfile) -> str:
        """Determine conversation outcome"""
        last_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        
        positive_indicators = ["yes", "agree", "proceed", "forward", "interested", "sounds good"]
        negative_indicators = ["no", "not interested", "maybe later", "think about it"]
        neutral_indicators = ["follow up", "more information", "discuss internally"]
        
        last_customer_messages = [msg.text.lower() for msg in last_messages if msg.speaker == "customer"]
        combined_text = " ".join(last_customer_messages)
        
        if any(indicator in combined_text for indicator in positive_indicators):
            return "positive"
        elif any(indicator in combined_text for indicator in negative_indicators):
            return "negative"
        elif any(indicator in combined_text for indicator in neutral_indicators):
            return "follow_up_needed"
        else:
            return "unclear"
    
    def _generate_next_steps(
        self, 
        conversation_history: List[Message], 
        customer_profile: CustomerProfile,
        outcome: str
    ) -> List[str]:
        """Generate recommended next steps"""
        if outcome == "positive":
            return [
                "Send proposal or contract",
                "Schedule implementation call",
                "Introduce implementation team",
                "Set project timeline"
            ]
        elif outcome == "follow_up_needed":
            return [
                "Send summary of key points discussed",
                "Provide additional information requested",
                "Schedule follow-up call in 1 week",
                "Connect with decision makers"
            ]
        elif outcome == "negative":
            return [
                "Understand specific concerns",
                "Provide case studies or references",
                "Schedule future check-in",
                "Add to nurture campaign"
            ]
        else:
            return [
                "Send meeting summary",
                "Clarify next steps",
                "Schedule follow-up call",
                "Provide additional resources"
            ]
    
    def _analyze_conversation_sentiment(self, conversation_history: List[Message]) -> Dict[str, float]:
        """Analyze overall conversation sentiment"""
        # Simple sentiment analysis - in production, use proper sentiment analysis
        positive_words = ["great", "excellent", "perfect", "love", "amazing", "fantastic"]
        negative_words = ["bad", "terrible", "awful", "hate", "horrible", "disappointing"]
        neutral_words = ["okay", "fine", "alright", "maybe", "possibly"]
        
        customer_messages = [msg.text.lower() for msg in conversation_history if msg.speaker == "customer"]
        all_customer_text = " ".join(customer_messages)
        
        positive_count = sum(1 for word in positive_words if word in all_customer_text)
        negative_count = sum(1 for word in negative_words if word in all_customer_text)
        neutral_count = sum(1 for word in neutral_words if word in all_customer_text)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return {"positive": 0.5, "negative": 0.3, "neutral": 0.2}
        
        return {
            "positive": positive_count / total_sentiment_words,
            "negative": negative_count / total_sentiment_words,
            "neutral": neutral_count / total_sentiment_words
        }
    
    def get_stage_info(self, stage_name: str) -> Optional[SalesStage]:
        """Get information about a specific sales stage"""
        return self.sales_stages.get(stage_name)
    
    def get_valid_transitions(self, current_stage: str) -> List[str]:
        """Get valid stage transitions from current stage"""
        return self.stage_transitions.get(current_stage, []) 