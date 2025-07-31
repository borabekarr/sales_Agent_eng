from typing import Dict, Any, List
from models.schemas import AgentContext
from services.gemini_api import GeminiAPIService
from utils.logging import LoggerMixin


class InterruptAgent(LoggerMixin):
    """Specialized agent for handling conversation interruptions and topic changes"""
    
    def __init__(self, gemini_api_service: GeminiAPIService):
        self.gemini_api_service = gemini_api_service
        self.agent_type = "interrupt"
        
        # Types of interruptions and how to handle them
        self.interrupt_types = {
            "question": {
                "indicators": ["?", "how", "what", "when", "where", "why", "can you"],
                "strategy": "Answer directly then redirect",
                "priority": "high"
            },
            "objection": {
                "indicators": ["but", "however", "concern", "worry", "issue", "problem"],
                "strategy": "Acknowledge, address, then continue",
                "priority": "high"
            },
            "tangent": {
                "indicators": ["by the way", "also", "speaking of", "reminds me"],
                "strategy": "Acknowledge and redirect back",
                "priority": "medium"
            },
            "clarification": {
                "indicators": ["wait", "hold on", "confused", "don't understand"],
                "strategy": "Stop and clarify immediately",
                "priority": "high"
            },
            "urgency": {
                "indicators": ["urgent", "important", "immediately", "asap", "emergency"],
                "strategy": "Address urgency then assess impact",
                "priority": "critical"
            },
            "emotional": {
                "indicators": ["frustrated", "angry", "upset", "disappointed"],
                "strategy": "Acknowledge emotion and empathize",
                "priority": "critical"
            },
            "information": {
                "indicators": ["just to let you know", "forgot to mention", "by the way"],
                "strategy": "Note information and continue",
                "priority": "low"
            },
            "positive": {
                "indicators": ["great", "excellent", "love", "perfect", "amazing"],
                "strategy": "Acknowledge positively and build momentum",
                "priority": "medium"
            }
        }
    
    async def handle_interrupt(self, context: AgentContext, interruption_text: str, speaker: str) -> Dict[str, Any]:
        """Handle conversation interruption with appropriate response"""
        try:
            # Analyze the interruption
            interrupt_analysis = self._analyze_interruption(interruption_text, speaker, context)
            
            # Generate immediate response
            immediate_response = await self._generate_immediate_response(
                context, interruption_text, interrupt_analysis
            )
            
            # Plan conversation recovery
            recovery_plan = self._plan_conversation_recovery(context, interrupt_analysis)
            
            # Update conversation context
            context_updates = self._generate_context_updates(interrupt_analysis, context)
            
            result = {
                "immediate_response": immediate_response,
                "interrupt_type": interrupt_analysis["type"],
                "priority": interrupt_analysis["priority"],
                "recovery_plan": recovery_plan,
                "context_updates": context_updates,
                "confidence": interrupt_analysis["confidence"]
            }
            
            self.log_info(
                "Handled conversation interrupt",
                session_id=context.session_metadata.get("session_id"),
                interrupt_type=interrupt_analysis["type"],
                priority=interrupt_analysis["priority"]
            )
            
            return result
            
        except Exception as e:
            self.log_error("Error handling interrupt", error=str(e))
            return self._get_fallback_interrupt_response()
    
    async def generate_suggestion(self, context: AgentContext) -> Dict[str, Any]:
        """Generate general interrupt handling suggestion"""
        try:
            # This is called when interrupt agent is selected as primary agent
            # Usually means we're in a complex interrupt situation
            
            custom_prompt = self._build_interrupt_recovery_prompt(context)
            
            response = await self.gemini_api_service.generate_suggestion(
                context=context,
                agent_type=self.agent_type,
                conversation_history=context.recent_messages,
                custom_prompt=custom_prompt
            )
            
            enhanced_response = self._enhance_interrupt_response(response, context)
            
            return enhanced_response
            
        except Exception as e:
            self.log_error("Error generating interrupt suggestion", error=str(e))
            return self._get_fallback_interrupt_response()
    
    def _analyze_interruption(self, text: str, speaker: str, context: AgentContext) -> Dict[str, Any]:
        """Analyze the interruption to determine type and appropriate response"""
        text_lower = text.lower().strip()
        
        # Determine interrupt type
        interrupt_type = "general"
        max_score = 0
        
        for int_type, int_data in self.interrupt_types.items():
            score = sum(1 for indicator in int_data["indicators"] if indicator in text_lower)
            if score > max_score:
                max_score = score
                interrupt_type = int_type
        
        # Assess urgency and priority
        priority = self.interrupt_types[interrupt_type]["priority"]
        
        # Determine confidence in classification
        confidence = min(0.9, 0.5 + (max_score * 0.1))
        
        # Assess emotional state
        emotional_state = self._assess_emotional_state(text_lower)
        
        # Determine impact on conversation flow
        flow_impact = self._assess_flow_impact(interrupt_type, text_lower, context)
        
        # Check if this relates to current conversation topic
        topic_relevance = self._assess_topic_relevance(text_lower, context)
        
        return {
            "type": interrupt_type,
            "priority": priority,
            "confidence": confidence,
            "emotional_state": emotional_state,
            "flow_impact": flow_impact,
            "topic_relevance": topic_relevance,
            "original_text": text,
            "speaker": speaker
        }
    
    async def _generate_immediate_response(self, context: AgentContext, text: str, analysis: Dict[str, Any]) -> str:
        """Generate immediate response to interruption"""
        interrupt_type = analysis["type"]
        priority = analysis["priority"]
        emotional_state = analysis["emotional_state"]
        
        # Handle critical priority interruptions immediately
        if priority == "critical":
            if interrupt_type == "urgency":
                return "I understand this is urgent. Let me address that right away."
            elif interrupt_type == "emotional":
                return f"I can hear that you're {emotional_state}. Let me make sure I understand your concern."
        
        # Handle high priority interruptions
        if priority == "high":
            if interrupt_type == "question":
                return "That's a great question. Let me answer that for you."
            elif interrupt_type == "objection":
                return "I appreciate you bringing that up. Let me address that concern."
            elif interrupt_type == "clarification":
                return "Let me clarify that for you right away."
        
        # Handle medium priority interruptions
        if priority == "medium":
            if interrupt_type == "tangent":
                return "That's interesting. Let me make a note of that and we can circle back."
            elif interrupt_type == "positive":
                return "I'm glad to hear that! That's exactly what we're aiming for."
        
        # Default responses
        return "I hear you. Let me address that."
    
    def _plan_conversation_recovery(self, context: AgentContext, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Plan how to recover conversation flow after interruption"""
        interrupt_type = analysis["type"]
        flow_impact = analysis["flow_impact"]
        current_stage = context.current_stage
        
        recovery_strategy = {
            "approach": "direct",
            "timing": "immediate",
            "transition_method": "bridge",
            "content_adjustments": []
        }
        
        # High impact interruptions need careful recovery
        if flow_impact == "high":
            if interrupt_type in ["objection", "emotional", "urgency"]:
                recovery_strategy.update({
                    "approach": "address_fully",
                    "timing": "after_resolution",
                    "transition_method": "summary_bridge",
                    "content_adjustments": ["acknowledge_interrupt", "validate_concern", "resolve_before_continuing"]
                })
            elif interrupt_type == "tangent":
                recovery_strategy.update({
                    "approach": "acknowledge_redirect",
                    "timing": "immediate",
                    "transition_method": "polite_redirect",
                    "content_adjustments": ["note_for_later", "redirect_to_main_topic"]
                })
        
        # Medium impact - quick handle and continue
        elif flow_impact == "medium":
            recovery_strategy.update({
                "approach": "quick_handle",
                "timing": "immediate",
                "transition_method": "smooth_transition",
                "content_adjustments": ["brief_acknowledgment", "continue_main_flow"]
            })
        
        # Low impact - minimal disruption
        else:
            recovery_strategy.update({
                "approach": "minimal_acknowledgment",
                "timing": "immediate",
                "transition_method": "continue_seamlessly",
                "content_adjustments": ["brief_note", "maintain_momentum"]
            })
        
        # Stage-specific considerations
        if current_stage == "closing":
            recovery_strategy["content_adjustments"].append("maintain_closing_momentum")
        elif current_stage == "discovery":
            recovery_strategy["content_adjustments"].append("incorporate_into_discovery")
        elif current_stage == "pitch":
            recovery_strategy["content_adjustments"].append("relate_to_value_prop")
        
        return recovery_strategy
    
    def _generate_context_updates(self, analysis: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Generate updates to conversation context based on interruption"""
        updates = {
            "interrupt_logged": True,
            "interrupt_type": analysis["type"],
            "customer_state": analysis["emotional_state"],
            "flow_adjustments": []
        }
        
        # Update customer profile if interruption reveals new information
        if analysis["type"] == "objection":
            updates["new_concerns"] = [analysis["original_text"][:100]]
        elif analysis["type"] == "question":
            updates["information_gaps"] = [analysis["original_text"][:100]]
        elif analysis["type"] == "positive":
            updates["positive_indicators"] = [analysis["original_text"][:100]]
        
        # Flow adjustments based on interrupt type
        if analysis["priority"] == "critical":
            updates["flow_adjustments"].append("pause_main_conversation")
        elif analysis["topic_relevance"] == "low":
            updates["flow_adjustments"].append("note_for_later_discussion")
        
        return updates
    
    def _assess_emotional_state(self, text: str) -> str:
        """Assess customer's emotional state from interruption"""
        emotional_indicators = {
            "frustrated": ["frustrated", "annoying", "difficult", "hate"],
            "excited": ["excited", "great", "love", "amazing", "fantastic"],
            "concerned": ["worried", "concerned", "nervous", "unsure"],
            "confused": ["confused", "don't understand", "unclear", "lost"],
            "impatient": ["hurry", "quickly", "fast", "urgent", "time"],
            "skeptical": ["really", "sure", "doubt", "believe"],
            "neutral": []
        }
        
        for emotion, indicators in emotional_indicators.items():
            if any(indicator in text for indicator in indicators):
                return emotion
        
        return "neutral"
    
    def _assess_flow_impact(self, interrupt_type: str, text: str, context: AgentContext) -> str:
        """Assess how much the interruption impacts conversation flow"""
        # Critical interruptions always have high impact
        if interrupt_type in ["urgency", "emotional"]:
            return "high"
        
        # Objections and clarifications usually have high impact
        if interrupt_type in ["objection", "clarification"]:
            return "high"
        
        # Questions depend on complexity
        if interrupt_type == "question":
            if len(text) > 50 or "?" in text:
                return "medium"
            else:
                return "low"
        
        # Tangents and information usually have medium impact
        if interrupt_type in ["tangent", "information"]:
            return "medium"
        
        # Positive interruptions usually have low impact
        if interrupt_type == "positive":
            return "low"
        
        return "medium"  # Default
    
    def _assess_topic_relevance(self, text: str, context: AgentContext) -> str:
        """Assess how relevant the interruption is to current conversation"""
        current_stage = context.current_stage
        
        # Get stage-relevant keywords
        stage_keywords = {
            "opening": ["name", "company", "role", "background"],
            "discovery": ["problem", "challenge", "need", "current", "process"],
            "pitch": ["solution", "feature", "benefit", "value", "capability"],
            "objection": ["concern", "worry", "but", "however", "issue"],
            "closing": ["decision", "timeline", "next step", "start", "implement"]
        }
        
        relevant_keywords = stage_keywords.get(current_stage, [])
        relevance_score = sum(1 for keyword in relevant_keywords if keyword in text)
        
        if relevance_score >= 2:
            return "high"
        elif relevance_score >= 1:
            return "medium"
        else:
            return "low"
    
    def _build_interrupt_recovery_prompt(self, context: AgentContext) -> str:
        """Build interrupt handling prompt for managing conversation disruptions"""
        customer_data = context.customer_profile.dict()
        recent_history = []
        for msg in context.recent_messages[-5:]:
            speaker = "SELLER" if msg.speaker == "seller" else "CUSTOMER"
            recent_history.append(f"{speaker}: {msg.text}")
        
        recent_history_text = "\n".join(recent_history) if recent_history else "No recent history"
        customer_message = context.recent_messages[-1].text if context.recent_messages else ""
        
        return f"""
<role>You are the Interrupt Handler Agent. You are quick, sharp, and exist to handle unexpected customer questions or statements without derailing the conversation. Your goal is to answer concisely and return the flow to the Main Controller.</role>

<context>
- Current Stage: Interrupted
- Customer Profile: {customer_data}
- The Interruption: "{customer_message}"
- Conversation History: {recent_history_text}
</context>

<instructions>
1.  **Acknowledge and Validate:** Quickly acknowledge their question or point.
2.  **Provide a Concise Answer:** Answer the question directly and without fluff. If you don't know, use the "I would be glad to research it for you" pattern.
3.  **Use Off-Handed Transition:** After answering, you can ask a small, related question in an off-handed way to regain control and gather more data before passing back to the main flow.
4.  **Handle Disagreements:** If they disagree with a point, use the "I thought X as well, then I found out about Y, now I realize that Z" framework to save face and guide them.
</instructions>

<examples>
Customer: (Interrupting the pitch) "So are you guys based in the US?"
Response: "That's a great question. We have offices globally, but I'm actually from Turkey. Oh, and by the way, how many new patients are you currently seeing per month?"

Customer: (Interrupting discovery) "I don't think Google reviews are that important."
Response: "You know, I thought the same thing for a while. Then I found out that 60% of searchers never go past the top 3 options, and now I realize it's the single most important factor for local visibility."
</examples>

<constraints>
- Response must be 1-2 sentences.
- Your tone is helpful and unflustered.
- Your primary goal is to resolve the interruption and get the conversation back on track.
</constraints>

Return JSON with your interrupt handling response.
        """
    
    def _enhance_interrupt_response(self, response: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Enhance interrupt response with specific improvements"""
        suggestion = response.get("suggestion", "")
        
        # Determine response type
        if any(word in suggestion.lower() for word in ["recap", "summary", "discussed"]):
            response["type"] = "summarize"
        elif any(word in suggestion.lower() for word in ["back to", "return to", "continue"]):
            response["type"] = "redirect"
        elif any(word in suggestion.lower() for word in ["understand", "appreciate", "hear"]):
            response["type"] = "acknowledge"
        else:
            response["type"] = "bridge"
        
        # Add interrupt context
        response["context"] = response.get("context", {})
        response["context"]["recovery_method"] = response["type"]
        response["context"]["stage_continuation"] = context.current_stage
        
        # Add interrupt-specific next actions
        response["next_actions"] = response.get("next_actions", [])
        response["next_actions"].extend([
            "Monitor for additional interruptions",
            "Ensure customer feels heard",
            "Maintain conversation momentum"
        ])
        
        return response
    
    def _get_fallback_interrupt_response(self) -> Dict[str, Any]:
        """Get fallback response when interrupt handling fails"""
        return {
            "immediate_response": "I understand. Let me address that for you.",
            "interrupt_type": "general",
            "priority": "medium",
            "recovery_plan": {
                "approach": "acknowledge_and_continue",
                "timing": "immediate",
                "transition_method": "bridge",
                "content_adjustments": ["acknowledge_input", "continue_conversation"]
            },
            "context_updates": {
                "interrupt_logged": True,
                "customer_state": "neutral"
            },
            "confidence": 0.5
        }
    
    def determine_interrupt_urgency(self, text: str) -> str:
        """Determine how urgently an interruption needs to be handled"""
        critical_indicators = ["stop", "wait", "emergency", "urgent", "important"]
        high_indicators = ["question", "confused", "don't understand", "concern"]
        medium_indicators = ["by the way", "also", "just wanted to say"]
        
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in critical_indicators):
            return "critical"
        elif any(indicator in text_lower for indicator in high_indicators):
            return "high"
        elif any(indicator in text_lower for indicator in medium_indicators):
            return "medium"
        else:
            return "low"
    
    def should_pause_main_conversation(self, analysis: Dict[str, Any]) -> bool:
        """Determine if main conversation should be paused to handle interrupt"""
        return (
            analysis["priority"] in ["critical", "high"] or
            analysis["flow_impact"] == "high" or
            analysis["type"] in ["urgency", "emotional", "clarification"]
        ) 