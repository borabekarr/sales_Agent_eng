import asyncio
import json
import websockets
from typing import Optional, Callable, Dict, Any
import assemblyai as aai
from utils.config import get_settings
from utils.logging import LoggerMixin


class AssemblyAIService(LoggerMixin):
    """Service for Assembly AI real-time speech processing"""
    
    def __init__(self):
        self.settings = get_settings()
        # Use the provided Assembly AI API key
        self.api_key = "d62ad71a6cf54e02ac000e8c4920819f"
        aai.settings.api_key = self.api_key
        self.transcriber = None
        self.websocket = None
        self.is_connected = False
        self.message_callbacks = []
        self.error_callbacks = []
        
    async def connect(self, language: str = "en", speaker_diarization: bool = True):
        """Connect to Assembly AI real-time transcription service"""
        try:
            # Configure transcription settings
            config = aai.TranscriptionConfig(
                language_code=language,
                punctuate=True,
                format_text=True,
                speaker_labels=speaker_diarization,
                speakers_expected=2 if speaker_diarization else None,
                dual_channel=False,
                speech_threshold=0.5,
                auto_highlights=False,
                sentiment_analysis=True,
                content_safety=False
            )
            
            # Create transcriber
            self.transcriber = aai.RealtimeTranscriber(
                sample_rate=16000,
                on_data=self._on_data,
                on_error=self._on_error,
                on_open=self._on_open,
                on_close=self._on_close,
                end_utterance_silence_threshold=1000,
                disable_partial_transcripts=False
            )
            
            # Connect to Assembly AI
            await asyncio.to_thread(self.transcriber.connect)
            self.is_connected = True
            
            self.log_info(
                "Connected to Assembly AI",
                language=language,
                speaker_diarization=speaker_diarization
            )
            
        except Exception as e:
            self.log_error("Failed to connect to Assembly AI", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Assembly AI service"""
        try:
            if self.transcriber and self.is_connected:
                await asyncio.to_thread(self.transcriber.close)
                self.is_connected = False
                self.log_info("Disconnected from Assembly AI")
        except Exception as e:
            self.log_error("Error disconnecting from Assembly AI", error=str(e))
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data for transcription"""
        if not self.is_connected or not self.transcriber:
            raise RuntimeError("Not connected to Assembly AI")
        
        try:
            await asyncio.to_thread(self.transcriber.stream, audio_data)
        except Exception as e:
            self.log_error("Error sending audio data", error=str(e))
            raise
    
    def add_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for transcription messages"""
        self.message_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Add callback for error handling"""
        self.error_callbacks.append(callback)
    
    def _on_open(self, session_opened: aai.RealtimeSessionOpened):
        """Handle session opened event"""
        self.log_info(
            "Assembly AI session opened",
            session_id=session_opened.session_id
        )
    
    def _on_data(self, transcript: aai.RealtimeTranscript):
        """Handle transcription data"""
        if not transcript.text:
            return
        
        try:
            # Prepare message data
            message_data = {
                "type": "transcription",
                "text": transcript.text,
                "confidence": transcript.confidence if hasattr(transcript, 'confidence') else 0.9,
                "is_final": not isinstance(transcript, aai.RealtimePartialTranscript),
                "timestamp": transcript.created if hasattr(transcript, 'created') else None,
                "speaker": None,
                "raw_data": {
                    "words": [],
                    "sentiment": None
                }
            }
            
            # Add speaker information if available
            if hasattr(transcript, 'words') and transcript.words:
                speakers = set()
                words_data = []
                
                for word in transcript.words:
                    word_data = {
                        "text": word.text,
                        "confidence": word.confidence,
                        "start": word.start,
                        "end": word.end,
                        "speaker": getattr(word, 'speaker', None)
                    }
                    words_data.append(word_data)
                    
                    if hasattr(word, 'speaker') and word.speaker:
                        speakers.add(word.speaker)
                
                message_data["raw_data"]["words"] = words_data
                
                # Determine primary speaker for this transcript
                if speakers:
                    # Use the speaker with the most words in this transcript
                    speaker_counts = {}
                    for word in transcript.words:
                        if hasattr(word, 'speaker') and word.speaker:
                            speaker_counts[word.speaker] = speaker_counts.get(word.speaker, 0) + 1
                    
                    if speaker_counts:
                        primary_speaker = max(speaker_counts, key=speaker_counts.get)
                        # Map speaker labels to roles
                        message_data["speaker"] = "customer" if primary_speaker == "A" else "seller"
            
            # Add sentiment if available
            if hasattr(transcript, 'sentiment') and transcript.sentiment:
                message_data["raw_data"]["sentiment"] = {
                    "sentiment": transcript.sentiment.sentiment,
                    "confidence": transcript.sentiment.confidence
                }
            
            # Call all registered callbacks
            for callback in self.message_callbacks:
                try:
                    callback(message_data)
                except Exception as e:
                    self.log_error("Error in message callback", error=str(e))
                    
        except Exception as e:
            self.log_error("Error processing transcription data", error=str(e))
    
    def _on_error(self, error: aai.RealtimeError):
        """Handle transcription errors"""
        error_message = f"Assembly AI error: {error}"
        self.log_error("Assembly AI transcription error", error=error_message)
        
        # Call all registered error callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.log_error("Error in error callback", error=str(e))
    
    def _on_close(self, code: int, reason: str):
        """Handle session close event"""
        self.is_connected = False
        self.log_info(
            "Assembly AI session closed",
            code=code,
            reason=reason
        )
    
    async def create_batch_transcription(
        self, 
        audio_file_path: str, 
        language: str = "en",
        speaker_diarization: bool = True
    ) -> Dict[str, Any]:
        """Create batch transcription for audio file (for testing)"""
        try:
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
                raise Exception(f"Transcription failed: {transcript.error}")
            
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
                ],
                "sentiment_analysis": {
                    "sentiment": transcript.sentiment_analysis.overall_sentiment,
                    "confidence": transcript.sentiment_analysis.overall_confidence,
                    "results": [
                        {
                            "text": result.text,
                            "sentiment": result.sentiment,
                            "confidence": result.confidence,
                            "start": result.start,
                            "end": result.end
                        }
                        for result in transcript.sentiment_analysis.results
                    ]
                } if transcript.sentiment_analysis else None
            }
            
        except Exception as e:
            self.log_error("Batch transcription failed", error=str(e))
            raise
    
    def is_service_available(self) -> bool:
        """Check if Assembly AI service is available"""
        return bool(self.settings.ASSEMBLY_AI_API_KEY and aai.settings.api_key) 