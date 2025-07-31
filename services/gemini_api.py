import asyncio
import json
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from utils.config import get_settings
from utils.logging import LoggerMixin
from models.schemas import Message, CustomerProfile, AgentContext


class GeminiAPIService(LoggerMixin):
    """Service for Gemini API interactions using Gemini 2.5 Pro for main agent and Flash for sub-agents"""
    
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        
        # Initialize models
        self.main_model = genai.GenerativeModel('gemini-2.5-pro')  # Main orchestrator
        self.sub_model = genai.GenerativeModel('gemini-2.5-pro')  # Sub-agents with reasoning
        
        # Generation config for consistent responses
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            max_output_tokens=1000,
            response_mime_type="application/json"
        )
    
    async def generate_suggestion(
        self,
        context: AgentContext,
        agent_type: str,
        conversation_history: List[Message],
        custom_prompt: Optional[str] = None,
        use_main_model: bool = False
    ) -> Dict[str, Any]:
        """Generate AI suggestion based on conversation context"""
        try:
            # Build conversation context
            conversation_text = self._build_conversation_text(conversation_history)
            
            # Get agent-specific prompt
            system_prompt = custom_prompt or self._get_agent_prompt(agent_type, context)
            
            # Combine system prompt with conversation
            full_prompt = f"{system_prompt}\n\nConversation History:\n{conversation_text}\n\nPlease respond with a JSON object containing your suggestion."
            
            # Choose model based on agent type and use_main_model flag
            model = self.main_model if use_main_model or agent_type == "orchestrator" else self.sub_model
            
            # Call Gemini API
            response = await asyncio.to_thread(
                model.generate_content,
                full_prompt,
                generation_config=self.generation_config
            )
            
            # Parse response
            suggestion_text = response.text if response.text else ""
            
            # Extract structured data from response
            parsed_response = self._parse_suggestion_response(suggestion_text, agent_type)
            
            self.log_info(
                "Generated AI suggestion with Gemini",
                agent_type=agent_type,
                model_used="gemini-2.5-pro" if use_main_model or agent_type == "orchestrator" else "gemini-2.5-pro",
                response_length=len(suggestion_text)
            )
            
            return parsed_response
            
        except Exception as e:
            self.log_error(
                "Failed to generate AI suggestion with Gemini",
                agent_type=agent_type,
                error=str(e)
            )
            # Return fallback response
            return self._get_fallback_response(agent_type)
    
    async def analyze_customer_profile(
        self,
        conversation_history: List[Message]
    ) -> CustomerProfile:
        """Analyze conversation to build customer profile using Gemini 2.5 Pro (Reasoning)"""
        try:
            conversation_text = self._build_conversation_text(conversation_history)
            
            system_prompt = """
            You are an expert sales analyst using advanced reasoning. Analyze the conversation to build a detailed customer profile.
            
            Extract and analyze:
            1. Customer's pain points and challenges
            2. Their interests and needs  
            3. Budget indicators
            4. Decision-making authority
            5. Timeline urgency
            6. Overall sentiment
            7. Company information
            8. Role and responsibilities
            
            Return your analysis in this JSON format:
            {
                "name": "customer name if mentioned",
                "company": "company name if mentioned", 
                "role": "job title/role if mentioned",
                "pain_points": ["list of identified pain points"],
                "interests": ["list of interests and needs"],
                "budget_range": "budget indicators or 'unknown'",
                "decision_authority": "level of decision making power",
                "timeline": "urgency/timeline mentioned",
                "sentiment": "positive/neutral/negative"
            }
            """
            
            full_prompt = f"{system_prompt}\n\nConversation:\n{conversation_text}"
            
            response = await asyncio.to_thread(
                self.sub_model.generate_content,
                full_prompt,
                generation_config=self.generation_config
            )
            
            # Parse JSON response
            response_text = response.text if response.text else "{}"
            profile_data = self._extract_json_from_response(response_text)
            
            return CustomerProfile(**profile_data)
            
        except Exception as e:
            self.log_error("Failed to analyze customer profile with Gemini", error=str(e))
            return CustomerProfile()
    
    async def determine_conversation_stage(
        self,
        conversation_history: List[Message],
        current_stage: str
    ) -> Dict[str, Any]:
        """Determine appropriate conversation stage based on content using Gemini 2.5 Pro (Reasoning)"""
        try:
            conversation_text = self._build_conversation_text(conversation_history[-10:])
            
            system_prompt = f"""
            You are a sales conversation expert with advanced reasoning capabilities. Analyze the conversation to determine the appropriate sales stage.
            
            Current stage: {current_stage}
            
            Sales stages:
            1. opening - Initial rapport building and introduction
            2. discovery - Understanding customer needs and pain points  
            3. pitch - Presenting solution and value proposition
            4. objection - Handling concerns and resistance
            5. closing - Finalizing deal and next steps
            
            Analyze the conversation and return:
            {{
                "recommended_stage": "stage name",
                "confidence": 0.8,
                "reasoning": "why this stage is appropriate",
                "stage_completion": 0.7,
                "next_actions": ["specific actions for this stage"]
            }}
            """
            
            full_prompt = f"{system_prompt}\n\nConversation:\n{conversation_text}"
            
            response = await asyncio.to_thread(
                self.sub_model.generate_content,
                full_prompt,
                generation_config=self.generation_config
            )
            
            response_text = response.text if response.text else "{}"
            return self._extract_json_from_response(response_text)
            
        except Exception as e:
            self.log_error("Failed to determine conversation stage with Gemini", error=str(e))
            return {
                "recommended_stage": current_stage,
                "confidence": 0.5,
                "reasoning": "Error in analysis",
                "stage_completion": 0.5,
                "next_actions": []
            }
    
    async def handle_interruption(
        self,
        context: AgentContext,
        interruption_text: str,
        speaker: str
    ) -> Dict[str, Any]:
        """Handle conversation interruption with appropriate response using Gemini 2.5 Pro (Reasoning)"""
        try:
            system_prompt = f"""
            You are an expert sales conversation assistant with advanced reasoning. The customer has just interrupted with: "{interruption_text}"
            
            Current context:
            - Stage: {context.current_stage}
            - Customer profile: {context.customer_profile.dict()}
            
            Provide an immediate, contextual response that:
            1. Acknowledges the interruption professionally
            2. Addresses their concern or question
            3. Maintains conversation flow
            4. Keeps the sales process on track
            
            Return response in this format:
            {{
                "immediate_response": "what to say right now",
                "follow_up_questions": ["questions to ask next"],
                "stage_adjustment": "any stage changes needed",
                "context_updates": {{"key": "value pairs for context"}}
            }}
            """
            
            response = await asyncio.to_thread(
                self.sub_model.generate_content,
                system_prompt,
                generation_config=self.generation_config
            )
            
            response_text = response.text if response.text else "{}"
            return self._extract_json_from_response(response_text)
            
        except Exception as e:
            self.log_error("Failed to handle interruption with Gemini", error=str(e))
            return {
                "immediate_response": "I understand your concern. Let me address that for you.",
                "follow_up_questions": ["Could you tell me more about that?"],
                "stage_adjustment": None,
                "context_updates": {}
            }
    
    async def generate_conversation_summary(
        self,
        conversation_history: List[Message],
        customer_profile: CustomerProfile
    ) -> Dict[str, Any]:
        """Generate comprehensive conversation summary using Gemini 2.5 Pro"""
        try:
            conversation_text = self._build_conversation_text(conversation_history)
            
            system_prompt = """
            Generate a comprehensive sales conversation summary using advanced reasoning. Analyze the entire conversation and provide:
            
            1. Key topics discussed
            2. Customer pain points identified
            3. Objections raised and how they were handled
            4. Value propositions presented
            5. Next steps agreed upon
            6. Overall sentiment and engagement level
            7. Success probability assessment
            8. Recommended follow-up actions
            
            Format as JSON:
            {
                "key_topics": ["topic1", "topic2"],
                "pain_points": ["pain1", "pain2"],
                "objections": ["objection1", "objection2"],
                "value_props": ["value1", "value2"],
                "next_steps": ["step1", "step2"],
                "sentiment": "positive/neutral/negative",
                "engagement_level": 0.8,
                "success_probability": 0.7,
                "follow_up_actions": ["action1", "action2"],
                "conversation_quality": 0.8,
                "duration_assessment": "appropriate/too_long/too_short"
            }
            """
            
            full_prompt = f"{system_prompt}\n\nConversation:\n{conversation_text}"
            
            response = await asyncio.to_thread(
                self.main_model.generate_content,
                full_prompt,
                generation_config=self.generation_config
            )
            
            response_text = response.text if response.text else "{}"
            return self._extract_json_from_response(response_text)
            
        except Exception as e:
            self.log_error("Failed to generate conversation summary with Gemini", error=str(e))
            return {
                "key_topics": [],
                "pain_points": [],
                "objections": [],
                "value_props": [],
                "next_steps": [],
                "sentiment": "neutral",
                "engagement_level": 0.5,
                "success_probability": 0.5,
                "follow_up_actions": [],
                "conversation_quality": 0.5,
                "duration_assessment": "unknown"
            }
    
    def _build_conversation_text(self, messages: List[Message]) -> str:
        """Build conversation text for Gemini input"""
        conversation_parts = []
        
        for msg in messages:
            speaker_label = "SELLER" if msg.speaker == "seller" else "CUSTOMER"
            conversation_parts.append(f"{speaker_label}: {msg.text}")
        
        return "\n".join(conversation_parts)
    
    def _get_agent_prompt(self, agent_type: str, context: AgentContext) -> str:
        """Get agent-specific system prompt for Gemini"""
        customer_data = context.customer_profile.dict()
        recent_history = []
        for msg in context.recent_messages[-5:]:  # Last 5 messages
            speaker = "SELLER" if msg.speaker == "seller" else "CUSTOMER"
            recent_history.append(f"{speaker}: {msg.text}")
        
        recent_history_text = "\n".join(recent_history) if recent_history else "No recent history"
        customer_message = context.recent_messages[-1].text if context.recent_messages else ""
        
        prompts = {
            "orchestrator": f"""
<role>You are the Main Controller Agent for a real-time AI sales assistant. Your primary function is to analyze the conversation flow and delegate tasks to the appropriate specialized agent. You do not speak to the customer directly.</role>

<context>
- Current Stage: {context.current_stage}
- Customer Profile: {customer_data}
- Last Customer Input: "{customer_message}"
- Last Agent: {context.session_metadata.get('last_agent', 'None')}
- Conversation History: {recent_history_text}
</context>

<instructions>
1.  **Track the Conversation Stage:** Maintain the current stage of the sale: `Opening`, `Discovery`, `Pitch`, `ObjectionHandling`, `Closing`, `Interrupted`.
2.  **Analyze Customer Input:** Based on the `Last Customer Input`, determine the correct next step.
    * If the conversation is just beginning, select `OpeningAgent`.
    * If the `OpeningAgent` has established rapport, select `DiscoveryAgent` to start asking questions.
    * If enough pain points have been uncovered in `Discovery`, select `PitchAgent`.
    * If the `PitchAgent` has presented the offer and the customer responds with anything other than a clear "yes" (e.g., "I need to think," "It's too expensive," "I have to talk to my partner"), select `ObjectionHandlerAgent`.
    * If the `ObjectionHandlerAgent` has successfully navigated the objection and the customer shows buying signals, select `ClosingAgent`.
    * If the customer asks a question or interrupts the agent's flow mid-sentence, select `InterruptHandlerAgent` to provide a quick response before resuming the flow.
3.  **Select the Next Agent:** Your only output will be the name of the next agent to activate. Example: `ObjectionHandlerAgent`.
</instructions>

<constraints>
- Your output must ONLY be the name of the agent to be activated next.
- Do not generate any conversational text.
</constraints>

Return JSON: {{"next_agent": "AgentName"}}
            """,
            
            "opening": f"""
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

Return JSON: {{"suggestion": "your response", "type": "opening", "confidence": 0.9}}
            """,
            
            "discovery": f"""
<role>You are the Discovery Agent. Your goal is to listen more than you talk. You must uncover the customer's challenges, their consequences, and amplify their pain indirectly by asking insightful questions. You are an empathetic expert seeking to understand.</role>

<context>
- Current Stage: Discovery
- Customer Profile: {customer_data}
- Last Customer Input: "{customer_message}"
- Conversation History: {recent_history_text}
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

Return JSON: {{"suggestion": "your response", "type": "discovery", "confidence": 0.9}}
            """,
            
            "pitch": f"""
<role>You are the Pitch Agent. Your goal is to present the logical and emotional case for the solution in a clear, confident, and compelling way. You are the authority figure who has the key to their desired future.</role>

<context>
- Current Stage: Pitch
- Customer Profile: {customer_data}
- Customer Pains: {context.context_stack[-3:] if context.context_stack else []}
- Last Customer Input: "{customer_message}"
- Conversation History: {recent_history_text}
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

Return JSON: {{"suggestion": "your response", "type": "pitch", "confidence": 0.9}}
            """,
            
            "objection": f"""
<role>You are the Objection Handler Agent. Your goal is NOT to argue or directly counter an objection. Your goal is to use the looping process to deflect the objection, resell the three core beliefs (product, you, company), and lower the customer's action threshold.</role>

<context>
- Current Stage: ObjectionHandling
- Customer Profile: {customer_data}
- Customer Pains: {context.context_stack[-3:] if context.context_stack else []}
- The Objection: "{customer_message}"
- Conversation History: {recent_history_text}
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

Return JSON: {{"suggestion": "your response", "type": "objection", "confidence": 0.9}}
            """,
            
            "closing": f"""
<role>You are the Closing Agent. Your goal is to confidently and clearly ask for the order. You have built the case, handled the objections, and now it's time to guide the customer to a decision. You are a reasonable man making a reasonable request.</role>

<context>
- Current Stage: Closing
- Customer Profile: {customer_data}
- Last Customer Input: "{customer_message}"
- Conversation History: {recent_history_text}
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

Return JSON: {{"suggestion": "your response", "type": "closing", "confidence": 0.9}}
            """,
            
            "interrupt": f"""
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

Return JSON: {{"suggestion": "your response", "type": "interrupt", "confidence": 0.9}}
            """
        }
        
        return prompts.get(agent_type, prompts["discovery"])
    
    def _parse_suggestion_response(self, response_text: str, agent_type: str) -> Dict[str, Any]:
        """Parse and structure the suggestion response from Gemini"""
        try:
            # Try to extract JSON if present
            json_data = self._extract_json_from_response(response_text)
            if json_data:
                return json_data
        except:
            pass
        
        # Fallback to text parsing
        return {
            "suggestion": response_text.strip(),
            "type": agent_type,
            "confidence": 0.8,
            "alternatives": [],
            "reasoning": "Generated by Gemini AI",
            "next_actions": []
        }
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from Gemini response text"""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            # Find JSON in response
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_text = cleaned_text[start_idx:end_idx]
                return json.loads(json_text)
            
            # Try parsing the entire cleaned text
            return json.loads(cleaned_text)
        except Exception as e:
            self.log_warning(f"Failed to parse JSON from Gemini response: {e}")
            return {}
    
    def _get_fallback_response(self, agent_type: str) -> Dict[str, Any]:
        """Get fallback response when Gemini API fails"""
        fallbacks = {
            "opening": {
                "suggestion": "Thank you for taking the time to speak with me today. I'm excited to learn more about your business and how we might be able to help.",
                "type": "opening",
                "confidence": 0.5,
                "alternatives": [
                    "I appreciate you joining me today. Could you start by telling me a bit about your current situation?",
                    "Great to connect with you. What's been your biggest challenge lately?"
                ]
            },
            "discovery": {
                "suggestion": "That's interesting. Could you tell me more about how that impacts your business?",
                "type": "discovery",
                "confidence": 0.5,
                "alternatives": [
                    "Help me understand - what would an ideal solution look like for you?",
                    "What's been the biggest obstacle you've faced with this?"
                ]
            },
            "pitch": {
                "suggestion": "Based on what you've shared, I believe our solution could address exactly what you're looking for.",
                "type": "pitch",
                "confidence": 0.5,
                "alternatives": [
                    "Let me show you how this directly solves the challenge you mentioned.",
                    "This feature specifically addresses the pain point you described."
                ]
            },
            "objection": {
                "suggestion": "I understand your concern. Let me address that directly.",
                "type": "objection",
                "confidence": 0.5,
                "alternatives": [
                    "That's a great question. Many of our clients had the same concern initially.",
                    "I appreciate you bringing that up. Here's how we typically handle that..."
                ]
            },
            "closing": {
                "suggestion": "Based on our conversation, it sounds like this could be a great fit. What questions do you have before we move forward?",
                "type": "closing",
                "confidence": 0.5,
                "alternatives": [
                    "What would need to happen for you to feel confident moving ahead?",
                    "Are you ready to take the next step?"
                ]
            }
        }
        
        return fallbacks.get(agent_type, fallbacks["discovery"])
    
    def is_service_available(self) -> bool:
        """Check if Gemini API service is available"""
        return bool(self.settings.GEMINI_API_KEY)
    
    async def test_connection(self) -> bool:
        """Test Gemini API connection"""
        try:
            response = await asyncio.to_thread(
                self.sub_model.generate_content,
                "Test connection. Respond with: {'status': 'connected'}",
                generation_config=self.generation_config
            )
            return bool(response.text)
        except Exception as e:
            self.log_error("Gemini API connection test failed", error=str(e))
            return False 