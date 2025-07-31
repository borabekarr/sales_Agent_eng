from typing import Dict, Any, List
from models.schemas import AgentContext, CustomerProfile
from services.gemini_api import GeminiAPIService
from utils.logging import LoggerMixin


class PitchAgent(LoggerMixin):
    """Specialized agent for presenting solutions and value propositions"""
    
    def __init__(self, gemini_api_service: GeminiAPIService):
        self.gemini_api_service = gemini_api_service
        self.agent_type = "pitch"
        
        # Value proposition framework
        self.value_frameworks = {
            "pain_relief": {
                "structure": "Problem → Solution → Benefit",
                "approach": "Address specific pain points with targeted solutions"
            },
            "gain_creation": {
                "structure": "Current State → Improved State → Value Created",
                "approach": "Show how solution creates new opportunities"
            },
            "roi_focused": {
                "structure": "Investment → Returns → Timeline",
                "approach": "Focus on financial benefits and ROI"
            },
            "competitive_advantage": {
                "structure": "Challenge → Our Advantage → Customer Win",
                "approach": "Position against alternatives and status quo"
            }
        }
        
        # Pitch components
        self.pitch_elements = {
            "problem_confirmation": "Confirm understanding of their specific challenge",
            "solution_overview": "High-level solution explanation",
            "feature_benefit": "Specific features tied to their needs",
            "proof_points": "Evidence, case studies, testimonials",
            "roi_demonstration": "Financial impact and returns",
            "risk_mitigation": "Address concerns about implementation",
            "next_steps": "Clear path forward"
        }
    
    async def generate_suggestion(self, context: AgentContext) -> Dict[str, Any]:
        """Generate pitch stage suggestions"""
        try:
            # Analyze customer needs and pain points
            pitch_analysis = self._analyze_pitch_opportunity(context)
            
            # Determine best value framework
            value_framework = self._select_value_framework(context, pitch_analysis)
            
            # Identify next pitch element to focus on
            next_element = self._determine_next_pitch_element(context, pitch_analysis)
            
            # Build custom prompt
            custom_prompt = self._build_pitch_prompt(context, value_framework, next_element, pitch_analysis)
            
            # Generate suggestion using Gemini API
            response = await self.gemini_api_service.generate_suggestion(
                context=context,
                agent_type=self.agent_type,
                conversation_history=context.recent_messages,
                custom_prompt=custom_prompt
            )
            
            # Enhance response with pitch-specific logic
            enhanced_response = self._enhance_pitch_response(response, context, value_framework, next_element)
            
            self.log_info(
                "Generated pitch suggestion",
                session_id=context.session_metadata.get("session_id"),
                value_framework=value_framework,
                pitch_element=next_element
            )
            
            return enhanced_response
            
        except Exception as e:
            self.log_error("Error generating pitch suggestion", error=str(e))
            return self._get_fallback_pitch_response()
    
    def _analyze_pitch_opportunity(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze the pitch opportunity based on discovered needs"""
        profile = context.customer_profile
        conversation = context.conversation_history
        
        analysis = {
            "primary_pain_points": profile.pain_points[:3],  # Top 3 pain points
            "interests": profile.interests,
            "urgency_level": self._assess_urgency(profile, conversation),
            "budget_signals": self._assess_budget_signals(profile, conversation),
            "decision_complexity": self._assess_decision_complexity(profile, conversation),
            "competitive_situation": self._assess_competitive_situation(conversation),
            "customer_sophistication": self._assess_customer_sophistication(conversation),
            "engagement_level": self._assess_engagement_level(conversation),
            "objection_likelihood": self._predict_objection_likelihood(profile, conversation)
        }
        
        return analysis
    
    def _select_value_framework(self, context: AgentContext, analysis: Dict[str, Any]) -> str:
        """Select the most appropriate value framework"""
        # High urgency + clear pain = pain relief framework
        if (analysis["urgency_level"] == "high" and 
            len(analysis["primary_pain_points"]) >= 2):
            return "pain_relief"
        
        # Budget signals + sophisticated customer = ROI focused
        if (analysis["budget_signals"] == "positive" and 
            analysis["customer_sophistication"] == "high"):
            return "roi_focused"
        
        # Multiple interests + growth focused = gain creation
        if (len(analysis["interests"]) >= 2 and 
            any("grow" in interest.lower() or "improve" in interest.lower() 
                for interest in analysis["interests"])):
            return "gain_creation"
        
        # Complex decision + competitive situation = competitive advantage
        if (analysis["decision_complexity"] == "high" or 
            analysis["competitive_situation"] == "competitive"):
            return "competitive_advantage"
        
        # Default to pain relief
        return "pain_relief"
    
    def _determine_next_pitch_element(self, context: AgentContext, analysis: Dict[str, Any]) -> str:
        """Determine which pitch element to focus on next"""
        conversation_text = " ".join([msg.text.lower() for msg in context.conversation_history])
        
        # Check what's been covered
        covered_elements = set()
        
        if any(word in conversation_text for word in ["understand", "problem", "challenge"]):
            covered_elements.add("problem_confirmation")
        
        if any(word in conversation_text for word in ["solution", "approach", "system"]):
            covered_elements.add("solution_overview")
        
        if any(word in conversation_text for word in ["feature", "capability", "function"]):
            covered_elements.add("feature_benefit")
        
        if any(word in conversation_text for word in ["case", "example", "client", "customer"]):
            covered_elements.add("proof_points")
        
        if any(word in conversation_text for word in ["save", "roi", "return", "investment"]):
            covered_elements.add("roi_demonstration")
        
        # Determine next element based on priority and what's covered
        priority_order = [
            "problem_confirmation",
            "solution_overview", 
            "feature_benefit",
            "proof_points",
            "roi_demonstration",
            "risk_mitigation",
            "next_steps"
        ]
        
        for element in priority_order:
            if element not in covered_elements:
                return element
        
        # If everything covered, focus on reinforcement
        if analysis["engagement_level"] == "high":
            return "next_steps"
        else:
            return "roi_demonstration"  # Reinforce value
    
    def _build_pitch_prompt(self, context: AgentContext, value_framework: dict, next_element: str, pitch_analysis: dict) -> str:
        """Build pitch agent prompt for presenting the solution"""
        customer_data = context.customer_profile.dict()
        recent_history = []
        for msg in context.recent_messages[-5:]:
            speaker = "SELLER" if msg.speaker == "seller" else "CUSTOMER"
            recent_history.append(f"{speaker}: {msg.text}")
        
        recent_history_text = "\n".join(recent_history) if recent_history else "No recent history"
        customer_message = context.recent_messages[-1].text if context.recent_messages else ""
        discovered_pains = context.context_stack[-3:] if context.context_stack else []
        
        return f"""
<role>You are the Pitch Agent. Your goal is to present the logical and emotional case for the solution in a clear, confident, and compelling way. You are the authority figure who has the key to their desired future.</role>

<context>
- Current Stage: Pitch
- Customer Profile: {customer_data}
- Customer Pains: {discovered_pains}
- Last Customer Input: "{customer_message}"
- Conversation History: {recent_history_text}
- Value Framework: {value_framework}
- Next Element: {next_element}
- Pitch Analysis: {pitch_analysis}
</context>

<instructions>
1.  **Connect to Their Pain:** Start by connecting the solution directly to the challenges you just uncovered.
2.  **Present the Solution:** Use the "AI Voice Caller" or "Chatbot" pitch scripts as your foundation.
    * If they mentioned missed calls or staff being overwhelmed, use the "AI Voice Caller" pitch and the pain amplification math.
    * Otherwise, use the "Chatbot" pitch.
3.  **Limit Claims:** Make a maximum of three core positive claims to maintain credibility, as per "Do not praise your service."
4.  **Use Psychological Anchors:** Frame the solution around a core theme. (e.g., "This is about closing that black hole of missed revenue," or "This is the key to getting your time back.").
5.  **Be Certain:** Use confident and clear language. Avoid ambiguous words like "maybe" or "I think." Use trigger words like "virtually" and "only" when mentioning the price ("cash outlay").
6.  **Future Pace:** Paint a picture of the massive benefits and how they will *feel* after the system is implemented (e.g., "fully booked," "stress-free team").
</instructions>

<examples>
User: "I just feel like we're leaving money on the table with all the missed calls."
Response: "I understand. Now, that's exactly why I'm here. We have to close this black hole, and you have a big, shiny third option on your hands right now."

User: "So how does it work?"
Response: "Well, imagine if your current front-desk staff woke up differently tomorrow. She can handle all incoming calls, at the same time, without missing a single one, and she'll do it 24/7."
</examples>

<constraints>
- Response must be 1-2 sentences, leading into the next line like a slippery slide.
- Be enthusiastic as hell, sharp as a tack.
- Your pitch should feel like the inevitable, obvious solution to their stated problems.
</constraints>

Return JSON with your pitch response.
        """
    
    def _format_customer_needs(self, profile: CustomerProfile, analysis: Dict[str, Any]) -> str:
        """Format customer needs for prompt"""
        info_parts = []
        
        if analysis["primary_pain_points"]:
            info_parts.append(f"Primary Pain Points: {', '.join(analysis['primary_pain_points'])}")
        
        if profile.interests:
            info_parts.append(f"Interests/Goals: {', '.join(profile.interests)}")
        
        if profile.budget_range:
            info_parts.append(f"Budget Context: {profile.budget_range}")
        
        if profile.timeline:
            info_parts.append(f"Timeline: {profile.timeline}")
        
        if profile.decision_authority:
            info_parts.append(f"Decision Authority: {profile.decision_authority}")
        
        info_parts.append(f"Urgency: {analysis['urgency_level']}")
        info_parts.append(f"Engagement: {analysis['engagement_level']}")
        
        return "\n".join(info_parts) if info_parts else "Limited customer information available"
    
    def _enhance_pitch_response(self, response: Dict[str, Any], context: AgentContext, framework: str, element: str) -> Dict[str, Any]:
        """Enhance response with pitch-specific improvements"""
        suggestion = response.get("suggestion", "")
        
        # Determine pitch type based on content
        if any(word in suggestion.lower() for word in ["save", "roi", "return", "investment"]):
            response["type"] = "roi_demo"
        elif any(word in suggestion.lower() for word in ["feature", "capability", "helps", "enables"]):
            response["type"] = "feature_benefit"
        elif any(word in suggestion.lower() for word in ["client", "customer", "example", "case"]):
            response["type"] = "proof_point"
        elif "?" in suggestion:
            response["type"] = "trial_close"
        else:
            response["type"] = "value_proposition"
        
        # Add pitch context
        response["context"] = response.get("context", {})
        response["context"]["framework"] = framework
        response["context"]["element"] = element
        response["context"]["value_strength"] = self._assess_value_strength(context, suggestion)
        
        # Add pitch-specific next actions
        response["next_actions"] = response.get("next_actions", [])
        response["next_actions"].extend(self._get_pitch_listening_points(element))
        
        # Ensure alternatives are pitch-focused
        if not response.get("alternatives"):
            response["alternatives"] = self._get_pitch_alternatives(element, framework)
        
        # Add urgency indicators if appropriate
        if element in ["roi_demonstration", "next_steps"]:
            response["context"]["urgency_building"] = True
        
        return response
    
    def _assess_urgency(self, profile: CustomerProfile, conversation: List) -> str:
        """Assess customer urgency level"""
        urgency_indicators = {
            "high": ["urgent", "asap", "immediately", "soon", "pressure", "deadline"],
            "medium": ["this quarter", "next month", "planning", "timeline"],
            "low": ["eventually", "someday", "thinking about", "considering"]
        }
        
        all_text = " ".join([msg.text.lower() for msg in conversation])
        
        for level, indicators in urgency_indicators.items():
            if any(indicator in all_text for indicator in indicators):
                return level
        
        # Check timeline in profile
        if profile.timeline:
            if any(word in profile.timeline.lower() for word in ["urgent", "soon", "asap"]):
                return "high"
            elif any(word in profile.timeline.lower() for word in ["month", "quarter"]):
                return "medium"
        
        return "unknown"
    
    def _assess_budget_signals(self, profile: CustomerProfile, conversation: List) -> str:
        """Assess budget signals from customer"""
        positive_signals = ["budget", "investment", "spend", "allocate", "approved"]
        negative_signals = ["expensive", "cost", "cheap", "free", "tight budget"]
        
        all_text = " ".join([msg.text.lower() for msg in conversation])
        
        if any(signal in all_text for signal in positive_signals):
            return "positive"
        elif any(signal in all_text for signal in negative_signals):
            return "price_sensitive"
        elif profile.budget_range:
            return "indicated"
        
        return "unknown"
    
    def _assess_decision_complexity(self, profile: CustomerProfile, conversation: List) -> str:
        """Assess decision-making complexity"""
        complexity_indicators = ["team", "committee", "approve", "boss", "stakeholders", "board"]
        
        all_text = " ".join([msg.text.lower() for msg in conversation])
        
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in all_text)
        
        if complexity_count >= 3:
            return "high"
        elif complexity_count >= 1:
            return "medium"
        elif profile.decision_authority and "final" in profile.decision_authority.lower():
            return "low"
        
        return "unknown"
    
    def _assess_competitive_situation(self, conversation: List) -> str:
        """Assess competitive landscape"""
        competitive_indicators = ["comparing", "other", "alternative", "versus", "competitor"]
        
        all_text = " ".join([msg.text.lower() for msg in conversation])
        
        if any(indicator in all_text for indicator in competitive_indicators):
            return "competitive"
        
        return "unclear"
    
    def _assess_customer_sophistication(self, conversation: List) -> str:
        """Assess customer sophistication level"""
        sophisticated_indicators = ["roi", "metrics", "kpi", "analytics", "integration", "scalability"]
        basic_indicators = ["simple", "easy", "basic", "straightforward"]
        
        all_text = " ".join([msg.text.lower() for msg in conversation])
        
        sophisticated_count = sum(1 for indicator in sophisticated_indicators if indicator in all_text)
        basic_count = sum(1 for indicator in basic_indicators if indicator in all_text)
        
        if sophisticated_count >= 2:
            return "high"
        elif basic_count >= 2:
            return "low"
        
        return "medium"
    
    def _assess_engagement_level(self, conversation: List) -> str:
        """Assess customer engagement level"""
        customer_messages = [msg for msg in conversation if msg.speaker == "customer"]
        
        if not customer_messages:
            return "unknown"
        
        # Calculate engagement metrics
        avg_length = sum(len(msg.text) for msg in customer_messages) / len(customer_messages)
        questions_asked = sum(1 for msg in customer_messages if "?" in msg.text)
        
        if avg_length > 50 and questions_asked >= 2:
            return "high"
        elif avg_length > 25 and questions_asked >= 1:
            return "medium"
        
        return "low"
    
    def _predict_objection_likelihood(self, profile: CustomerProfile, conversation: List) -> str:
        """Predict likelihood of objections"""
        objection_indicators = ["but", "however", "concern", "worry", "issue", "problem"]
        
        all_text = " ".join([msg.text.lower() for msg in conversation if msg.speaker == "customer"])
        
        objection_count = sum(1 for indicator in objection_indicators if indicator in all_text)
        
        if objection_count >= 3:
            return "high"
        elif objection_count >= 1:
            return "medium"
        
        return "low"
    
    def _assess_value_strength(self, context: AgentContext, suggestion: str) -> str:
        """Assess the strength of the value proposition"""
        strong_indicators = ["save", "increase", "reduce", "eliminate", "improve", "roi"]
        moderate_indicators = ["help", "assist", "support", "enable"]
        
        suggestion_lower = suggestion.lower()
        
        if any(indicator in suggestion_lower for indicator in strong_indicators):
            return "high"
        elif any(indicator in suggestion_lower for indicator in moderate_indicators):
            return "medium"
        
        return "low"
    
    def _get_pitch_listening_points(self, element: str) -> List[str]:
        """Get what to listen for during pitch"""
        listening_points = {
            "problem_confirmation": ["Agreement signals", "Additional pain points", "Emotional responses"],
            "solution_overview": ["Understanding signals", "Interest indicators", "Questions about approach"],
            "feature_benefit": ["Feature interest", "Benefit comprehension", "Specific use cases"],
            "proof_points": ["Credibility acceptance", "Similarity recognition", "Reference requests"],
            "roi_demonstration": ["Financial interest", "ROI questions", "Timeline discussions"],
            "risk_mitigation": ["Concern reduction", "Confidence building", "Implementation questions"],
            "next_steps": ["Commitment signals", "Decision timeline", "Process questions"]
        }
        
        return listening_points.get(element, ["Customer engagement", "Interest level", "Questions"])
    
    def _get_pitch_alternatives(self, element: str, framework: str) -> List[str]:
        """Get alternative pitch approaches"""
        alternatives = {
            "problem_confirmation": [
                "Does this match what you're experiencing?",
                "Is this the challenge you're facing?",
                "Have I understood your situation correctly?"
            ],
            "solution_overview": [
                "Here's how we typically address this challenge.",
                "Our approach to solving this is straightforward.",
                "Let me show you how this works."
            ],
            "feature_benefit": [
                "This feature directly addresses your need for [specific need].",
                "What this means for you is [specific benefit].",
                "The impact on your business would be [specific impact]."
            ],
            "proof_points": [
                "We helped a similar company achieve [result].",
                "Here's an example of how this worked for another client.",
                "Let me share a relevant case study."
            ],
            "roi_demonstration": [
                "Based on what you've shared, here's the potential ROI.",
                "This investment typically pays for itself in [timeframe].",
                "The financial impact would be [specific numbers]."
            ]
        }
        
        return alternatives.get(element, [
            "Let me explain how this benefits you specifically.",
            "Here's what this means for your situation.",
            "The value for your business would be significant."
        ])
    
    def _get_fallback_pitch_response(self) -> Dict[str, Any]:
        """Get fallback response when AI generation fails"""
        return {
            "suggestion": "Based on what you've shared about your challenges, I believe our solution could make a significant impact. Let me show you how it directly addresses your specific needs.",
            "type": "value_proposition",
            "confidence": 0.6,
            "reasoning": "Generic value proposition that connects to customer needs",
            "alternatives": [
                "Here's how we can solve the problem you described.",
                "Let me demonstrate the value this would create for your business."
            ],
            "next_actions": [
                "Watch for engagement and interest signals",
                "Listen for questions about the solution",
                "Prepare to address potential concerns"
            ],
            "context": {
                "framework": "pain_relief",
                "element": "solution_overview",
                "value_strength": "medium"
            }
        }
    
    def should_transition_to_objection_or_closing(self, context: AgentContext) -> Dict[str, Any]:
        """Determine if ready to transition to objection handling or closing"""
        try:
            customer_messages = [msg for msg in context.recent_messages if msg.speaker == "customer"]
            
            if not customer_messages:
                return {"should_transition": False, "reason": "No customer response"}
            
            recent_text = " ".join([msg.text.lower() for msg in customer_messages[-3:]])
            
            # Check for objection signals
            objection_signals = ["but", "however", "concern", "worry", "issue", "expensive", "cost"]
            if any(signal in recent_text for signal in objection_signals):
                return {
                    "should_transition": True,
                    "next_stage": "objection",
                    "reason": "Customer expressed concerns or objections"
                }
            
            # Check for buying signals
            buying_signals = ["interested", "sounds good", "how", "when", "next steps", "move forward"]
            if any(signal in recent_text for signal in buying_signals):
                return {
                    "should_transition": True,
                    "next_stage": "closing",
                    "reason": "Customer showing buying interest"
                }
            
            # Check for engagement but no clear direction
            if len(customer_messages) >= 3:
                avg_length = sum(len(msg.text) for msg in customer_messages[-3:]) / 3
                if avg_length > 30:
                    return {
                        "should_transition": False,
                        "reason": "Customer engaged but unclear on direction",
                        "continue_pitch": True
                    }
            
            return {"should_transition": False, "reason": "Pitch in progress"}
            
        except Exception as e:
            self.log_error("Error determining pitch transition", error=str(e))
            return {"should_transition": False, "reason": "Error in analysis"} 