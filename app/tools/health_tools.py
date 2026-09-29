from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel
from typing import Optional, Annotated
from datetime import date
from app.database.db import db_log_workout, db_log_meal

#WORKOUT TOOL ----------------------------------------------------------------------------------
class WorkoutInput(BaseModel):
     workout_type: str
     workout_duration: Optional[int] = None
     calories_burned: Optional[int] = None
     workout_notes: Optional[str] = None
     workout_date: Optional[date] = None

@tool
def log_workout(
    workout: WorkoutInput,
    user_id: Annotated[int, InjectedState("user_id")]
    ):

    """Log Workout session in database."""
    workout.workout_date = workout.workout_date or date.today()

    #logs in db
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
        "message": "Workout Logged Successfully.",
        "data": result
    }

#MEAL TOOL ----------------------------------------------------------------------------------
class MealInput(BaseModel):
        meal_type: str
        meal_description: Optional[str] = None
        calories_gain: Optional[int] = None
        meal_date: Optional[date] = None

@tool
def log_meal(
     meal: MealInput,
     user_id: Annotated[int, InjectedState("user_id")] 
):
    """Log meal data in database."""
    meal.meal_date = meal.meal_date or date.today()

    result = db_log_meal(
         user_id = user_id,
         meal_type = meal.meal_type,
         description = meal.meal_description,
         calories = meal.calories_gain,
         meal_date = meal.meal_date
    )

    return{
         "status": "success",
         "message": "Meal Logged Successfully",
         "data": result
    }



#SLEEP TOOL ----------------------------------------------------------------------------------
@tool
def log_sleep():
    "Log sleep in database."


@tool
def retrieve_health_data():
    "Retrieve healtyh data from database."