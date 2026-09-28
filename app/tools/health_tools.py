from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database.db import db_log_workout

#WORKOUT TOOL ----------------------------------------------------------------------------------
class WorkoutInput(BaseModel):
     workout_type: str
     workout_duration: Optional[int] = None
     calories_burned: Optional[int] = None
     workout_notes: Optional[str] = None
     workout_date: Optional[date] = None

@tool
def log_workout(user_id: int, workout: WorkoutInput):
    """Log Workout session in database."""
    workout.workout_date = workout.workout_date or date.today()

    result = db_log_workout(
        user_id =  user_id,
        workout_type = workout.workout_type,
        workout_duration = workout.workout_duration,
        calories_burned = workout.calories_burned,
        workout_notes = workout.workout_notes,
        workout_date = workout.workout_date
    )
    
    return{
        "status": "success",
        "message": "workout logged successfully.",
        "data": result
    }

#MEAL TOOL ----------------------------------------------------------------------------------
@tool
def log_meal():
    "Log meal in database."

#SLEEP TOOL ----------------------------------------------------------------------------------
@tool
def log_sleep():
    "Log sleep in database."


@tool
def retrieve_health_data():
    "Retrieve healtyh data from database."