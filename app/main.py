from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.messages import HumanMessage
from fastapi import HTTPException

from app.graph.graph import graph
from app.memory.memory import retrieve_memories
from app.graph.state import AssistantState

app = FastAPI(title="Nexus — Personal Chief of Staff")

@app.get("/health")
def helth_check():
    return {"status": "ok", "service": "nexus"}

class ChatRequest(BaseModel):
    user_id: int
    message: str = Field(min_length=1)

class ChatResponse(BaseModel):
    user_id: int
    response: str

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    initial_state = AssistantState(
        user_id=request.user_id,
        messages=[HumanMessage(content=request.message)]
    )
    result = graph.invoke(initial_state)

    return ChatResponse(
        user_id=request.user_id,
        response=result["final_response"]
    )

@app.get("/log")
def get_logs(
    user_id: int,
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

    logs = retrieve_memories(
        user_id=user_id,
        query=query,
        top_k=limit,
        source_types=source_types[domain]
    )

    return {
        "user_id": user_id,
        "domain": domain,
        "logs": logs
    }