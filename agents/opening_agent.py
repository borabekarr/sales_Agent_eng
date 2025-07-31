from typing import Dict, Any
from models.schemas import AgentContext, AgentResponse
from services.gemini_api import GeminiAPIService
from utils.logging import LoggerMixin
import asyncio


class OpeningAgent(LoggerMixin):
    """Specialized agent for opening conversations and building rapport"""
    
    def __init__(self, gemini_api_service: GeminiAPIService):
        self.gemini_api_service = gemini_api_service
        self.agent_type = "opening"
    
    async def generate_suggestion(self, context: AgentContext) -> Dict[str, Any]:
        """Generate opening stage suggestions"""
        try:
            # Custom prompt for opening stage
            custom_prompt = self._build_opening_prompt(context)
            
            # Generate suggestion using Gemini API
            response = await self.gemini_api_service.generate_suggestion(
                context=context,
                agent_type=self.agent_type,
                conversation_history=context.recent_messages,
                custom_prompt=custom_prompt
            )
            
            # Enhance response with opening-specific logic
            enhanced_response = self._enhance_opening_response(response, context)
            
            self.log_info(
                "Generated opening suggestion",
                session_id=context.session_metadata.get("session_id"),
                suggestion_type=enhanced_response.get("type", "unknown")
            )
            
            return enhanced_response
            
        except Exception as e:
            self.log_error("Error generating opening suggestion", error=str(e))
            return self._get_fallback_opening_response()
    
    def _build_opening_prompt(self, context: AgentContext) -> str:
        """Build opening agent prompt for rapport building and first impression"""
        customer_data = context.customer_profile.dict()
        recent_history = []
        for msg in context.recent_messages[-5:]:
            speaker = "SELLER" if msg.speaker == "seller" else "CUSTOMER"
            recent_history.append(f"{speaker}: {msg.text}")
        
        recent_history_text = "\n".join(recent_history) if recent_history else "No recent history"
        customer_message = context.recent_messages[-1].text if context.recent_messages else ""
        
        return f"""
<role>You are the Opening Agent. Your goal is to make a powerful first impression, build immediate rapport, and establish yourself as a confident, authoritative expert who is here to help.</role>

<context>
- Current Stage: Opening
- Customer Profile: {customer_data}
- Last Customer Input: "{customer_message}"
- Conversation History: {recent_history_text}
</context>

<instructions>
1.  **Establish Authority & Confidence:** Start with a sharp, enthusiastic, and certain tone.
2.  **Use "Start with No" Technique:** Open by giving the customer an easy way to say "no" to protect their autonomy. For example, instead of "Do you have a minute?", use a reverse question.
3.  **Build Rapport:** Briefly introduce yourself and your purpose. Imply that you are an expert and that your time is valuable, but you are focused on them.
4.  **Transition to Discovery:** Your goal is to get permission to start the discovery process.
</instructions>

<examples>
Customer: "Hello?"
Response: "Hi {{Client Name}}, this is Bora. I know you weren't expecting my call. Is this a bad time to talk for a moment?"

Customer: "Who is this?"
Response: "This is Bora. I'm an AI Automation specialist for dental clinics. I promise to be brief, but I have an idea that might be incredibly valuable for you. Would it be ridiculous to share it?"
</examples>

<constraints>
- Response must be 1-2 sentences.
- Sound enthusiastic, sharp, and confident.
- Your primary goal is to get a "no" that means "yes, continue."
</constraints>

Return JSON with your opening response.
        """
    
    def _enhance_opening_response(self, response: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Enhance the response with opening-specific improvements"""
        suggestion = response.get("suggestion", "")
        
        # Determine conversation stage within opening
        message_count = len(context.conversation_history)
        
        if message_count == 0:
            # First interaction - focus on greeting
            response["type"] = "greeting"
            response["context"] = response.get("context", {})
            response["context"]["opening_phase"] = "initial_greeting"
            
        elif message_count <= 3:
            # Early rapport building
            response["type"] = "rapport_building"
            response["context"] = response.get("context", {})
            response["context"]["opening_phase"] = "rapport_building"
            
        elif message_count <= 5:
            # Setting agenda and expectations
            response["type"] = "agenda_setting"
            response["context"] = response.get("context", {})
            response["context"]["opening_phase"] = "agenda_setting"
            
        else:
            # Transition to discovery
            response["type"] = "transition"
            response["context"] = response.get("context", {})
            response["context"]["opening_phase"] = "transition_to_discovery"
            response["next_actions"] = response.get("next_actions", []) + [
                "Begin understanding customer needs",
                "Ask open-ended discovery questions"
            ]
        
        # Add opening-specific alternatives if not present
        if not response.get("alternatives"):
            response["alternatives"] = self._get_opening_alternatives(response["type"])
        
        # Ensure professional tone
        if "greeting" in suggestion.lower() or "hello" in suggestion.lower():
            response["context"]["conversation_tone"] = "professional"
        
        return response
    
    def _get_opening_alternatives(self, suggestion_type: str) -> list:
        """Get alternative suggestions based on type"""
        alternatives = {
            "greeting": [
                "Good morning! Thank you for taking the time to speak with me today.",
                "Hi there! I'm excited to learn more about your business.",
                "Thank you for joining me today. I hope you're having a great day so far."
            ],
            "rapport_building": [
                "Before we dive in, how has your week been going?",
                "I'd love to hear a bit about what you're working on lately.",
                "What's been keeping you busy in your role recently?"
            ],
            "agenda_setting": [
                "I'd like to use our time effectively today. What would make this conversation most valuable for you?",
                "To make sure we cover what's most important to you, what are your main priorities right now?",
                "I have some ideas about how we might help, but I'd love to understand your situation first."
            ],
            "transition": [
                "Now that we've connected, I'd love to understand more about your current challenges.",
                "Let's dive into what brought you to explore a solution like ours.",
                "I'm curious to learn more about your business and what you're hoping to achieve."
            ]
        }
        
        return alternatives.get(suggestion_type, [
            "That's interesting. Could you tell me more?",
            "I'd love to understand that better.",
            "Help me understand your perspective on that."
        ])
    
    def _get_fallback_opening_response(self) -> Dict[str, Any]:
        """Get fallback response when AI generation fails"""
        return {
            "suggestion": "Thank you for taking the time to speak with me today. I'm looking forward to learning more about your business and how we might be able to help.",
            "type": "greeting",
            "confidence": 0.6,
            "reasoning": "Professional, warm greeting that sets positive tone",
            "alternatives": [
                "Good morning! I appreciate you joining me today.",
                "Thank you for your time today. I'm excited to hear about your business."
            ],
            "next_actions": [
                "Build rapport with the customer",
                "Ask about their current situation",
                "Set expectations for the conversation"
            ],
            "context": {
                "opening_phase": "initial_greeting",
                "conversation_tone": "professional",
                "rapport_level": "low"
            }
        }
    
    async def evaluate_rapport_level(self, context: AgentContext) -> str:
        """Evaluate the current level of rapport with the customer"""
        try:
            customer_messages = [msg for msg in context.recent_messages if msg.speaker == "customer"]
            
            if not customer_messages:
                return "unknown"
            
            # Simple rapport indicators
            positive_indicators = ["great", "good", "excellent", "thank you", "appreciate"]
            engagement_indicators = ["yes", "sure", "absolutely", "definitely"]
            personal_sharing = ["i", "we", "our", "my"]
            
            total_score = 0
            total_messages = len(customer_messages)
            
            for msg in customer_messages:
                text_lower = msg.text.lower()
                message_score = 0
                
                # Check for positive language
                if any(indicator in text_lower for indicator in positive_indicators):
                    message_score += 2
                
                # Check for engagement
                if any(indicator in text_lower for indicator in engagement_indicators):
                    message_score += 1
                
                # Check for personal sharing
                if any(indicator in text_lower for indicator in personal_sharing):
                    message_score += 1
                
                # Length indicates engagement
                if len(msg.text) > 20:
                    message_score += 1
                
                total_score += message_score
            
            # Calculate average rapport score
            avg_score = total_score / total_messages if total_messages > 0 else 0
            
            if avg_score >= 3:
                return "high"
            elif avg_score >= 1.5:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.log_error("Error evaluating rapport level", error=str(e))
            return "unknown"
    
    def should_transition_to_discovery(self, context: AgentContext) -> bool:
        """Determine if ready to transition to discovery stage"""
        try:
            # Check message count (minimum interactions)
            if len(context.conversation_history) < 4:
                return False
            
            # Check for rapport establishment
            rapport_level = asyncio.create_task(self.evaluate_rapport_level(context))
            if rapport_level in ["medium", "high"]:
                return True
            
            # Check for customer readiness signals
            customer_messages = [msg for msg in context.recent_messages if msg.speaker == "customer"]
            readiness_signals = ["tell me more", "how", "what", "interested", "learn", "understand"]
            
            for msg in customer_messages:
                if any(signal in msg.text.lower() for signal in readiness_signals):
                    return True
            
            # If conversation has gone on too long without transition
            if len(context.conversation_history) > 8:
                return True
            
            return False
            
        except Exception as e:
            self.log_error("Error determining transition readiness", error=str(e))
            return False 