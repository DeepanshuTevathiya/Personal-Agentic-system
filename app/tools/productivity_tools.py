from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated, Optional
from pydantic import BaseModel
from datetime import date, datetime
from app.database.db import db_habit_tool, db_task_tool, db_complete_task


# === Habit tool ===
class HabitInput(BaseModel):
    habit_name: str
    habit_description: Optional[str] = None
    habit_frequency: str
    target_count: int
    current_streak: int = 0
    longest_streak: int = 0
    is_active: bool = True

@tool
def habit_tool(
        habit: HabitInput,
        user_id: Annotated[int, InjectedState("user_id")]
):
    """Log habit progress in database."""

    result = db_habit_tool(
        user_id = user_id,
        name = habit.habit_name,
        description = habit.habit_description,
        frequency = habit.habit_frequency,
        target_count = habit.target_count,
        current_streak = habit.current_streak,
        longest_streak = habit.longest_streak,
        is_active = habit.is_active
    )

    return {
        "status": "Successfull",
        "data": result
    }

# === Task Tool ===
class task_input(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "low"
    due_date: date

@tool
def task_tool(
    task: task_input,
    user_id: Annotated[int, InjectedState("user_id")]
):
    """Log tasks in database."""
    completed_at = datetime.now().isoformat() if task.status.lower() == "completed" else None

    result = db_task_tool(
        user_id=user_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date
    )

    return {
        "status": "Successfull",
        "message": "Task logged successfully",
        "data": result
    }

# === Update Task ===
@tool
def complete_task(
    user_id: Annotated[int, InjectedState("user_id")],
    task_id: int = 27
):
    """Mark an existing task as completed."""

    result = db_complete_task(
        task_id=task_id,
        user_id=user_id
    )

    return {
        "status": "success",
        "message": "Task completed successfully",
        "data": result
    }