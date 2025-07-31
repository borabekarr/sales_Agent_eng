from typing import Dict, Any, List
from models.schemas import AgentContext
from services.gemini_api import GeminiAPIService
from utils.logging import LoggerMixin


class ClosingAgent(LoggerMixin):
    """Specialized agent for closing deals and finalizing next steps"""
    
    def __init__(self, gemini_api_service: GeminiAPIService):
        self.gemini_api_service = gemini_api_service
        self.agent_type = "closing"
        
        # Different closing techniques and when to use them
        self.closing_techniques = {
            "assumptive": {
                "description": "Assume the sale and discuss implementation",
                "best_for": "Highly engaged customers with clear buying signals",
                "indicators": ["interested", "sounds good", "how does this work"],
                "approach": "When would you like to get started?"
            },
            "summary": {
                "description": "Summarize value and ask for decision",
                "best_for": "Customers who need reinforcement of value",
                "indicators": ["thinking", "considering", "evaluating"],
                "approach": "Based on everything we've discussed, does this make sense?"
            },
            "alternative": {
                "description": "Offer choice between options",
                "best_for": "Customers who need sense of control",
                "indicators": ["options", "choices", "flexibility"],
                "approach": "Would you prefer option A or option B?"
            },
            "urgency": {
                "description": "Create time-based motivation",
                "best_for": "Price-sensitive or procrastinating customers",
                "indicators": ["later", "think about it", "timing"],
                "approach": "If we move forward this month, I can include..."
            },
            "trial": {
                "description": "Offer low-risk trial or pilot",
                "best_for": "Risk-averse or skeptical customers",
                "indicators": ["sure", "risk", "try", "test"],
                "approach": "How about we start with a pilot program?"
            },
            "question": {
                "description": "Ask what's needed to move forward",
                "best_for": "Customers with unclear objections",
                "indicators": ["not sure", "concerns", "questions"],
                "approach": "What questions do you have before we move forward?"
            }
        }
        
        # Closing sequence steps
        self.closing_sequence = [
            "value_summary",
            "fit_confirmation", 
            "decision_check",
            "close_attempt",
            "next_steps",
            "implementation_planning"
        ]
    
    async def generate_suggestion(self, context: AgentContext) -> Dict[str, Any]:
        """Generate closing stage suggestions"""
        try:
            # Analyze closing opportunity
            closing_analysis = self._analyze_closing_opportunity(context)
            
            # Select appropriate closing technique
            closing_technique = self._select_closing_technique(context, closing_analysis)
            
            # Determine current closing sequence step
            current_step = self._determine_closing_step(context, closing_analysis)
            
            # Build custom prompt
            custom_prompt = self._build_closing_prompt(context, closing_technique, current_step, closing_analysis)
            
            # Generate suggestion using Gemini API
            response = await self.gemini_api_service.generate_suggestion(
                context=context,
                agent_type=self.agent_type,
                conversation_history=context.recent_messages,
                custom_prompt=custom_prompt
            )
            
            # Enhance response with closing-specific logic
            enhanced_response = self._enhance_closing_response(response, context, closing_technique, current_step)
            
            self.log_info(
                "Generated closing suggestion",
                session_id=context.session_metadata.get("session_id"),
                closing_technique=closing_technique,
                closing_step=current_step
            )
            
            return enhanced_response
            
        except Exception as e:
            self.log_error("Error generating closing suggestion", error=str(e))
            return self._get_fallback_closing_response()
    
    def _analyze_closing_opportunity(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze the closing opportunity and customer readiness"""
        customer_messages = [msg for msg in context.conversation_history if msg.speaker == "customer"]
        recent_text = " ".join([msg.text.lower() for msg in customer_messages[-5:]])
        
        # Assess buying signals
        buying_signals = self._assess_buying_signals(recent_text, customer_messages)
        
        # Assess objection resolution
        objections_resolved = self._assess_objection_resolution(context, recent_text)
        
        # Assess customer engagement
        engagement_level = self._assess_closing_engagement(customer_messages)
        
        # Assess decision authority
        decision_authority = self._assess_decision_authority(context, recent_text)
        
        # Assess urgency
        urgency_level = self._assess_urgency_signals(recent_text)
        
        # Assess risk factors
        risk_factors = self._assess_closing_risks(context, recent_text)
        
        # Calculate overall closing readiness score
        readiness_score = self._calculate_readiness_score(
            buying_signals, objections_resolved, engagement_level, 
            decision_authority, urgency_level, risk_factors
        )
        
        return {
            "buying_signals": buying_signals,
            "objections_resolved": objections_resolved,
            "engagement_level": engagement_level,
            "decision_authority": decision_authority,
            "urgency_level": urgency_level,
            "risk_factors": risk_factors,
            "readiness_score": readiness_score,
            "recommendation": self._get_closing_recommendation(readiness_score)
        }
    
    def _select_closing_technique(self, context: AgentContext, analysis: Dict[str, Any]) -> str:
        """Select the most appropriate closing technique"""
        recent_text = " ".join([msg.text.lower() for msg in context.recent_messages if msg.speaker == "customer"])
        
        # High readiness = assumptive close
        if analysis["readiness_score"] >= 0.8:
            return "assumptive"
        
        # High engagement but needs value reinforcement = summary close
        if analysis["engagement_level"] == "high" and analysis["readiness_score"] >= 0.6:
            return "summary"
        
        # Risk-averse customers = trial close
        if any(word in recent_text for word in ["risk", "sure", "careful", "safe"]):
            return "trial"
        
        # Time pressures = urgency close
        if analysis["urgency_level"] == "high" or any(word in recent_text for word in ["budget", "quarter", "deadline"]):
            return "urgency"
        
        # Indecisive customers = alternative choice
        if any(word in recent_text for word in ["options", "choices", "compare", "different"]):
            return "alternative"
        
        # Unclear objections = question close
        if analysis["risk_factors"] > 2:
            return "question"
        
        # Default to summary close
        return "summary"
    
    def _determine_closing_step(self, context: AgentContext, analysis: Dict[str, Any]) -> str:
        """Determine current step in closing sequence"""
        conversation_text = " ".join([msg.text.lower() for msg in context.conversation_history])
        
        # Check what's been covered
        if "summary" not in conversation_text and "recap" not in conversation_text:
            return "value_summary"
        elif "fit" not in conversation_text and "right solution" not in conversation_text:
            return "fit_confirmation"
        elif "?" not in conversation_text[-200:]:  # No recent questions
            return "decision_check"
        elif "move forward" not in conversation_text and "get started" not in conversation_text:
            return "close_attempt"
        elif "next step" not in conversation_text and "timeline" not in conversation_text:
            return "next_steps"
        else:
            return "implementation_planning"
    
    def _build_closing_prompt(self, context: AgentContext, closing_technique: str, current_step: str, closing_analysis: dict) -> str:
        """Build closing agent prompt for finalizing the sale"""
        customer_data = context.customer_profile.dict()
        recent_history = []
        for msg in context.recent_messages[-5:]:
            speaker = "SELLER" if msg.speaker == "seller" else "CUSTOMER"
            recent_history.append(f"{speaker}: {msg.text}")
        
        recent_history_text = "\n".join(recent_history) if recent_history else "No recent history"
        customer_message = context.recent_messages[-1].text if context.recent_messages else ""
        
        return f"""
<role>You are the Closing Agent. Your goal is to confidently and clearly ask for the order. You have built the case, handled the objections, and now it's time to guide the customer to a decision. You are a reasonable man making a reasonable request.</role>

<context>
- Current Stage: Closing
- Customer Profile: {customer_data}
- Last Customer Input: "{customer_message}"
- Conversation History: {recent_history_text}
- Closing Technique: {closing_technique}
- Current Step: {current_step}
- Closing Analysis: {closing_analysis}
</context>

<instructions>
1.  **Ask Closing Questions:** Use the three-yes framework. Ask questions that are easy "yes" responses based on the conversation so far. Use "feel" instead of "think."
2.  **Ask for the Order:** Once you get buying signals or a series of "yes" answers, ask for the order directly but smoothly.
3.  **Use Powerful Closing Patterns:** Frame the close with a pattern like "And believe me {{Client Name}}..." or "All I ask is that you give me one shot..."
4.  **Justify with "Because":** Provide a final justification. "...because I am sure she deserves it. Sound fair enough?"
5.  **Be Silent:** After you ask, stop talking. The first person who speaks, loses.
</instructions>

<examples>
Customer: "Yeah, I can see how that would help."
Response: "So does this feel like this could be the answer for you?"

Customer: "Yes."
Response: "And do you see yourself using this system to finally get your time back?"

Customer: "Yeah, I do."
Response: "Great. And believe me {{Client Name}}, the only problem you're gonna have is that I didn't call you six months ago. Sound fair enough?"
</examples>

<constraints>
- Response must be 1-2 sentences.
- Your tone is the peak of confidence and sincerity.
- Your only job is to ask for the sale and then stop.
</constraints>

Return JSON with your closing response.
        """
    
    def _get_step_guidance(self, step: str) -> str:
        """Get guidance for specific closing sequence step"""
        guidance = {
            "value_summary": "Summarize the key benefits and value they'll receive. Tie back to their specific pain points and goals.",
            "fit_confirmation": "Confirm that this solution addresses their needs and is the right fit for their situation.",
            "decision_check": "Check their current thinking and any remaining questions or concerns.",
            "close_attempt": "Ask for the decision directly using your chosen closing technique.",
            "next_steps": "Outline the specific steps to move forward and begin implementation.",
            "implementation_planning": "Discuss timeline, resources, and process for getting started."
        }
        
        return guidance.get(step, "Move the conversation toward commitment and next steps.")
    
    def _enhance_closing_response(self, response: Dict[str, Any], context: AgentContext, technique: str, step: str) -> Dict[str, Any]:
        """Enhance response with closing-specific improvements"""
        suggestion = response.get("suggestion", "")
        
        # Determine closing type based on content
        if "?" in suggestion and any(word in suggestion.lower() for word in ["ready", "move forward", "get started"]):
            response["type"] = "trial_close"
        elif any(word in suggestion.lower() for word in ["summary", "recap", "benefits", "value"]):
            response["type"] = "summary"
        elif any(word in suggestion.lower() for word in ["next", "step", "timeline", "implementation"]):
            response["type"] = "next_steps"
        elif any(word in suggestion.lower() for word in ["when", "how", "start"]):
            response["type"] = "implementation"
        else:
            response["type"] = "ask"
        
        # Add closing context
        response["context"] = response.get("context", {})
        response["context"]["technique"] = technique
        response["context"]["step"] = step
        response["context"]["urgency"] = self._determine_urgency_tone(suggestion)
        response["context"]["close_strength"] = self._determine_close_strength(suggestion)
        
        # Add closing-specific next actions
        response["next_actions"] = response.get("next_actions", [])
        response["next_actions"].extend(self._get_closing_next_actions(step, technique))
        
        # Ensure alternatives are closing-focused
        if not response.get("alternatives"):
            response["alternatives"] = self._get_closing_alternatives(technique, step)
        
        return response
    
    def _assess_buying_signals(self, recent_text: str, customer_messages: List) -> int:
        """Assess strength of buying signals (0-5 scale)"""
        strong_signals = ["yes", "interested", "sounds good", "let's do it", "move forward"]
        medium_signals = ["how", "when", "timeline", "process", "next step"]
        weak_signals = ["maybe", "possibly", "considering", "thinking"]
        
        score = 0
        score += sum(2 for signal in strong_signals if signal in recent_text)
        score += sum(1 for signal in medium_signals if signal in recent_text)
        score -= sum(1 for signal in weak_signals if signal in recent_text)
        
        # Question frequency indicates interest
        question_count = sum(1 for msg in customer_messages[-3:] if "?" in msg.text)
        score += min(question_count, 2)
        
        return max(0, min(5, score))
    
    def _assess_objection_resolution(self, context: AgentContext, recent_text: str) -> bool:
        """Check if major objections have been resolved"""
        objection_indicators = ["but", "however", "concern", "worry", "issue", "problem"]
        recent_objections = sum(1 for indicator in objection_indicators if indicator in recent_text)
        
        # Check conversation history for objection handling
        conversation_text = " ".join([msg.text.lower() for msg in context.conversation_history])
        resolution_indicators = ["understand", "makes sense", "see", "good point", "fair enough"]
        resolutions = sum(1 for indicator in resolution_indicators if indicator in conversation_text)
        
        return recent_objections <= 1 and resolutions >= 2
    
    def _assess_closing_engagement(self, customer_messages: List) -> str:
        """Assess customer engagement level for closing"""
        if not customer_messages:
            return "low"
        
        recent_messages = customer_messages[-3:]
        avg_length = sum(len(msg.text) for msg in recent_messages) / len(recent_messages)
        question_count = sum(1 for msg in recent_messages if "?" in msg.text)
        
        if avg_length > 40 and question_count >= 2:
            return "high"
        elif avg_length > 20 and question_count >= 1:
            return "medium"
        else:
            return "low"
    
    def _assess_decision_authority(self, context: AgentContext, recent_text: str) -> str:
        """Assess customer's decision-making authority"""
        if context.customer_profile.decision_authority:
            if "final" in context.customer_profile.decision_authority.lower():
                return "high"
            elif "involved" in context.customer_profile.decision_authority.lower():
                return "medium"
        
        authority_indicators = ["decide", "my decision", "i can", "my call"]
        team_indicators = ["team", "boss", "manager", "approval", "committee"]
        
        if any(indicator in recent_text for indicator in authority_indicators):
            return "high"
        elif any(indicator in recent_text for indicator in team_indicators):
            return "low"
        
        return "unknown"
    
    def _assess_urgency_signals(self, recent_text: str) -> str:
        """Assess customer urgency level"""
        high_urgency = ["urgent", "asap", "immediately", "soon", "deadline", "pressure"]
        medium_urgency = ["month", "quarter", "planning", "timeline"]
        low_urgency = ["eventually", "someday", "future", "later"]
        
        if any(signal in recent_text for signal in high_urgency):
            return "high"
        elif any(signal in recent_text for signal in medium_urgency):
            return "medium"
        elif any(signal in recent_text for signal in low_urgency):
            return "low"
        
        return "unknown"
    
    def _assess_closing_risks(self, context: AgentContext, recent_text: str) -> int:
        """Assess risk factors that might prevent closing (0-5 scale)"""
        risk_score = 0
        
        # Budget concerns
        if any(word in recent_text for word in ["expensive", "cost", "budget", "cheap"]):
            risk_score += 1
        
        # Decision complexity
        if any(word in recent_text for word in ["team", "committee", "approval", "boss"]):
            risk_score += 1
        
        # Competitive situation
        if any(word in recent_text for word in ["comparing", "other", "competitor", "alternative"]):
            risk_score += 1
        
        # Timing issues
        if any(word in recent_text for word in ["later", "not now", "timing", "busy"]):
            risk_score += 1
        
        # Uncertainty signals
        if any(word in recent_text for word in ["not sure", "uncertain", "maybe", "think about"]):
            risk_score += 1
        
        return risk_score
    
    def _calculate_readiness_score(self, buying_signals: int, objections_resolved: bool, 
                                  engagement: str, authority: str, urgency: str, risks: int) -> float:
        """Calculate overall closing readiness score (0-1 scale)"""
        score = 0.0
        
        # Buying signals (0-0.3)
        score += min(0.3, buying_signals * 0.06)
        
        # Objections resolved (0-0.2)
        if objections_resolved:
            score += 0.2
        
        # Engagement level (0-0.2)
        engagement_scores = {"high": 0.2, "medium": 0.1, "low": 0.0}
        score += engagement_scores.get(engagement, 0.0)
        
        # Decision authority (0-0.15)
        authority_scores = {"high": 0.15, "medium": 0.1, "low": 0.05, "unknown": 0.0}
        score += authority_scores.get(authority, 0.0)
        
        # Urgency (0-0.15)
        urgency_scores = {"high": 0.15, "medium": 0.1, "low": 0.0, "unknown": 0.05}
        score += urgency_scores.get(urgency, 0.0)
        
        # Risk factors (subtract up to -0.25)
        score -= min(0.25, risks * 0.05)
        
        return max(0.0, min(1.0, score))
    
    def _get_closing_recommendation(self, readiness_score: float) -> str:
        """Get closing recommendation based on readiness score"""
        if readiness_score >= 0.8:
            return "strong_close"
        elif readiness_score >= 0.6:
            return "trial_close"
        elif readiness_score >= 0.4:
            return "soft_close"
        else:
            return "more_discovery"
    
    def _determine_urgency_tone(self, suggestion: str) -> str:
        """Determine urgency level of the suggestion"""
        high_urgency_words = ["today", "now", "immediately", "limited", "deadline"]
        medium_urgency_words = ["soon", "this week", "this month", "quickly"]
        
        suggestion_lower = suggestion.lower()
        
        if any(word in suggestion_lower for word in high_urgency_words):
            return "high"
        elif any(word in suggestion_lower for word in medium_urgency_words):
            return "medium"
        else:
            return "low"
    
    def _determine_close_strength(self, suggestion: str) -> str:
        """Determine how strong/direct the closing attempt is"""
        strong_close_words = ["decision", "commit", "sign", "agree", "purchase"]
        medium_close_words = ["ready", "move forward", "get started", "next step"]
        soft_close_words = ["thoughts", "questions", "concerns", "make sense"]
        
        suggestion_lower = suggestion.lower()
        
        if any(word in suggestion_lower for word in strong_close_words):
            return "strong"
        elif any(word in suggestion_lower for word in medium_close_words):
            return "medium"
        elif any(word in suggestion_lower for word in soft_close_words):
            return "soft"
        else:
            return "medium"
    
    def _get_closing_next_actions(self, step: str, technique: str) -> List[str]:
        """Get next actions based on closing step and technique"""
        next_actions = {
            "value_summary": ["Confirm understanding", "Check agreement", "Address questions"],
            "fit_confirmation": ["Get explicit confirmation", "Handle any concerns", "Move to decision"],
            "decision_check": ["Listen for concerns", "Address objections", "Gauge readiness"],
            "close_attempt": ["Wait for response", "Handle objections", "Confirm commitment"],
            "next_steps": ["Get calendar out", "Discuss timeline", "Assign responsibilities"],
            "implementation_planning": ["Set milestones", "Plan kickoff", "Exchange contacts"]
        }
        
        return next_actions.get(step, ["Continue toward commitment"])
    
    def _get_closing_alternatives(self, technique: str, step: str) -> List[str]:
        """Get alternative closing approaches"""
        alternatives = {
            "assumptive": [
                "When would you like to get started with implementation?",
                "What's the best timeline for rolling this out?",
                "Should we schedule the kickoff for next week?"
            ],
            "summary": [
                "Does this solution address your main concerns?",
                "Are you comfortable that this is the right fit?",
                "Do you see how this solves your key challenges?"
            ],
            "question": [
                "What questions do you have before we move forward?",
                "What would you need to feel confident about this decision?",
                "Is there anything holding you back from moving ahead?"
            ],
            "trial": [
                "How about we start with a pilot program?",
                "Would a trial period help you feel more comfortable?",
                "What if we could minimize the risk with a phased approach?"
            ]
        }
        
        return alternatives.get(technique, [
            "Are you ready to move forward with this?",
            "What do you think about taking the next step?",
            "How does this sound to you?"
        ])
    
    def _format_customer_summary(self, profile) -> str:
        """Format customer summary for closing prompt"""
        summary_parts = []
        
        if profile.pain_points:
            summary_parts.append(f"Key Pain Points: {', '.join(profile.pain_points[:3])}")
        
        if profile.interests:
            summary_parts.append(f"Main Interests: {', '.join(profile.interests[:3])}")
        
        if profile.budget_range:
            summary_parts.append(f"Budget: {profile.budget_range}")
        
        if profile.timeline:
            summary_parts.append(f"Timeline: {profile.timeline}")
        
        if profile.decision_authority:
            summary_parts.append(f"Decision Role: {profile.decision_authority}")
        
        return "\n".join(summary_parts) if summary_parts else "Limited customer information"
    
    def _get_fallback_closing_response(self) -> Dict[str, Any]:
        """Get fallback response when AI generation fails"""
        return {
            "suggestion": "Based on everything we've discussed, I believe this solution is a great fit for your needs. Are you ready to move forward?",
            "type": "trial_close",
            "confidence": 0.6,
            "reasoning": "Direct but professional closing attempt that summarizes value and asks for decision",
            "alternatives": [
                "Does this solution address your main concerns?",
                "What questions do you have before we take the next step?"
            ],
            "next_actions": [
                "Wait for customer response",
                "Address any final concerns",
                "Discuss next steps and timeline"
            ],
            "context": {
                "technique": "summary",
                "step": "close_attempt",
                "urgency": "medium",
                "close_strength": "medium"
            }
        } 