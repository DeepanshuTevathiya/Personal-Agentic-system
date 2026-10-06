from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel
from typing import Optional, Annotated
from datetime import date
from app.database.db import db_log_workout, db_log_meal, db_log_sleep
from app.memory.memory import retrieve_memories, store_memory

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

    # Saving to memory table
    workout_id = result[0]["id"]

    memory_content = (
         f"Workout: {workout.workout_type}."
         f"Duration: {workout.workout_duration} minutes."
         f"Calories Burnned: {workout.calories_burned}"
         f"Notes: {workout.workout_notes}"
         f"Date: {workout.workout_date}"
    )

    store_memory(
         user_id=user_id,
         source_type="workouts",
         source_id=workout_id,
         content=memory_content
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

    #Store in memory
    meal_id = result[0]["id"]

    memory_content = (
         f"Meal: {meal.meal_type}. "
         f"Description: {meal.meal_description}. "
         f"Calories: {meal.calories_gain}. "
         f"Date: {meal.meal_date}."
     )

    store_memory(
         user_id=user_id,
         source_type="meals",
         source_id=meal_id,
         content=memory_content
     )

    return{
         "status": "success",
         "message": "Meal Logged Successfully",
         "data": result
    }



#SLEEP TOOL ----------------------------------------------------------------------------------
class SleepInput(BaseModel):
     sleep_date: Optional[date] = None
     sleep_hour: int
     sleep_quality: Optional[str] = None
     notes: Optional[str] = None

@tool
def log_sleep(
     sleep: SleepInput,
     user_id: Annotated[int, InjectedState("user_id")]
):
    """Log sleep info in database."""
    sleep.sleep_date = sleep.sleep_date or date.today()

    result =  db_log_sleep(
         user_id = user_id,
         sleep_date = sleep.sleep_date,
         sleep_hours = sleep.sleep_hour,
         sleep_quality = sleep.sleep_quality,
         notes = sleep.notes
    )

    # Store in memory
    sleep_id = result[0]["id"]

    memory_content = (
        f"Sleep: {sleep.sleep_hour} hours. "
        f"Quality: {sleep.sleep_quality}. "
        f"Notes: {sleep.notes}. "
        f"Date: {sleep.sleep_date}."
     )

    store_memory(
         user_id=user_id,
         source_type="sleep_logs",
         source_id=sleep_id,
         content=memory_content
     )

    return {
         "state": "success",
         "message": "Sleep Loged Successfully",
         "data": result
    }

# RETRIVLE
# EXPOSING RETRIEVE DATA TO THE HEALTH AGENT---------------------------------------------------

@tool
def retrieve_health_data(
    query: str,
    user_id: Annotated[int, InjectedState("user_id")]
):
    """Retrieve relevant health data from memory."""
    result = retrieve_memories(
        user_id=user_id,
        query=query,
        top_k=5,
        source_types=["workouts", "meals", "sleep_logs"]
    )

    return {
        "status": "success",
        "data": result
    }

