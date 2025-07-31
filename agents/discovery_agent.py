from typing import Dict, Any, List
from models.schemas import AgentContext, CustomerProfile
from services.gemini_api import GeminiAPIService
from utils.logging import LoggerMixin


class DiscoveryAgent(LoggerMixin):
    """Specialized agent for discovery, needs assessment, and qualification"""
    
    def __init__(self, gemini_api_service: GeminiAPIService):
        self.gemini_api_service = gemini_api_service
        self.agent_type = "discovery"
        
        # Discovery framework questions
        self.discovery_areas = {
            "current_situation": [
                "How are you currently handling [specific area]?",
                "What's your current process for [relevant process]?",
                "Tell me about your existing setup.",
                "What tools are you using today?"
            ],
            "pain_points": [
                "What's the biggest challenge you're facing with [area]?",
                "What keeps you up at night about [business area]?",
                "What would you change about your current situation?",
                "Where do you see the most friction in your process?"
            ],
            "impact": [
                "How is this affecting your business?",
                "What's the cost of not solving this?",
                "How much time does this take up?",
                "What impact does this have on your team?"
            ],
            "desired_outcome": [
                "What would an ideal solution look like?",
                "If you could wave a magic wand, what would change?",
                "What are your goals for [timeframe]?",
                "What does success look like to you?"
            ],
            "decision_process": [
                "Who else is involved in this decision?",
                "What's your typical evaluation process?",
                "How do you usually make decisions like this?",
                "What criteria are most important to you?"
            ],
            "budget_timeline": [
                "What's your timeline for making a decision?",
                "When would you like to have this implemented?",
                "What budget range are you working with?",
                "How urgent is solving this problem?"
            ]
        }
    
    async def generate_suggestion(self, context: AgentContext) -> Dict[str, Any]:
        """Generate discovery stage suggestions"""
        try:
            # Analyze what's been discovered so far
            discovery_analysis = self._analyze_discovery_progress(context)
            
            # Determine next discovery area to focus on
            next_area = self._determine_next_discovery_area(discovery_analysis, context)
            
            # Build custom prompt
            custom_prompt = self._build_discovery_prompt(context, next_area, discovery_analysis)
            
            # Generate suggestion using Gemini API
            response = await self.gemini_api_service.generate_suggestion(
                context=context,
                agent_type=self.agent_type,
                conversation_history=context.recent_messages,
                custom_prompt=custom_prompt
            )
            
            # Enhance response with discovery-specific logic
            enhanced_response = self._enhance_discovery_response(response, context, next_area)
            
            self.log_info(
                "Generated discovery suggestion",
                session_id=context.session_metadata.get("session_id"),
                discovery_area=next_area,
                suggestion_type=enhanced_response.get("type", "unknown")
            )
            
            return enhanced_response
            
        except Exception as e:
            self.log_error("Error generating discovery suggestion", error=str(e))
            return self._get_fallback_discovery_response()
    
    def _analyze_discovery_progress(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze what has been discovered so far"""
        profile = context.customer_profile
        conversation = context.conversation_history
        
        analysis = {
            "current_situation": "unknown",
            "pain_points": len(profile.pain_points),
            "impact": "unknown",
            "desired_outcome": "unknown",
            "decision_process": "partial" if profile.decision_authority else "unknown",
            "budget_timeline": "partial" if profile.budget_range or profile.timeline else "unknown",
            "gaps": []
        }
        
        # Analyze conversation for discovery indicators
        all_text = " ".join([msg.text.lower() for msg in conversation])
        
        # Check current situation understanding
        situation_indicators = ["currently", "today", "now", "existing", "using"]
        if any(indicator in all_text for indicator in situation_indicators):
            analysis["current_situation"] = "discovered"
        else:
            analysis["gaps"].append("current_situation")
        
        # Check impact understanding
        impact_indicators = ["cost", "time", "impact", "affect", "problem"]
        if any(indicator in all_text for indicator in impact_indicators):
            analysis["impact"] = "discovered"
        else:
            analysis["gaps"].append("impact")
        
        # Check desired outcome
        outcome_indicators = ["want", "need", "goal", "ideal", "looking for"]
        if any(indicator in all_text for indicator in outcome_indicators):
            analysis["desired_outcome"] = "discovered"
        else:
            analysis["gaps"].append("desired_outcome")
        
        # Check decision process
        decision_indicators = ["team", "boss", "approve", "decision", "evaluate"]
        if any(indicator in all_text for indicator in decision_indicators):
            analysis["decision_process"] = "discovered"
        elif not profile.decision_authority:
            analysis["gaps"].append("decision_process")
        
        # Check budget and timeline
        budget_indicators = ["budget", "cost", "price", "investment"]
        timeline_indicators = ["when", "timeline", "soon", "urgent", "month", "quarter"]
        
        if any(indicator in all_text for indicator in budget_indicators):
            analysis["budget_timeline"] = "budget_discovered"
        elif any(indicator in all_text for indicator in timeline_indicators):
            analysis["budget_timeline"] = "timeline_discovered"
        elif not profile.budget_range and not profile.timeline:
            analysis["gaps"].append("budget_timeline")
        
        return analysis
    
    def _determine_next_discovery_area(self, analysis: Dict[str, Any], context: AgentContext) -> str:
        """Determine which discovery area to focus on next"""
        # Priority order for discovery
        priority_order = [
            "pain_points",
            "current_situation", 
            "impact",
            "desired_outcome",
            "decision_process",
            "budget_timeline"
        ]
        
        # Find the highest priority gap
        for area in priority_order:
            if area in analysis.get("gaps", []):
                return area
            
            # Special handling for pain points
            if area == "pain_points" and analysis["pain_points"] < 2:
                return area
        
        # If no major gaps, focus on deepening understanding
        customer_messages = [msg for msg in context.recent_messages if msg.speaker == "customer"]
        if customer_messages:
            last_message = customer_messages[-1].text.lower()
            
            # Follow up based on last customer message
            if any(word in last_message for word in ["problem", "issue", "challenge"]):
                return "pain_points"
            elif any(word in last_message for word in ["process", "currently", "today"]):
                return "current_situation"
            elif any(word in last_message for word in ["cost", "time", "impact"]):
                return "impact"
            elif any(word in last_message for word in ["want", "need", "goal"]):
                return "desired_outcome"
        
        return "pain_points"  # Default fallback
    
    def _build_discovery_prompt(self, context: AgentContext, focus_area: str, discovery_analysis: dict) -> str:
        """Build discovery agent prompt for uncovering customer pain points"""
        customer_data = context.customer_profile.dict()
        recent_history = []
        for msg in context.recent_messages[-5:]:
            speaker = "SELLER" if msg.speaker == "seller" else "CUSTOMER"
            recent_history.append(f"{speaker}: {msg.text}")
        
        recent_history_text = "\n".join(recent_history) if recent_history else "No recent history"
        customer_message = context.recent_messages[-1].text if context.recent_messages else ""
        
        return f"""
<role>You are the Discovery Agent. Your goal is to listen more than you talk. You must uncover the customer's challenges, their consequences, and amplify their pain indirectly by asking insightful questions. You are an empathetic expert seeking to understand.</role>

<context>
- Current Stage: Discovery
- Customer Profile: {customer_data}
- Last Customer Input: "{customer_message}"
- Conversation History: {recent_history_text}
- Focus Area: {focus_area}
- Previous Discovery: {discovery_analysis}
</context>

<instructions>
1.  **Ask Permission:** Before digging deep, get permission. "Can I ask you a question?"
2.  **Uncover Pain:** Ask targeted, single-part questions about their clinic, workload, patient management, and current marketing. Focus on questions that, by their nature, reveal a challenge.
3.  **Amplify Pain:** Once a challenge is identified, explore its consequences. Use questions from "Amplifying Pain to Sell" to make them feel the weight of the situation.
4.  **Use Empathetic Tone:** Ask questions in a casual, "no big deal" tone, especially about sensitive topics. Match their emotional state. If they express frustration, validate it ("I hear you...").
5.  **Use "Feel":** Frame questions with "How do you feel about..." to keep them in an emotional state.
</instructions>

<examples>
Customer: "Yeah, we're doing okay, I guess."
Response: "It sounds like things are going a hundred percent perfect for you then. What would you change if you could?"

Customer: "We miss a few calls when we get busy."
Response: "And what's the knock-on effect of that in your clinic? How does that impact your staff's day?"

Customer: "Our marketing is handled by my receptionist."
Response: "I see. And out of curiosity, are you 100% happy with where you are at with new patient acquisition right now?"
</examples>

<constraints>
- Response must be 1-2 sentences.
- Never ask a two-part question.
- Your goal is to make the customer state their own pain out loud.
</constraints>

Return JSON with your discovery question.
        """
    
    def _format_customer_profile(self, profile: CustomerProfile) -> str:
        """Format customer profile for prompt"""
        info_parts = []
        
        if profile.name:
            info_parts.append(f"Name: {profile.name}")
        if profile.company:
            info_parts.append(f"Company: {profile.company}")
        if profile.role:
            info_parts.append(f"Role: {profile.role}")
        if profile.pain_points:
            info_parts.append(f"Pain Points: {', '.join(profile.pain_points)}")
        if profile.interests:
            info_parts.append(f"Interests: {', '.join(profile.interests)}")
        if profile.budget_range:
            info_parts.append(f"Budget: {profile.budget_range}")
        if profile.timeline:
            info_parts.append(f"Timeline: {profile.timeline}")
        if profile.decision_authority:
            info_parts.append(f"Decision Authority: {profile.decision_authority}")
        
        return "\n".join(info_parts) if info_parts else "Limited information available"
    
    def _get_area_questions(self, area: str) -> str:
        """Get sample questions for a discovery area"""
        questions = self.discovery_areas.get(area, [])
        return "\n".join(f"- {q}" for q in questions[:3])
    
    def _enhance_discovery_response(self, response: Dict[str, Any], context: AgentContext, focus_area: str) -> Dict[str, Any]:
        """Enhance response with discovery-specific improvements"""
        suggestion = response.get("suggestion", "")
        
        # Determine question type
        if "?" in suggestion:
            if suggestion.lower().startswith(("what", "how", "why", "tell me", "describe")):
                response["type"] = "open_question"
            else:
                response["type"] = "clarification"
        else:
            response["type"] = "statement"
        
        # Add discovery context
        response["context"] = response.get("context", {})
        response["context"]["discovery_area"] = focus_area
        response["context"]["qualification_stage"] = self._assess_qualification_stage(context)
        
        # Determine question depth
        pain_point_count = len(context.customer_profile.pain_points)
        if pain_point_count == 0:
            response["context"]["question_depth"] = "surface"
        elif pain_point_count < 3:
            response["context"]["question_depth"] = "medium"
        else:
            response["context"]["question_depth"] = "deep"
        
        # Add listening points
        response["next_actions"] = response.get("next_actions", [])
        response["next_actions"].extend(self._get_listening_points(focus_area))
        
        # Ensure alternatives are discovery-focused
        if not response.get("alternatives"):
            response["alternatives"] = self._get_discovery_alternatives(focus_area)
        
        return response
    
    def _assess_qualification_stage(self, context: AgentContext) -> str:
        """Assess how well qualified the prospect is"""
        profile = context.customer_profile
        
        qualification_score = 0
        
        # Pain points identified
        if len(profile.pain_points) >= 2:
            qualification_score += 2
        elif len(profile.pain_points) >= 1:
            qualification_score += 1
        
        # Budget indicated
        if profile.budget_range:
            qualification_score += 1
        
        # Timeline indicated
        if profile.timeline:
            qualification_score += 1
        
        # Decision authority
        if profile.decision_authority:
            qualification_score += 1
        
        if qualification_score >= 4:
            return "highly_qualified"
        elif qualification_score >= 2:
            return "moderately_qualified"
        else:
            return "early_qualification"
    
    def _get_listening_points(self, focus_area: str) -> List[str]:
        """Get what to listen for based on focus area"""
        listening_points = {
            "current_situation": ["Current tools and processes", "Team structure", "Workflow details"],
            "pain_points": ["Emotional language", "Frustration indicators", "Specific problems"],
            "impact": ["Cost implications", "Time lost", "Business consequences"],
            "desired_outcome": ["Success criteria", "Goals and objectives", "Vision statements"],
            "decision_process": ["Stakeholder names", "Approval process", "Evaluation criteria"],
            "budget_timeline": ["Urgency indicators", "Budget hints", "Timeline pressure"]
        }
        
        return listening_points.get(focus_area, ["Key details", "Emotional responses", "Follow-up opportunities"])
    
    def _get_discovery_alternatives(self, focus_area: str) -> List[str]:
        """Get alternative questions for the focus area"""
        alternatives = {
            "current_situation": [
                "Walk me through your current process.",
                "How are you handling this today?",
                "What does your typical workflow look like?"
            ],
            "pain_points": [
                "What's the biggest challenge with your current approach?",
                "Where do you see the most friction?",
                "What keeps you up at night about this?"
            ],
            "impact": [
                "How is this affecting your business?",
                "What's the cost of the status quo?",
                "How much time does this consume?"
            ],
            "desired_outcome": [
                "What would success look like?",
                "If you could solve this perfectly, what would that mean?",
                "What are you hoping to achieve?"
            ],
            "decision_process": [
                "Who else would be involved in evaluating a solution?",
                "How do you typically make decisions like this?",
                "What factors are most important in your evaluation?"
            ],
            "budget_timeline": [
                "What's driving the timing on this?",
                "When would you like to have this resolved?",
                "What kind of investment makes sense for solving this?"
            ]
        }
        
        return alternatives.get(focus_area, [
            "Help me understand that better.",
            "Can you give me more details on that?",
            "What else should I know about this?"
        ])
    
    def _get_fallback_discovery_response(self) -> Dict[str, Any]:
        """Get fallback response when AI generation fails"""
        return {
            "suggestion": "Help me understand your current situation better. What's the biggest challenge you're facing right now?",
            "type": "open_question",
            "confidence": 0.6,
            "reasoning": "Open-ended question to uncover pain points and current state",
            "alternatives": [
                "Tell me more about how you're handling this today.",
                "What's working well with your current approach, and what isn't?"
            ],
            "next_actions": [
                "Listen for pain points and challenges",
                "Identify emotional language",
                "Ask follow-up questions for clarity"
            ],
            "context": {
                "discovery_area": "pain_points",
                "question_depth": "surface",
                "qualification_stage": "early_qualification"
            }
        }
    
    def should_transition_to_pitch(self, context: AgentContext) -> bool:
        """Determine if ready to transition to pitch stage"""
        try:
            profile = context.customer_profile
            
            # Minimum qualification criteria
            criteria_met = 0
            
            # Must have at least 2 pain points
            if len(profile.pain_points) >= 2:
                criteria_met += 1
            
            # Should have some budget/timeline indication
            if profile.budget_range or profile.timeline:
                criteria_met += 1
            
            # Should understand current situation
            conversation_text = " ".join([msg.text.lower() for msg in context.conversation_history])
            if any(word in conversation_text for word in ["currently", "today", "process", "using"]):
                criteria_met += 1
            
            # Customer should be engaged (asking questions or sharing details)
            customer_messages = [msg for msg in context.conversation_history if msg.speaker == "customer"]
            if len(customer_messages) >= 3 and any(len(msg.text) > 30 for msg in customer_messages[-3:]):
                criteria_met += 1
            
            return criteria_met >= 3
            
        except Exception as e:
            self.log_error("Error determining pitch transition readiness", error=str(e))
            return False 