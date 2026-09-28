from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WorkoutInput(BaseModel):
     workout_type: str
     workout_duration: Optional[int] = None
     calories_burned: Optional[int] = None
     workout_notes: Optional[str] = None
     workout_date: Optional[datetime] = None

@tool
def log_workout(user_id: int, workout: WorkoutInput):
    """Log Workout session in database."""
    workout.workout_date = workout.workout_date or datetime.now()

    #TODO: db
    
    return{
        "status": "success",
        "message": "workout logged successfully."
    }

@tool
def log_meal():
    "Log meal in database."

@tool
def log_sleep():
    "Log sleep in database."

@tool
def retrieve_health_data():
    "Retrieve healtyh data from database."