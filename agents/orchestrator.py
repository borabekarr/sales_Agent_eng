import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import WebSocket

from models.schemas import (
    Message, CustomerProfile, Suggestion, SuggestionResponse,
    ConversationSummary, PerformanceMetrics, AgentContext
)
from services.assembly_ai import AssemblyAIService
from services.gemini_api import GeminiAPIService
from services.conversation import ConversationService
from agents.opening_agent import OpeningAgent
from agents.discovery_agent import DiscoveryAgent
from agents.pitch_agent import PitchAgent
from agents.objection_agent import ObjectionAgent
from agents.closing_agent import ClosingAgent
from agents.interrupt_agent import InterruptAgent
from utils.logging import LoggerMixin


class ConversationOrchestrator(LoggerMixin):
    """Main orchestrator for managing conversation flow and agents"""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        assembly_ai_service: AssemblyAIService,
        gemini_api_service: GeminiAPIService,
        conversation_service: ConversationService
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.assembly_ai_service = assembly_ai_service
        self.gemini_api_service = gemini_api_service
        self.conversation_service = conversation_service
        
        # Session state
        self.current_stage = "opening"
        self.customer_profile = CustomerProfile()
        self.conversation_history: List[Message] = []
        self.context_stack: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.last_suggestion: Optional[Suggestion] = None
        self.audio_websocket: Optional[WebSocket] = None
        
        # Initialize specialized agents
        self.agents = {
            "opening": OpeningAgent(gemini_api_service),
            "discovery": DiscoveryAgent(gemini_api_service),
            "pitch": PitchAgent(gemini_api_service),
            "objection": ObjectionAgent(gemini_api_service),
            "closing": ClosingAgent(gemini_api_service),
            "interrupt": InterruptAgent(gemini_api_service)
        }
        
        # Audio processing state
        self.audio_processing_active = False
        self.pending_audio_buffer = b""
        
        # Setup Assembly AI callbacks
        self.assembly_ai_service.add_message_callback(self._on_transcription_received)
        self.assembly_ai_service.add_error_callback(self._on_assembly_ai_error)
        
        self.log_info(
            "Conversation orchestrator initialized",
            session_id=session_id,
            user_id=user_id
        )
    
    async def start_audio_processing(self, websocket: WebSocket):
        """Start audio processing with Assembly AI"""
        try:
            self.audio_websocket = websocket
            
            # Connect to Assembly AI
            await self.assembly_ai_service.connect(
                language="en",  # Default to English, could be configurable
                speaker_diarization=True
            )
            
            self.audio_processing_active = True
            
            self.log_info("Audio processing started", session_id=self.session_id)
            
        except Exception as e:
            self.log_error("Failed to start audio processing", error=str(e))
            raise
    
    async def stop_audio_processing(self):
        """Stop audio processing"""
        try:
            self.audio_processing_active = False
            await self.assembly_ai_service.disconnect()
            self.audio_websocket = None
            
            self.log_info("Audio processing stopped", session_id=self.session_id)
            
        except Exception as e:
            self.log_error("Error stopping audio processing", error=str(e))
    
    async def process_audio_data(self, audio_data: bytes):
        """Process incoming audio data"""
        if not self.audio_processing_active:
            return
        
        try:
            # Send audio to Assembly AI
            await self.assembly_ai_service.send_audio(audio_data)
            
        except Exception as e:
            self.log_error("Error processing audio data", error=str(e))
    
    async def _on_transcription_received(self, transcription_data: Dict[str, Any]):
        """Handle transcription from Assembly AI"""
        try:
            if not transcription_data.get("is_final", False):
                return  # Only process final transcriptions
            
            text = transcription_data.get("text", "").strip()
            if not text:
                return
            
            speaker = transcription_data.get("speaker", "customer")
            confidence = transcription_data.get("confidence", 0.9)
            
            # Add message to conversation history
            message = await self.conversation_service.add_message(
                session_id=self.session_id,
                speaker=speaker,
                text=text,
                confidence=confidence,
                stage=self.current_stage
            )
            
            self.conversation_history.append(message)
            self.last_activity = datetime.utcnow()
            
            # Process customer input
            if speaker == "customer":
                await self.process_customer_input(text)
            
            # Send real-time update via WebSocket
            if self.audio_websocket:
                await self.audio_websocket.send_json({
                    "type": "transcription",
                    "data": {
                        "message": message.dict(),
                        "speaker": speaker,
                        "text": text,
                        "confidence": confidence
                    }
                })
            
            self.log_info(
                "Transcription processed",
                session_id=self.session_id,
                speaker=speaker,
                text_length=len(text)
            )
            
        except Exception as e:
            self.log_error("Error handling transcription", error=str(e))
    
    async def _on_assembly_ai_error(self, error_message: str):
        """Handle Assembly AI errors"""
        self.log_error("Assembly AI error", error=error_message)
        
        # Send error to WebSocket if connected
        if self.audio_websocket:
            try:
                await self.audio_websocket.send_json({
                    "type": "error",
                    "data": {"message": error_message}
                })
            except:
                pass
    
    async def process_customer_input(self, text: str):
        """Process customer input and update conversation state"""
        try:
            # Update customer profile with new insights
            profile_insights = await self._extract_profile_insights(text)
            if profile_insights:
                self.customer_profile = await self.conversation_service.update_customer_profile(
                    self.customer_profile, profile_insights
                )
            
            # Check if stage transition is needed
            stage_analysis = await self.conversation_service.determine_next_stage(
                self.current_stage,
                self.conversation_history,
                self.customer_profile
            )
            
            if stage_analysis.get("should_advance", False):
                await self.advance_conversation_stage(stage_analysis["next_stage"])
            
            # Generate new suggestion
            await self.generate_next_suggestion()
            
        except Exception as e:
            self.log_error("Error processing customer input", error=str(e))
    
    async def generate_next_suggestion(self) -> SuggestionResponse:
        """Generate next AI suggestion based on current context"""
        try:
            # Get appropriate agent for current stage
            agent = self.agents.get(self.current_stage)
            if not agent:
                self.log_warning(f"No agent found for stage: {self.current_stage}")
                agent = self.agents["discovery"]  # Fallback to discovery
            
            # Build agent context
            context = AgentContext(
                current_stage=self.current_stage,
                customer_profile=self.customer_profile,
                recent_messages=self.conversation_history[-5:],
                conversation_history=self.conversation_history,
                context_stack=self.context_stack,
                session_metadata={"session_id": self.session_id, "user_id": self.user_id}
            )
            
            # Generate suggestion
            agent_response = await agent.generate_suggestion(context)
            
            # Create suggestion object
            suggestion = Suggestion(
                session_id=self.session_id,
                text=agent_response.get("suggestion", "Continue the conversation naturally."),
                type=agent_response.get("type", "statement"),
                confidence=agent_response.get("confidence", 0.8),
                stage=self.current_stage,
                context=agent_response.get("context", {}),
                alternatives=agent_response.get("alternatives", [])
            )
            
            self.last_suggestion = suggestion
            
            # Create response
            response = SuggestionResponse(
                suggestion=suggestion,
                context={
                    "stage": self.current_stage,
                    "customer_profile": self.customer_profile.dict(),
                    "stage_progress": await self._get_stage_progress()
                },
                next_actions=agent_response.get("next_actions", [])
            )
            
            self.log_info(
                "Generated suggestion",
                session_id=self.session_id,
                stage=self.current_stage,
                suggestion_type=suggestion.type
            )
            
            return response
            
        except Exception as e:
            self.log_error("Error generating suggestion", error=str(e))
            
            # Return fallback suggestion
            fallback_suggestion = Suggestion(
                session_id=self.session_id,
                text="That's interesting. Could you tell me more about that?",
                type="question",
                confidence=0.5,
                stage=self.current_stage,
                alternatives=["I'd like to understand that better.", "Can you elaborate on that?"]
            )
            
            return SuggestionResponse(
                suggestion=fallback_suggestion,
                context={"stage": self.current_stage},
                next_actions=["Listen actively", "Ask follow-up questions"]
            )
    
    async def handle_interrupt(
        self,
        speaker: str,
        text: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Handle conversation interruption"""
        try:
            # Save current context to stack
            self.context_stack.append({
                "stage": self.current_stage,
                "timestamp": timestamp,
                "context": "interrupted",
                "speaker": speaker,
                "text": text
            })
            
            # Get interrupt agent
            interrupt_agent = self.agents["interrupt"]
            
            # Build context
            context = AgentContext(
                current_stage=self.current_stage,
                customer_profile=self.customer_profile,
                recent_messages=self.conversation_history[-3:],
                conversation_history=self.conversation_history,
                context_stack=self.context_stack
            )
            
            # Generate interrupt response
            response = await interrupt_agent.handle_interrupt(context, text, speaker)
            
            # Add interrupt message to history
            interrupt_message = await self.conversation_service.add_message(
                session_id=self.session_id,
                speaker=speaker,
                text=text,
                stage=self.current_stage,
                metadata={"type": "interrupt"}
            )
            
            self.conversation_history.append(interrupt_message)
            self.last_activity = datetime.utcnow()
            
            self.log_info(
                "Handled interrupt",
                session_id=self.session_id,
                speaker=speaker,
                response_type=response.get("type", "unknown")
            )
            
            return response
            
        except Exception as e:
            self.log_error("Error handling interrupt", error=str(e))
            return {
                "immediate_response": "I understand. Let me address that for you.",
                "type": "acknowledgment",
                "confidence": 0.5
            }
    
    async def advance_conversation_stage(self, target_stage: str) -> Dict[str, Any]:
        """Advance conversation to new stage"""
        try:
            previous_stage = self.current_stage
            
            # Validate stage transition
            valid_transitions = self.conversation_service.get_valid_transitions(self.current_stage)
            if target_stage not in valid_transitions and target_stage != self.current_stage:
                self.log_warning(
                    f"Invalid stage transition: {self.current_stage} -> {target_stage}"
                )
                # Allow transition anyway but log warning
            
            self.current_stage = target_stage
            
            # Add to context stack
            self.context_stack.append({
                "type": "stage_transition",
                "from_stage": previous_stage,
                "to_stage": target_stage,
                "timestamp": datetime.utcnow()
            })
            
            # Generate new suggestion for the new stage
            new_suggestion = await self.generate_next_suggestion()
            
            self.log_info(
                "Advanced conversation stage",
                session_id=self.session_id,
                from_stage=previous_stage,
                to_stage=target_stage
            )
            
            return {
                "success": True,
                "previous_stage": previous_stage,
                "new_stage": target_stage,
                "suggestion": new_suggestion.dict()
            }
            
        except Exception as e:
            self.log_error("Error advancing conversation stage", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_session_summary(self) -> ConversationSummary:
        """Generate comprehensive session summary"""
        try:
            summary = await self.conversation_service.generate_conversation_summary(
                session_id=self.session_id,
                conversation_history=self.conversation_history,
                customer_profile=self.customer_profile,
                start_time=self.start_time,
                end_time=datetime.utcnow()
            )
            
            self.log_info(
                "Generated session summary",
                session_id=self.session_id,
                duration_minutes=summary.duration_minutes,
                message_count=summary.message_count
            )
            
            return summary
            
        except Exception as e:
            self.log_error("Error generating session summary", error=str(e))
            # Return basic summary
            return ConversationSummary(
                session_id=self.session_id,
                start_time=self.start_time,
                end_time=datetime.utcnow(),
                duration_minutes=(datetime.utcnow() - self.start_time).total_seconds() / 60,
                message_count=len(self.conversation_history),
                customer_profile=self.customer_profile,
                stages_covered=[self.current_stage]
            )
    
    async def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics for the session"""
        try:
            metrics = await self.conversation_service.calculate_conversation_metrics(
                session_id=self.session_id,
                conversation_history=self.conversation_history,
                start_time=self.start_time
            )
            
            return metrics
            
        except Exception as e:
            self.log_error("Error calculating performance metrics", error=str(e))
            # Return basic metrics
            return PerformanceMetrics(
                session_id=self.session_id,
                avg_response_time=0,
                suggestion_accuracy=0.5,
                customer_engagement=0.5,
                stage_progression_rate=0.5,
                interruption_count=0,
                successful_transitions=0,
                total_transitions=1,
                conversation_flow_score=0.5
            )
    
    async def _extract_profile_insights(self, text: str) -> Dict[str, Any]:
        """Extract customer profile insights from text"""
        try:
            # Simple keyword-based extraction
            insights = {}
            
            text_lower = text.lower()
            
            # Extract pain points
            pain_indicators = ["problem", "issue", "challenge", "difficult", "struggle", "frustrating"]
            if any(indicator in text_lower for indicator in pain_indicators):
                insights["pain_points"] = [text[:100]]  # Store first 100 chars as pain point
            
            # Extract interests
            interest_indicators = ["interested", "like", "want", "need", "looking for"]
            if any(indicator in text_lower for indicator in interest_indicators):
                insights["interests"] = [text[:100]]
            
            # Extract budget hints
            budget_indicators = ["budget", "cost", "price", "expensive", "cheap", "affordable"]
            if any(indicator in text_lower for indicator in budget_indicators):
                insights["budget_range"] = "mentioned"
            
            # Extract timeline hints
            timeline_indicators = ["soon", "immediately", "urgent", "asap", "next month", "next quarter"]
            if any(indicator in text_lower for indicator in timeline_indicators):
                insights["timeline"] = "urgent" if any(word in text_lower for word in ["soon", "immediately", "urgent", "asap"]) else "flexible"
            
            return insights
            
        except Exception as e:
            self.log_error("Error extracting profile insights", error=str(e))
            return {}
    
    async def _get_stage_progress(self) -> Dict[str, float]:
        """Get progress for each stage"""
        try:
            stages = ["opening", "discovery", "pitch", "objection", "closing"]
            progress = {}
            
            stages_covered = set(msg.stage for msg in self.conversation_history)
            
            for stage in stages:
                if stage in stages_covered:
                    # Calculate completion based on messages and objectives
                    stage_messages = [msg for msg in self.conversation_history if msg.stage == stage]
                    completion = min(len(stage_messages) / 5, 1.0)  # Rough estimate
                    progress[stage] = completion
                else:
                    progress[stage] = 0.0
            
            return progress
            
        except Exception as e:
            self.log_error("Error calculating stage progress", error=str(e))
            return {stage: 0.5 for stage in ["opening", "discovery", "pitch", "objection", "closing"]}
    
    def get_stage_progress(self) -> Dict[str, float]:
        """Get current stage progress (sync version)"""
        return asyncio.create_task(self._get_stage_progress())
    
    def get_stage_actions(self) -> List[str]:
        """Get suggested actions for current stage"""
        stage_info = self.conversation_service.get_stage_info(self.current_stage)
        if stage_info:
            return stage_info.key_questions[:3]  # Return first 3 key questions as actions
        return ["Continue the conversation", "Ask relevant questions", "Listen actively"]
    
    def has_new_suggestion(self) -> bool:
        """Check if there's a new suggestion available"""
        # In a real implementation, this would track suggestion updates
        return self.last_suggestion is not None
    
    async def get_latest_suggestion(self) -> Suggestion:
        """Get the latest suggestion"""
        if self.last_suggestion:
            return self.last_suggestion
        
        # Generate new suggestion if none exists
        response = await self.generate_next_suggestion()
        return response.suggestion
    
    async def get_next_suggestion(self, context: AgentContext) -> Dict[str, Any]:
        """Get next suggestion based on conversation context using main controller logic"""
        try:
            # Use the main controller prompt to determine next agent
            controller_response = await self.gemini_api_service.generate_suggestion(
                context=context,
                agent_type="orchestrator",
                conversation_history=context.recent_messages,
                use_main_model=True  # Use Gemini 2.5 Pro for orchestrator
            )
            
            # Extract next agent from controller response
            next_agent = controller_response.get("next_agent", "discovery")
            
            # Map agent names to our internal agents
            agent_mapping = {
                "OpeningAgent": "opening",
                "DiscoveryAgent": "discovery", 
                "PitchAgent": "pitch",
                "ObjectionHandlerAgent": "objection",
                "ClosingAgent": "closing",
                "InterruptHandlerAgent": "interrupt"
            }
            
            agent_key = agent_mapping.get(next_agent, "discovery")
            
            # Update session metadata to track last agent
            context.session_metadata["last_agent"] = next_agent
            
            # Get suggestion from the selected agent
            if agent_key in self.agents:
                agent_response = await self.agents[agent_key].generate_suggestion(context)
                
                # Add orchestrator metadata
                agent_response.update({
                    "selected_agent": next_agent,
                    "orchestrator_reasoning": controller_response.get("reasoning", "Agent selection based on conversation flow"),
                    "conversation_stage": context.current_stage
                })
                
                self.log_info(
                    "Orchestrator selected agent and generated suggestion",
                    selected_agent=next_agent,
                    current_stage=context.current_stage
                )
                
                return agent_response
            else:
                # Fallback to discovery agent
                return await self.agents["discovery"].generate_suggestion(context)
                
        except Exception as e:
            self.log_error("Failed to orchestrate conversation", error=str(e))
            # Fallback response
            return {
                "suggestion": "That's interesting. Could you tell me more about your current situation?",
                "type": "discovery",
                "confidence": 0.6,
                "reasoning": "Fallback response due to orchestration error",
                "selected_agent": "DiscoveryAgent"
            }
    
    async def cleanup(self):
        """Cleanup session resources"""
        try:
            await self.stop_audio_processing()
            self.log_info("Session cleanup completed", session_id=self.session_id)
        except Exception as e:
            self.log_error("Error during session cleanup", error=str(e)) 