import json
import asyncio
from typing import Annotated, Literal, Union
from uuid import UUID
from datetime import date


from fastapi import Depends, FastAPI, HTTPException, Query, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from app.services.auth import AuthenticatedUser, get_current_user
from app.graph.graph import build_assist_graph
from app.graph.state import AssistantState
from app.memory.memory import retrieve_memories
from app.services.threads import get_or_create_thread, list_user_threads
from app.memory.memory import store_memory
from app.services.checkpointer import get_checkpointer
from app.database.db import (
    db_habit_tool,
    db_log_meal,
    db_log_sleep,
    db_log_workout,
    db_reflection_tool,
    db_task_tool,
)

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

# Add data directly in db table if mannually filled the data.
class WorkoutLogRequest(BaseModel):
    type: Literal["workout"]
    workout_type: str
    duration_minutes: int | None = None
    calories_burned: int | None = None
    notes: str | None = None
    workout_date: date


class MealLogRequest(BaseModel):
    type: Literal["meal"]
    meal_type: str
    description: str | None = None
    calories: int | None = None
    meal_date: date


class SleepLogRequest(BaseModel):
    type: Literal["sleep"]
    sleep_date: date
    sleep_hours: float
    sleep_quality: str | None = None
    notes: str | None = None


class TaskLogRequest(BaseModel):
    type: Literal["task"]
    title: str
    description: str | None = None
    status: str = "pending"
    priority: str = "medium"
    due_date: date


class HabitLogRequest(BaseModel):
    type: Literal["habit"]
    name: str
    description: str | None = None
    frequency: str
    target_count: int = 1
    current_streak: int = 0
    longest_streak: int = 0
    is_active: bool = True

class ReflectionLogRequest(BaseModel):
    type: Literal["reflection"]
    content: str
    mood: str | None = None
    reflection_date: date

LogRequest = Annotated[
    Union[
        WorkoutLogRequest,
        MealLogRequest,
        SleepLogRequest,
        TaskLogRequest,
        HabitLogRequest,
        ReflectionLogRequest,
    ],
    Field(discriminator="type"),
]

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

@app.post("/logs")
async def create_log(
    payload: LogRequest,
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user)
    ],
):
    user_id = current_user.user_id

    if isinstance(payload, WorkoutLogRequest):
        result = await asyncio.to_thread(
            db_log_workout,
            user_id=user_id,
            workout_type=payload.workout_type,
            workout_duration=payload.duration_minutes,
            calories_burned=payload.calories_burned,
            workout_notes=payload.notes,
            workout_date=payload.workout_date,
        )

    elif isinstance(payload, MealLogRequest):
        result = await asyncio.to_thread(
            db_log_meal,
            user_id=user_id,
            meal_type=payload.meal_type,
            description=payload.description,
            calories=payload.calories,
            meal_date=payload.meal_date,
        )

    elif isinstance(payload, SleepLogRequest):
        result = await asyncio.to_thread(
            db_log_sleep,
            user_id=user_id,
            sleep_date=payload.sleep_date,
            sleep_hours=payload.sleep_hours, #type: ignore
            sleep_quality=payload.sleep_quality,
            notes=payload.notes,
        )

    elif isinstance(payload, TaskLogRequest):
        result = await asyncio.to_thread(
            db_task_tool,
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            due_date=payload.due_date,
        )

    elif isinstance(payload, HabitLogRequest):
        result = await asyncio.to_thread(
            db_habit_tool,
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            frequency=payload.frequency,
            target_count=payload.target_count,
            current_streak=payload.current_streak,
            longest_streak=payload.longest_streak,
            is_active=payload.is_active,
        )

    else:
        result = await asyncio.to_thread(
            db_reflection_tool,
            user_id=user_id,
            content=payload.content,
            mood=payload.mood,
            reflection_date=payload.reflection_date,
        )

    source_type = {
        "workout": "workouts",
        "meal": "meals",
        "sleep": "sleep_logs",
        "task": "tasks",
        "habit": "habits",
        "reflection": "reflections",
    }[payload.type]

    source_id = result[0].get("id") if result else None

    if source_id is not None:
        await asyncio.to_thread(
            store_memory,
            user_id=user_id,
            source_type=source_type,
            source_id=source_id,
            content=json.dumps(
                payload.model_dump(mode="json")
            ),
        )

    return {
        "type": payload.type,
        "data": result,
    }