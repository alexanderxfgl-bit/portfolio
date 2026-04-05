# AI Chatbot Engine

A production-ready conversational AI engine with multi-provider LLM support, conversation memory, tool-use capabilities, and a clean REST API.

## Features

- **Multi-provider LLM support**: OpenAI, Anthropic, Google Gemini, and local models via LiteLLM
- **Conversation memory**: Persistent thread-based conversation history with SQLite
- **Tool/Function calling**: Extensible plugin system for connecting bots to external APIs
- **REST API**: FastAPI-based server with streaming support (SSE)
- **Rate limiting & auth**: JWT-based authentication with per-user rate limits
- **Webhook integrations**: Slack, Discord, and custom webhook support

## Tech Stack

Python 3.11+, FastAPI, SQLAlchemy, LiteLLM, Pydantic, python-jose

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn main:app --reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat` | Send a message and get a response |
| GET | `/api/v1/threads` | List conversation threads |
| GET | `/api/v1/threads/{id}/messages` | Get thread history |
| POST | `/api/v1/threads/{id}/stream` | Stream responses via SSE |
| POST | `/api/v1/tools` | Register a new tool/plugin |

## Example Usage

```python
import requests

# Send a message
resp = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "What's the weather in London?",
    "thread_id": "optional-thread-id",
    "provider": "openai",
    "model": "gpt-4o"
})

print(resp.json()["response"])
```

## Project Structure

```
ai-chatbot-engine/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── models/              # SQLAlchemy models
│   ├── thread.py
│   └── message.py
├── services/
│   ├── llm.py           # Multi-provider LLM client
│   ├── memory.py        # Conversation memory manager
│   └── tools.py         # Tool/function calling system
├── routes/
│   ├── chat.py          # Chat endpoints
│   └── auth.py          # Authentication endpoints
├── plugins/             # Built-in integrations
│   ├── slack.py
│   └── discord.py
├── requirements.txt
├── .env.example
├── README.md
└── tests/
    └── test_chat.py
```

## License

MIT
