from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated, Optional
from pydantic import BaseModel
from datetime import date
from app.database.db import db_habit_tool


# Habit tool

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
