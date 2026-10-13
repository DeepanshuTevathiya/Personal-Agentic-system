import asyncio
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from app.services.auth import AuthenticatedUser, get_current_user
from app.graph.graph import build_assist_graph
from app.graph.state import AssistantState
from app.memory.memory import retrieve_memories
from app.services.threads import get_or_create_thread, list_user_threads
from app.services.checkpointer import get_checkpointer

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_checkpointer() as checkpointer:
        app.state.graph = build_assist_graph(checkpointer)
        yield


app = FastAPI(
    title="Nexus Personal Chief of Staff",
    lifespan=lifespan,
)

@app.get("/health")
def helth_check():
    return {"status": "ok", "service": "nexus"}

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    thread_id: UUID | None = None

class ChatResponse(BaseModel):
    user_id: int
    thread_id: UUID
    response: str

@app.get("/me")
async def get_me(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]):
    return {
        "user_id": current_user.user_id,
        "auth_id": current_user.auth_id,
        "email": current_user.email
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    fastapi_request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
):
    thread_id = await get_or_create_thread(
        user_id=current_user.user_id,
        thread_id=request.thread_id,
    )

    initial_state = AssistantState(
        user_id=current_user.user_id,
        messages=[HumanMessage(content=request.message)],
    )

    result = await fastapi_request.app.state.graph.ainvoke( #graph with checkpointer(thread ids)
        initial_state,
        config={"configurable": {"thread_id": str(thread_id),}}
    )

    return ChatResponse(
        user_id=current_user.user_id,
        thread_id=thread_id,
        response=result["final_response"],
    )

@app.get("/logs")
async def get_logs(
    current_user: Annotated[AuthenticatedUser,Depends(get_current_user)],
    domain: Literal["health", "productivity"] = Query(),
    query: str = "recent activities",
    limit: int = 5
):
    if not 1<= limit <=20:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 20"
        )

    source_types = {
        "health": ["workouts", "meals", "sleep_logs"],
        "productivity": ["tasks", "habits", "reflections"],
    }

    logs = await asyncio.to_thread(
        retrieve_memories,
        user_id=current_user.user_id,
        query=query,
        top_k=limit,
        source_types=source_types[domain]
    )

    return {
        "user_id": current_user.user_id,
        "domain": domain,
        "logs": logs
    }

# verify thread ownership firstly, then reads the thread saved msg
@app.get("/threads")
async def get_threads(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)] ):
    return {
        "threads": await list_user_threads(current_user.user_id)
    }

@app.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: UUID,
    fastapi_request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
):
    owned_thread_id = await get_or_create_thread(
        user_id=current_user.user_id,
        thread_id=thread_id,
    )

    snapshot = await fastapi_request.app.state.graph.aget_state(
        {"configurable": {"thread_id": str(owned_thread_id),}}
    )

    messages = [
        {
            "role": message.type,
            "content": str(message.content),
        }
        for message in snapshot.values.get("messages", [])
    ]

    return {
        "thread_id": str(owned_thread_id),
        "messages": messages
    }