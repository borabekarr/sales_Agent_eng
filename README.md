# Real-time AI Sales Assistant Backend

A sophisticated real-time AI-powered sales conversation assistant that provides live suggestions and guidance to sales representatives during customer calls. Built with FastAPI, Assembly AI for speech processing, and Google Gemini AI for intelligent conversation analysis.

## 🚀 Features

### Real-time Processing
- **Live Audio Transcription**: Real-time speech-to-text with speaker diarization
- **Instant AI Suggestions**: Context-aware recommendations during conversations
- **WebSocket Connections**: Bidirectional real-time communication
- **Multi-language Support**: English and Turkish language processing

### AI-Powered Intelligence  
- **Multi-Agent System**: Specialized agents for different sales stages
- **Conversation Analysis**: Deep understanding of customer intent and sentiment
- **Dynamic Stage Management**: Automatic progression through sales funnel
- **Contextual Responses**: Personalized suggestions based on conversation history

### Sales Optimization
- **Stage-Based Guidance**: Opening, Discovery, Pitch, Objection, Closing
- **Customer Profiling**: Real-time customer insights and pain point identification
- **Objection Handling**: Intelligent response suggestions for common concerns
- **Performance Analytics**: Conversation quality metrics and success tracking

## 🏗️ Architecture

### Core Services
- **Assembly AI Service**: Real-time speech-to-text with speaker diarization
- **Gemini AI Service**: Advanced conversation analysis with Gemini 2.5 Pro and Flash models
- **Conversation Service**: State management and analytics
- **WebSocket Manager**: Real-time bidirectional communication

### Specialized Agents
- **Conversation Orchestrator**: Main controller using Gemini 2.5 Pro
- **Opening Agent**: Rapport building and conversation initiation
- **Discovery Agent**: Needs assessment and qualification
- **Pitch Agent**: Solution presentation and value proposition
- **Objection Agent**: Concern handling and confidence building
- **Closing Agent**: Deal finalization and next steps
- **Interrupt Agent**: Flow recovery and topic management

## 🛠️ Requirements

- Python 3.11+
- Assembly AI API Key  
- Google Gemini API Key
- FastAPI
- WebSocket support
- Docker (optional)

## 🚀 Installation

### 1. Clone and Setup

```bash
git clone <repository>
cd sales-assistant-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the environment template:
```bash
cp env_template.txt .env
nano .env
```

Required environment variables:
```env
ASSEMBLY_AI_API_KEY=d62ad71a6cf54e02ac000e8c4920819f
GEMINI_API_KEY=AIzaSyCQkgYAsflx3ITD4_8XljNOhO2QxxoH52k
ENVIRONMENT=development
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. API Keys (Pre-configured)

**Assembly AI API Key:**
- Pre-configured: `d62ad71a6cf54e02ac000e8c4920819f`
- Ready for immediate use

**Google Gemini API Key:**
- Pre-configured: `AIzaSyCQkgYAsflx3ITD4_8XljNOhO2QxxoH52k`
- Ready for immediate use

## 🎮 Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **WebSocket Audio**: ws://localhost:8000/ws/audio/{session_id}
- **WebSocket Suggestions**: ws://localhost:8000/ws/suggestions/{session_id}

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

```bash
# Build the image
docker build -t sales-assistant-backend .

# Run with Docker
docker run -p 8000:8000 --env-file .env sales-assistant-backend

# Or use Docker Compose
docker-compose up -d
```

## 📡 API Endpoints

### Session Management
- `POST /start-session` - Start new conversation session
- `POST /end-session/{session_id}` - End conversation session
- `GET /session-status/{session_id}` - Get session status

### Conversation Management
- `GET /next-suggestion/{session_id}` - Get AI suggestion for next response
- `POST /handle-interrupt/{session_id}` - Handle conversation interruption
- `GET /conversation-state/{session_id}` - Get current conversation state
- `POST /advance-stage/{session_id}` - Manually advance sales stage
- `GET /current-stage/{session_id}` - Get current sales stage

### Analytics
- `GET /conversation-summary/{session_id}` - Get conversation summary
- `GET /performance-metrics/{session_id}` - Get performance metrics

### WebSocket Connections
- `ws://localhost:8000/ws/audio/{session_id}` - Real-time audio streaming
- `ws://localhost:8000/ws/suggestions/{session_id}` - Real-time AI suggestions

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api.py -v

# Test Gemini integration
python test_gemini_integration.py
```

### Test Coverage

The test suite includes:
- API endpoint testing
- WebSocket connection testing
- Service integration testing
- Error handling validation
- Mock service testing

## 🚀 Railway Deployment

### Automatic Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Deploy
railway up
```

### Manual Deployment

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on git push

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ASSEMBLY_AI_API_KEY` | Assembly AI API key | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `MAX_REQUESTS_PER_MINUTE` | Rate limiting | `60` |
| `MAX_CONCURRENT_SESSIONS` | Session limit | `10` |

### Customization

- **Agent Behavior**: Modify agent prompts in `agents/` directory
- **Sales Stages**: Customize stage logic in `services/conversation.py`
- **Response Templates**: Update suggestion templates in agent files
- **Analytics**: Extend metrics in `services/conversation.py`

## 📊 Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# View application logs
tail -f logs/app.log

# Docker logs
docker logs <container_id>

# Railway logs
railway logs
```

### Metrics

- Session success rates
- Response times
- AI suggestion accuracy
- Conversation completion rates

## 🔒 Security

### Best Practices

- **API Keys**: Store in environment variables, never in code
- **CORS**: Configure allowed origins appropriately
- **Rate Limiting**: Implemented for API protection
- **Input Validation**: All inputs validated with Pydantic
- **Error Handling**: Comprehensive error management

### Rate Limiting

- 60 requests per minute per IP
- 10 concurrent sessions maximum
- Configurable via environment variables

## 💡 Usage Examples

### Start a Session

```python
import httpx

# Start session
response = httpx.post("http://localhost:8000/start-session", json={
    "user_id": "sales_rep_1",
    "customer_name": "John Doe",
    "session_type": "discovery_call"
})

session_id = response.json()["session_id"]
```

### Get AI Suggestions

```python
# Get next suggestion
response = httpx.get(f"http://localhost:8000/next-suggestion/{session_id}")
suggestion = response.json()["suggestion"]
```

### WebSocket Connection

```javascript
// Connect to suggestions WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/suggestions/${sessionId}`);

ws.onmessage = (event) => {
    const suggestion = JSON.parse(event.data);
    console.log('AI Suggestion:', suggestion);
};
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Dependencies Issues:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**WebSocket Connection Failed:**
- Check firewall settings
- Verify CORS configuration
- Check network connectivity

**API Rate Limits:**
- Check Gemini API usage
- Verify rate limiting configuration
- Monitor request patterns

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```

## 🚀 Next Steps

1. **Frontend Integration**: Connect with React/Vue.js frontend
2. **Database Integration**: Add PostgreSQL for conversation storage
3. **User Authentication**: Implement JWT-based authentication
4. **Analytics Dashboard**: Build comprehensive analytics interface
5. **Mobile App**: Develop mobile application for field sales
6. **Voice Synthesis**: Add text-to-speech for AI responses
7. **Multi-language**: Expand language support beyond English/Turkish

## 📝 Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## 📄 License

This project is proprietary software. All rights reserved.

---

**Built with ❤️ for sales teams worldwide** 