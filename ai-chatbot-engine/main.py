"""
AI Chatbot Engine - Multi-provider conversational AI with tool-use capabilities.
"""
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import uuid
import json
from datetime import datetime, timezone

load_dotenv()


# --- Configuration ---
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chatbot.db")
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")


# --- Database ---
engine = create_async_engine(Config.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Thread(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    provider = Column(String, default="openai")
    model = Column(String, default="gpt-4o")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String, ForeignKey("threads.id"), nullable=False)
    role = Column(String, nullable=False)  # "user", "assistant", "system", "tool"
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON-serialized tool call data
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    thread_id: Optional[str] = None
    provider: str = "openai"
    model: str = "gpt-4o"
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    message_id: str
    provider: str
    model: str
    created_at: str


class ThreadResponse(BaseModel):
    id: str
    title: Optional[str]
    provider: str
    model: str
    created_at: str
    updated_at: str


# --- LLM Client ---
class LLMClient:
    """Multi-provider LLM client using LiteLLM for unified interface."""

    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                import litellm
                litellm.suppress_debug_info = True
                self._client = litellm
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="litellm package required. Install with: pip install litellm"
                )
        return self._client

    async def chat(
        self,
        messages: list[dict],
        provider: str = "openai",
        model: str = "gpt-4o",
        temperature: float = 0.7,
        tools: Optional[list] = None,
        stream: bool = False,
    ):
        litellm = await self._get_client()
        model_id = f"{provider}/{model}" if "/" not in model else model

        kwargs = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if tools:
            kwargs["tools"] = tools

        try:
            response = await litellm.acompletion(**kwargs)
            return response
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM provider error: {str(e)}")


# --- Tool System ---
class ToolRegistry:
    """Extensible tool/function calling registry."""

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, parameters: dict, handler):
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }

    def to_openai_schema(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, arguments: dict) -> str:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = self._tools[name]["handler"](**arguments)
            if hasattr(result, "__await__"):
                result = await result
            return json.dumps(result) if not isinstance(result, str) else result
        except Exception as e:
            return json.dumps({"error": str(e)})


tool_registry = ToolRegistry()
llm_client = LLMClient()


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# --- App ---
app = FastAPI(
    title="AI Chatbot Engine",
    description="Multi-provider conversational AI with tool-use capabilities",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Routes ---
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and receive an AI response."""
    async with async_session() as session:
        # Get or create thread
        if request.thread_id:
            thread = await session.get(Thread, request.thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
        else:
            thread = Thread(provider=request.provider, model=request.model)
            session.add(thread)
            await session.commit()
            await session.refresh(thread)

        # Save user message
        user_msg = Message(thread_id=thread.id, role="user", content=request.message)
        session.add(user_msg)
        await session.commit()

        # Build message history
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        result = await session.execute(
            select(Message).where(Message.thread_id == thread.id).order_by(Message.created_at)
        )
        history = result.scalars().all()
        messages.extend([{"role": m.role, "content": m.content} for m in history])

        # Call LLM
        tools_schema = tool_registry.to_openai_schema() or None
        response = await llm_client.chat(
            messages=messages,
            provider=thread.provider,
            model=request.model,
            temperature=request.temperature,
            tools=tools_schema,
        )

        assistant_content = response.choices[0].message.content or ""

        # Save assistant message
        assistant_msg = Message(thread_id=thread.id, role="assistant", content=assistant_content)
        session.add(assistant_msg)
        await session.commit()

        return ChatResponse(
            response=assistant_content,
            thread_id=thread.id,
            message_id=assistant_msg.id,
            provider=thread.provider,
            model=request.model,
            created_at=assistant_msg.created_at.isoformat(),
        )


@app.get("/api/v1/threads", response_model=list[ThreadResponse])
async def list_threads(limit: int = 50, offset: int = 0):
    """List all conversation threads."""
    async with async_session() as session:
        result = await session.execute(
            select(Thread).order_by(Thread.updated_at.desc()).offset(offset).limit(limit)
        )
        threads = result.scalars().all()
        return [
            ThreadResponse(
                id=t.id, title=t.title, provider=t.provider,
                model=t.model, created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
            )
            for t in threads
        ]


@app.get("/api/v1/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    """Get all messages in a thread."""
    async with async_session() as session:
        thread = await session.get(Thread, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        result = await session.execute(
            select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
        )
        messages = result.scalars().all()
        return [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages
        ]


@app.post("/api/v1/tools")
async def register_tool(
    name: str,
    description: str,
    parameters: dict,
):
    """Register a new tool (placeholder — real implementation would accept a handler)."""
    # In production, tools would be registered via plugins or config
    raise HTTPException(
        status_code=501,
        detail="Tool registration via API not yet implemented. Use the plugin system."
    )


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# --- Entry Point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
