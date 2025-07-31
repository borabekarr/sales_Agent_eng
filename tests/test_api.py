import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from main import app
from models.schemas import SessionCreate


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_services():
    with patch('main.assembly_ai_service') as mock_assembly, \
         patch('main.gemini_api_service') as mock_gemini, \
         patch('main.conversation_service') as mock_conversation:
        
        # Mock Assembly AI service
        mock_assembly.connect = AsyncMock()
        mock_assembly.disconnect = AsyncMock()
        mock_assembly.is_service_available.return_value = True
        
        # Mock Gemini API service
        mock_gemini.generate_suggestion = AsyncMock(return_value={
            "suggestion": "Great question! Let me understand your current situation better.",
            "type": "discovery",
            "confidence": 0.9
        })
        mock_gemini.is_service_available.return_value = True
        
        # Mock conversation service
        mock_conversation.create_session = AsyncMock(return_value="test-session-id")
        mock_conversation.get_session_status = AsyncMock(return_value="active")
        
        yield {
            "assembly": mock_assembly,
            "gemini": mock_gemini,
            "conversation": mock_conversation
        }


class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "active_sessions" in data


class TestSessionManagement:
    def test_start_session(self, client, mock_services):
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe",
            "session_type": "discovery_call"
        }
        
        response = client.post("/start-session", json=session_data)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "active"
        assert data["user_id"] == "test_user"
    
    def test_end_session(self, client, mock_services):
        # First start a session
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Then end it
        response = client.post(f"/end-session/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session ended successfully"
    
    def test_session_status(self, client, mock_services):
        # Start a session first
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Check status
        response = client.get(f"/session-status/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "session_id" in data


class TestConversationManagement:
    def test_get_next_suggestion(self, client, mock_services):
        # Start a session first
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Get suggestion
        response = client.get(f"/next-suggestion/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "suggestion" in data
        assert "type" in data
        assert "confidence" in data
    
    def test_handle_interrupt(self, client, mock_services):
        # Start a session first
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Handle interrupt
        interrupt_data = {
            "interruption_text": "Wait, I have a question",
            "speaker": "customer"
        }
        response = client.post(f"/handle-interrupt/{session_id}", json=interrupt_data)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_conversation_state(self, client, mock_services):
        # Start a session first
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Get conversation state
        response = client.get(f"/conversation-state/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "current_stage" in data
        assert "session_id" in data
    
    def test_advance_stage(self, client, mock_services):
        # Start a session first
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Advance stage
        stage_data = {
            "target_stage": "discovery",
            "reason": "Customer is ready for needs assessment"
        }
        response = client.post(f"/advance-stage/{session_id}", json=stage_data)
        assert response.status_code == 200
        data = response.json()
        assert "current_stage" in data
        assert "message" in data
    
    def test_get_current_stage(self, client, mock_services):
        # Start a session first
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Get current stage
        response = client.get(f"/current-stage/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "current_stage" in data


class TestAnalytics:
    def test_conversation_summary(self, client, mock_services):
        # Start a session first
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Get conversation summary
        response = client.get(f"/conversation-summary/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "key_topics" in data
        assert "overall_sentiment" in data
    
    def test_performance_metrics(self, client, mock_services):
        # Start a session first
        session_data = {
            "user_id": "test_user",
            "customer_name": "John Doe"
        }
        start_response = client.post("/start-session", json=session_data)
        session_id = start_response.json()["session_id"]
        
        # Get performance metrics
        response = client.get(f"/performance-metrics/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "conversation_duration" in data
        assert "engagement_score" in data
        assert "success_probability" in data


class TestErrorHandling:
    def test_nonexistent_session(self, client):
        response = client.get("/session-status/nonexistent-session")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_invalid_session_data(self, client):
        # Missing required fields
        invalid_data = {
            "user_id": "test_user"
            # Missing customer_name
        }
        response = client.post("/start-session", json=invalid_data)
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestWebSocketConnections:
    async def test_websocket_connection_audio(self):
        """Test WebSocket connection for audio streaming"""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            # Start a session first
            session_data = {
                "user_id": "test_user",
                "customer_name": "John Doe"
            }
            start_response = client.post("/start-session", json=session_data)
            session_id = start_response.json()["session_id"]
            
            # Test WebSocket connection (basic connection test)
            with client.websocket_connect(f"/ws/audio/{session_id}") as websocket:
                # WebSocket connected successfully
                assert websocket is not None
    
    async def test_websocket_connection_suggestions(self):
        """Test WebSocket connection for suggestions"""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            # Start a session first
            session_data = {
                "user_id": "test_user",
                "customer_name": "John Doe"
            }
            start_response = client.post("/start-session", json=session_data)
            session_id = start_response.json()["session_id"]
            
            # Test WebSocket connection (basic connection test)
            with client.websocket_connect(f"/ws/suggestions/{session_id}") as websocket:
                # WebSocket connected successfully
                assert websocket is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 