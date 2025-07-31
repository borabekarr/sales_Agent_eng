import asyncio
import logging
from typing import Optional, Callable, Dict, Any, Type
import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)
from utils.config import get_settings
from utils.logging import LoggerMixin


class AssemblyAIV3Service(LoggerMixin):
    """Assembly AI v3 streaming service for real-time speech processing"""
    
    def __init__(self):
        self.settings = get_settings()
        # Use the provided Assembly AI API key
        self.api_key = "d62ad71a6cf54e02ac000e8c4920819f"
        self.client: Optional[StreamingClient] = None
        self.is_connected = False
        self.message_callbacks = []
        self.error_callbacks = []
        self.session_id: Optional[str] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger_internal = logging.getLogger(__name__)
    
    async def connect(self, language: str = "en", sample_rate: int = 16000):
        """Connect to Assembly AI v3 streaming service"""
        try:
            # Initialize streaming client
            self.client = StreamingClient(
                StreamingClientOptions(
                    api_key=self.api_key,
                    api_host="streaming.assemblyai.com",
                )
            )
            
            # Register event handlers
            self.client.on(StreamingEvents.Begin, self._on_begin)
            self.client.on(StreamingEvents.Turn, self._on_turn)
            self.client.on(StreamingEvents.Termination, self._on_terminated)
            self.client.on(StreamingEvents.Error, self._on_error)
            
            # Connect with streaming parameters
            await asyncio.to_thread(
                self.client.connect,
                StreamingParameters(
                    sample_rate=sample_rate,
                    format_turns=True,
                    language_code=language
                )
            )
            
            self.is_connected = True
            
            self.log_info(
                "Connected to Assembly AI v3 streaming",
                language=language,
                sample_rate=sample_rate
            )
            
        except Exception as e:
            self.log_error("Failed to connect to Assembly AI v3", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Assembly AI service"""
        try:
            if self.client and self.is_connected:
                await asyncio.to_thread(self.client.disconnect, terminate=True)
                self.is_connected = False
                self.client = None
                self.log_info("Disconnected from Assembly AI v3")
        except Exception as e:
            self.log_error("Error disconnecting from Assembly AI v3", error=str(e))
    
    async def stream_audio(self, audio_stream):
        """Stream audio data for transcription"""
        if not self.is_connected or not self.client:
            raise RuntimeError("Not connected to Assembly AI v3")
        
        try:
            await asyncio.to_thread(self.client.stream, audio_stream)
        except Exception as e:
            self.log_error("Error streaming audio data", error=str(e))
            raise
    
    async def stream_microphone(self, sample_rate: int = 16000):
        """Stream microphone input (for testing)"""
        if not self.is_connected or not self.client:
            raise RuntimeError("Not connected to Assembly AI v3")
        
        try:
            # Use Assembly AI's microphone stream
            microphone_stream = aai.extras.MicrophoneStream(sample_rate=sample_rate)
            await asyncio.to_thread(self.client.stream, microphone_stream)
        except Exception as e:
            self.log_error("Error streaming microphone", error=str(e))
            raise
    
    def add_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for transcription messages"""
        self.message_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Add callback for error handling"""
        self.error_callbacks.append(callback)
    
    def _on_begin(self, event: BeginEvent):
        """Handle session begin event"""
        self.session_id = event.id
        self.log_info(
            "Assembly AI v3 session started",
            session_id=event.id
        )
    
    def _on_turn(self, event: TurnEvent):
        """Handle turn event (transcription)"""
        if not event.transcript:
            return
        
        try:
            # Prepare message data for callbacks
            message_data = {
                "type": "transcription",
                "text": event.transcript,
                "confidence": getattr(event, 'confidence', 0.9),
                "is_final": event.end_of_turn,
                "end_of_turn": event.end_of_turn,
                "timestamp": getattr(event, 'timestamp', None),
                "speaker": self._determine_speaker(event),
                "raw_data": {
                    "turn_is_formatted": getattr(event, 'turn_is_formatted', False),
                    "session_id": self.session_id
                }
            }
            
            # Format turns if needed and not already formatted
            if event.end_of_turn and not getattr(event, 'turn_is_formatted', False):
                if self.client:
                    params = StreamingSessionParameters(format_turns=True)
                    self.client.set_params(params)
            
            # Call all registered callbacks
            for callback in self.message_callbacks:
                try:
                    callback(message_data)
                except Exception as e:
                    self.log_error("Error in message callback", error=str(e))
                    
            self.log_info(
                "Processed transcription turn",
                text_length=len(event.transcript),
                end_of_turn=event.end_of_turn
            )
                    
        except Exception as e:
            self.log_error("Error processing turn event", error=str(e))
    
    def _on_terminated(self, event: TerminationEvent):
        """Handle session termination event"""
        self.is_connected = False
        self.log_info(
            "Assembly AI v3 session terminated",
            session_id=self.session_id,
            audio_duration_seconds=event.audio_duration_seconds
        )
    
    def _on_error(self, error: StreamingError):
        """Handle streaming errors"""
        error_message = f"Assembly AI v3 streaming error: {error}"
        self.log_error("Assembly AI v3 streaming error", error=error_message)
        
        # Call all registered error callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.log_error("Error in error callback", error=str(e))
    
    def _determine_speaker(self, event: TurnEvent) -> str:
        """Determine speaker from turn event"""
        # Assembly AI v3 doesn't provide speaker diarization by default in turns
        # This would need to be implemented based on your specific requirements
        # For now, we'll alternate or use a simple heuristic
        
        # You could implement speaker detection logic here based on:
        # - Audio channel (if using dual channel)
        # - Voice characteristics
        # - External speaker detection
        
        # Simple alternating logic (replace with actual speaker detection)
        return "customer"  # Default to customer for now
    
    async def create_batch_transcription(
        self, 
        audio_file_path: str, 
        language: str = "en",
        speaker_diarization: bool = True
    ) -> Dict[str, Any]:
        """Create batch transcription for audio file (using standard API)"""
        try:
            # Use standard Assembly AI for batch processing
            config = aai.TranscriptionConfig(
                language_code=language,
                speaker_labels=speaker_diarization,
                sentiment_analysis=True,
                content_safety=False,
                punctuate=True,
                format_text=True
            )
            
            transcriber = aai.Transcriber()
            transcript = await asyncio.to_thread(
                transcriber.transcribe, 
                audio_file_path, 
                config
            )
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Batch transcription failed: {transcript.error}")
            
            return {
                "text": transcript.text,
                "confidence": transcript.confidence,
                "utterances": [
                    {
                        "text": utterance.text,
                        "confidence": utterance.confidence,
                        "start": utterance.start,
                        "end": utterance.end,
                        "speaker": utterance.speaker,
                        "words": [
                            {
                                "text": word.text,
                                "confidence": word.confidence,
                                "start": word.start,
                                "end": word.end,
                                "speaker": word.speaker
                            }
                            for word in utterance.words
                        ] if utterance.words else []
                    }
                    for utterance in (transcript.utterances or [])
                ]
            }
            
        except Exception as e:
            self.log_error("Batch transcription failed", error=str(e))
            raise
    
    def is_service_available(self) -> bool:
        """Check if Assembly AI service is available"""
        return bool(self.api_key)
    
    async def test_connection(self) -> bool:
        """Test Assembly AI connection"""
        try:
            # Simple connection test
            await self.connect()
            await self.disconnect()
            return True
        except Exception as e:
            self.log_error("Assembly AI connection test failed", error=str(e))
            return False


# Usage example (for testing)
async def test_microphone_streaming():
    """Test microphone streaming with Assembly AI v3"""
    service = AssemblyAIV3Service()
    
    def on_message(data):
        print(f"Transcription: {data['text']} (Final: {data['is_final']})")
    
    def on_error(error):
        print(f"Error: {error}")
    
    service.add_message_callback(on_message)
    service.add_error_callback(on_error)
    
    try:
        await service.connect()
        print("Starting microphone streaming... (Press Ctrl+C to stop)")
        await service.stream_microphone()
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await service.disconnect()


if __name__ == "__main__":
    # Test the service
    asyncio.run(test_microphone_streaming()) 