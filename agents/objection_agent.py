from typing import Dict, Any, List
from models.schemas import AgentContext
from services.gemini_api import GeminiAPIService
from utils.logging import LoggerMixin


class ObjectionAgent(LoggerMixin):
    """Specialized agent for handling objections and customer concerns"""
    
    def __init__(self, gemini_api_service: GeminiAPIService):
        self.gemini_api_service = gemini_api_service
        self.agent_type = "objection"
        
        # Common objection types and handling frameworks
        self.objection_types = {
            "price": {
                "indicators": ["expensive", "cost", "price", "budget", "cheap", "affordable"],
                "framework": "acknowledge → value → reframe → proof",
                "approach": "Focus on ROI and value, not just price"
            },
            "authority": {
                "indicators": ["boss", "manager", "decision", "approval", "team"],
                "framework": "acknowledge → qualify → involve → next steps",
                "approach": "Work with them to involve decision makers"
            },
            "timing": {
                "indicators": ["later", "not now", "busy", "next", "timing"],
                "framework": "acknowledge → urgency → cost of delay → timeline",
                "approach": "Create urgency around waiting"
            },
            "trust": {
                "indicators": ["sure", "doubt", "trust", "confident", "proven"],
                "framework": "acknowledge → evidence → references → trial",
                "approach": "Provide proof and reduce risk"
            },
            "competition": {
                "indicators": ["other", "competitor", "alternative", "comparing"],
                "framework": "acknowledge → differentiate → value → unique benefit",
                "approach": "Position unique advantages"
            },
            "feature": {
                "indicators": ["doesn't", "can't", "missing", "need", "require"],
                "framework": "acknowledge → clarify → alternative → benefit",
                "approach": "Find alternative ways to meet their needs"
            },
            "general": {
                "indicators": ["but", "however", "concern", "worry", "issue"],
                "framework": "acknowledge → understand → address → confirm",
                "approach": "Understand root concern before addressing"
            }
        }
    
    async def generate_suggestion(self, context: AgentContext) -> Dict[str, Any]:
        """Generate objection handling suggestions"""
        try:
            # Identify the objection type
            objection_analysis = self._analyze_objection(context)
            
            # Build custom prompt for objection handling
            custom_prompt = self._build_objection_prompt(context, objection_analysis)
            
            # Generate suggestion using Gemini API
            response = await self.gemini_api_service.generate_suggestion(
                context=context,
                agent_type=self.agent_type,
                conversation_history=context.recent_messages,
                custom_prompt=custom_prompt
            )
            
            # Enhance response with objection-specific logic
            enhanced_response = self._enhance_objection_response(response, context, objection_analysis)
            
            self.log_info(
                "Generated objection handling suggestion",
                session_id=context.session_metadata.get("session_id"),
                objection_type=objection_analysis.get("primary_type", "unknown"),
                confidence=enhanced_response.get("confidence", 0)
            )
            
            return enhanced_response
            
        except Exception as e:
            self.log_error("Error generating objection handling suggestion", error=str(e))
            return self._get_fallback_objection_response()
    
    async def handle_interrupt(self, context: AgentContext, interruption_text: str, speaker: str) -> Dict[str, Any]:
        """Handle objection-based interruptions"""
        try:
            # Quick objection analysis
            objection_type = self._quick_objection_classification(interruption_text)
            
            # Generate immediate response
            immediate_response = self._get_immediate_objection_response(objection_type, interruption_text)
            
            # Plan follow-up strategy
            follow_up_strategy = self._plan_objection_follow_up(objection_type, context)
            
            return {
                "immediate_response": immediate_response,
                "objection_type": objection_type,
                "follow_up_strategy": follow_up_strategy,
                "confidence": 0.8,
                "next_actions": [
                    "Listen for complete objection",
                    "Ask clarifying questions",
                    "Provide evidence or proof"
                ]
            }
            
        except Exception as e:
            self.log_error("Error handling objection interrupt", error=str(e))
            return {
                "immediate_response": "I understand your concern. Let me address that for you.",
                "objection_type": "general",
                "confidence": 0.5
            }
    
    def _analyze_objection(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze the objection to determine type and handling approach"""
        # Get recent customer messages that likely contain objections
        customer_messages = [msg for msg in context.recent_messages if msg.speaker == "customer"]
        recent_text = " ".join([msg.text.lower() for msg in customer_messages[-3:]])
        
        # Identify objection types present
        objection_scores = {}
        for obj_type, obj_data in self.objection_types.items():
            score = sum(1 for indicator in obj_data["indicators"] if indicator in recent_text)
            if score > 0:
                objection_scores[obj_type] = score
        
        # Determine primary objection type
        primary_type = max(objection_scores, key=objection_scores.get) if objection_scores else "general"
        
        # Analyze objection intensity
        intensity_indicators = ["absolutely", "definitely", "never", "impossible", "can't", "won't"]
        intensity = "high" if any(indicator in recent_text for indicator in intensity_indicators) else "medium"
        
        # Check if it's a genuine objection or just a question
        question_indicators = ["how", "what", "when", "where", "why", "?"]
        is_genuine_objection = not any(indicator in recent_text for indicator in question_indicators)
        
        # Assess emotional state
        emotional_indicators = {
            "frustrated": ["frustrated", "annoying", "difficult", "hard"],
            "skeptical": ["sure", "doubt", "believe", "really"],
            "concerned": ["worried", "concern", "nervous", "afraid"],
            "neutral": []
        }
        
        emotional_state = "neutral"
        for emotion, indicators in emotional_indicators.items():
            if any(indicator in recent_text for indicator in indicators):
                emotional_state = emotion
                break
        
        return {
            "primary_type": primary_type,
            "all_types": list(objection_scores.keys()),
            "intensity": intensity,
            "is_genuine_objection": is_genuine_objection,
            "emotional_state": emotional_state,
            "framework": self.objection_types[primary_type]["framework"],
            "approach": self.objection_types[primary_type]["approach"],
            "recent_text": recent_text
        }
    
    def _build_objection_prompt(self, context: AgentContext, objection_analysis: dict) -> str:
        """Build objection handling prompt for addressing customer concerns"""
        customer_data = context.customer_profile.dict()
        recent_history = []
        for msg in context.recent_messages[-5:]:
            speaker = "SELLER" if msg.speaker == "seller" else "CUSTOMER"
            recent_history.append(f"{speaker}: {msg.text}")
        
        recent_history_text = "\n".join(recent_history) if recent_history else "No recent history"
        customer_message = context.recent_messages[-1].text if context.recent_messages else ""
        discovered_pains = context.context_stack[-3:] if context.context_stack else []
        
        return f"""
<role>You are the Objection Handler Agent. Your goal is NOT to argue or directly counter an objection. Your goal is to use the looping process to deflect the objection, resell the three core beliefs (product, you, company), and lower the customer's action threshold.</role>

<context>
- Current Stage: ObjectionHandling
- Customer Profile: {customer_data}
- Customer Pains: {discovered_pains}
- The Objection: "{customer_message}"
- Conversation History: {recent_history_text}
- Objection Analysis: {objection_analysis}
</context>

<instructions>
1.  **Acknowledge & Deflect:** Immediately acknowledge their concern and deflect. Use "I hear what you're saying. But let me ask you a question..." or "I understand. You see, the true beauty of this system is..."
2.  **Identify the Real Objection Type:**
    * If they say **"I have no money for that,"** use script #6. Acknowledge the economy, confirm they like the idea, and ask what they *can* afford.
    * If they say **"I have to talk to my business partner,"** use script #3. Ask what the partner would oppose to uncover their own fears.
    * For any other objection (e.g., "I need to think," "It's bad timing," "I've been burned before"), treat it as a belief issue and start the main loop.
3.  **Execute the Loop:**
    * **Resell the Product (Logic):** "Does the idea make sense to you? Do you like the idea?"
    * **Resell Yourself & Company (Emotion):** Talk about your values, the long-term relationship, and your commitment to their success. Use offsetting language patterns like "I'm gonna hold your hand every step of the way."
    * **Minimize Risk:** Ask "What's the worst that can possibly happen?" Use the refund guarantee.
4.  **Use Powerful Language:** Weave in trigger words ("investment," "only," "because") and powerful closing patterns ("And believe me...").
</instructions>

<examples>
Customer: "I have to talk to my business partner before I make a decision."
Response: "I understand. Well, what would happen if they say no?"

Customer: "I need to think it over."
Response: "Yeah, you can always get back to me. But before I leave, what was it that you were wanting to go over in your mind, just so I know what questions you'll have later?"

Customer: "That sounds great but, I don't know..."
Response: "Listen, I understand it's like a big decision for you then. But I'm here to help you, {{Client Name}}. We're not just giving you the system and disappearing. It's a long-term relationship."
</examples>

<constraints>
- Response must be 1-2 sentences.
- Your tone is calm, curious, and utterly sincere. You are here to help them overcome their fear.
- Do not directly fight the objection. Always loop.
</constraints>

Return JSON with your objection handling response.
        """
    
    def _get_objection_guidelines(self, objection_type: str) -> str:
        """Get specific guidelines for handling different objection types"""
        guidelines = {
            "price": """
            - Never compete on price alone - compete on value
            - Break down the investment vs. the return
            - Compare cost of solution vs. cost of problem
            - Use payment options or ROI timeline
            - Reference similar customers who saw value
            """,
            "authority": """
            - Don't see this as rejection - it's process
            - Help them become an internal champion
            - Provide materials they can share with decision makers
            - Offer to present to the team
            - Understand the approval process
            """,
            "timing": """
            - Create urgency around the cost of waiting
            - Highlight what they're losing by not acting
            - Offer limited-time incentives if appropriate
            - Break implementation into phases
            - Show quick wins they could achieve
            """,
            "trust": """
            - Provide social proof and references
            - Offer trial periods or guarantees
            - Share relevant case studies
            - Connect them with similar customers
            - Reduce risk with phased approach
            """,
            "competition": """
            - Don't badmouth competitors
            - Focus on unique differentiators
            - Highlight specific advantages for their situation
            - Use comparison frameworks
            - Emphasize the relationship and service
            """,
            "feature": """
            - Understand the underlying need behind the feature
            - Explain alternative ways to achieve their goal
            - Highlight other benefits that outweigh this gap
            - Discuss roadmap or custom development
            - Focus on most important capabilities
            """
        }
        
        return guidelines.get(objection_type, """
        - Listen completely before responding
        - Ask clarifying questions to understand root concern
        - Provide specific, relevant solutions
        - Use evidence and proof points
        - Check for understanding and agreement
        """)
    
    def _enhance_objection_response(self, response: Dict[str, Any], context: AgentContext, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response with objection-specific improvements"""
        suggestion = response.get("suggestion", "")
        
        # Determine response type based on content and framework step
        framework_step = self._determine_framework_step(suggestion, analysis)
        
        response["type"] = framework_step
        response["context"] = response.get("context", {})
        response["context"]["objection_type"] = analysis["primary_type"]
        response["context"]["framework_step"] = framework_step
        response["context"]["risk_level"] = self._assess_objection_risk(analysis, context)
        
        # Add objection-specific next actions
        response["next_actions"] = response.get("next_actions", [])
        response["next_actions"].extend(self._get_objection_next_actions(analysis["primary_type"], framework_step))
        
        # Ensure alternatives are objection-focused
        if not response.get("alternatives"):
            response["alternatives"] = self._get_objection_alternatives(analysis["primary_type"], framework_step)
        
        # Add confidence adjustment based on objection complexity
        if analysis["intensity"] == "high":
            response["confidence"] = max(0.5, response.get("confidence", 0.8) - 0.2)
        
        return response
    
    def _determine_framework_step(self, suggestion: str, analysis: Dict[str, Any]) -> str:
        """Determine which step of the objection handling framework this represents"""
        suggestion_lower = suggestion.lower()
        
        if any(word in suggestion_lower for word in ["understand", "hear", "appreciate", "see"]):
            return "acknowledge"
        elif "?" in suggestion or any(word in suggestion_lower for word in ["help me", "clarify", "explain"]):
            return "clarify"
        elif any(word in suggestion_lower for word in ["however", "actually", "fact", "example", "case"]):
            return "evidence"
        elif any(word in suggestion_lower for word in ["think about", "consider", "perspective", "way"]):
            return "reframe"
        elif any(word in suggestion_lower for word in ["make sense", "address", "resolve", "move forward"]):
            return "close"
        else:
            return "acknowledge"  # Default
    
    def _assess_objection_risk(self, analysis: Dict[str, Any], context: AgentContext) -> str:
        """Assess the risk level of this objection to the deal"""
        risk_factors = 0
        
        # High intensity objections are riskier
        if analysis["intensity"] == "high":
            risk_factors += 2
        
        # Multiple objection types indicate higher risk
        if len(analysis["all_types"]) >= 3:
            risk_factors += 1
        
        # Emotional state affects risk
        if analysis["emotional_state"] in ["frustrated", "skeptical"]:
            risk_factors += 1
        
        # Price objections can be deal killers
        if analysis["primary_type"] == "price":
            risk_factors += 1
        
        # Authority objections are usually manageable
        if analysis["primary_type"] == "authority":
            risk_factors -= 1
        
        if risk_factors >= 3:
            return "high"
        elif risk_factors >= 1:
            return "medium"
        else:
            return "low"
    
    def _get_objection_next_actions(self, objection_type: str, framework_step: str) -> List[str]:
        """Get next actions based on objection type and framework step"""
        next_actions = {
            "acknowledge": ["Listen for complete concern", "Show empathy", "Ask clarifying questions"],
            "clarify": ["Dig deeper into root cause", "Understand their perspective", "Identify decision criteria"],
            "evidence": ["Provide specific proof points", "Share relevant examples", "Offer trial or demo"],
            "reframe": ["Help them see different perspective", "Focus on value and benefits", "Address misunderstandings"],
            "close": ["Confirm resolution", "Check for other concerns", "Move to next step"]
        }
        
        return next_actions.get(framework_step, ["Continue addressing the concern"])
    
    def _get_objection_alternatives(self, objection_type: str, framework_step: str) -> List[str]:
        """Get alternative responses for objection handling"""
        alternatives = {
            "price": [
                "I understand cost is important. Let's look at the value this creates.",
                "That's a fair concern. What if I could show you how this pays for itself?",
                "I hear you on the investment. Let me break down the ROI for you."
            ],
            "authority": [
                "I'd be happy to help you present this to your team.",
                "What information would help you discuss this internally?",
                "Would it be helpful if I joined a call with your decision makers?"
            ],
            "timing": [
                "I understand timing is important. What's driving your timeline?",
                "What would need to change for the timing to work better?",
                "Let's talk about what you're missing out on by waiting."
            ],
            "trust": [
                "I understand you want to feel confident in this decision.",
                "Let me share how we've helped companies in similar situations.",
                "What would help you feel more comfortable moving forward?"
            ]
        }
        
        return alternatives.get(objection_type, [
            "I understand your concern. Let me address that directly.",
            "That's a valid point. Here's how we handle that.",
            "I appreciate you bringing that up. Let me explain."
        ])
    
    def _quick_objection_classification(self, text: str) -> str:
        """Quickly classify objection type for interrupt handling"""
        text_lower = text.lower()
        
        for obj_type, obj_data in self.objection_types.items():
            if any(indicator in text_lower for indicator in obj_data["indicators"]):
                return obj_type
        
        return "general"
    
    def _get_immediate_objection_response(self, objection_type: str, text: str) -> str:
        """Get immediate response to objection interrupt"""
        responses = {
            "price": "I understand cost is a concern. Let me address that for you.",
            "authority": "I appreciate you mentioning the decision process. Let's talk about that.",
            "timing": "I hear you on the timing. Let me understand your situation better.",
            "trust": "I want you to feel completely confident in this decision.",
            "competition": "I understand you're exploring options. Let me show you what makes us different.",
            "feature": "That's a great question about the features. Let me explain.",
            "general": "I understand your concern. Let me address that directly."
        }
        
        return responses.get(objection_type, "I hear what you're saying. Let me respond to that.")
    
    def _plan_objection_follow_up(self, objection_type: str, context: AgentContext) -> Dict[str, Any]:
        """Plan follow-up strategy for objection handling"""
        strategies = {
            "price": {
                "approach": "Value demonstration",
                "tactics": ["ROI calculation", "Cost of inaction", "Payment options"],
                "evidence": ["Case studies", "References", "Guarantees"]
            },
            "authority": {
                "approach": "Stakeholder involvement",
                "tactics": ["Champion development", "Executive presentation", "Decision criteria"],
                "evidence": ["Executive brief", "ROI summary", "Implementation plan"]
            },
            "timing": {
                "approach": "Urgency creation",
                "tactics": ["Opportunity cost", "Limited availability", "Quick wins"],
                "evidence": ["Timeline benefits", "Competitive advantage", "Market changes"]
            },
            "trust": {
                "approach": "Risk reduction",
                "tactics": ["Social proof", "Trial periods", "References"],
                "evidence": ["Customer testimonials", "Case studies", "Guarantees"]
            }
        }
        
        return strategies.get(objection_type, {
            "approach": "Direct address",
            "tactics": ["Clarification", "Evidence", "Confirmation"],
            "evidence": ["Relevant examples", "Proof points", "Expert opinions"]
        })
    
    def _format_customer_context(self, profile) -> str:
        """Format customer context for objection handling"""
        context_parts = []
        
        if profile.pain_points:
            context_parts.append(f"Pain Points: {', '.join(profile.pain_points)}")
        
        if profile.budget_range:
            context_parts.append(f"Budget Context: {profile.budget_range}")
        
        if profile.decision_authority:
            context_parts.append(f"Decision Role: {profile.decision_authority}")
        
        if profile.timeline:
            context_parts.append(f"Timeline: {profile.timeline}")
        
        return "\n".join(context_parts) if context_parts else "Limited customer context"
    
    def _get_fallback_objection_response(self) -> Dict[str, Any]:
        """Get fallback response when AI generation fails"""
        return {
            "suggestion": "I understand your concern, and I appreciate you bringing it up. Let me address that directly for you.",
            "type": "acknowledge",
            "confidence": 0.6,
            "reasoning": "Professional acknowledgment that validates concern while maintaining control",
            "alternatives": [
                "That's a valid point. Let me explain how we handle that.",
                "I hear what you're saying. Here's my perspective on that."
            ],
            "next_actions": [
                "Ask clarifying questions",
                "Understand the root concern",
                "Provide specific evidence or solutions"
            ],
            "context": {
                "objection_type": "general",
                "framework_step": "acknowledge",
                "risk_level": "medium"
            }
        }
    
    def should_transition_to_closing(self, context: AgentContext) -> bool:
        """Determine if objection has been resolved and ready for closing"""
        try:
            customer_messages = [msg for msg in context.recent_messages if msg.speaker == "customer"]
            
            if not customer_messages:
                return False
            
            recent_text = " ".join([msg.text.lower() for msg in customer_messages[-2:]])
            
            # Look for resolution signals
            resolution_signals = ["makes sense", "understand", "see", "okay", "good point", "fair enough"]
            if any(signal in recent_text for signal in resolution_signals):
                return True
            
            # Look for buying signals after objection handling
            buying_signals = ["how", "when", "next steps", "move forward", "interested"]
            if any(signal in recent_text for signal in buying_signals):
                return True
            
            # Check if they've stopped objecting and are asking questions
            question_count = sum(1 for msg in customer_messages[-3:] if "?" in msg.text)
            objection_indicators = ["but", "however", "concern", "worry"]
            recent_objections = any(indicator in recent_text for indicator in objection_indicators)
            
            if question_count >= 1 and not recent_objections:
                return True
            
            return False
            
        except Exception as e:
            self.log_error("Error determining closing transition", error=str(e))
            return False 