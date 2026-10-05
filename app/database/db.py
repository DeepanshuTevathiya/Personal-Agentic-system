from app.database.config import supabase
from datetime import datetime
#--------------------------------------- HEALTH -----------------------------------------------
# LOG WORKOUT SESSION
def db_log_workout(
        user_id: int,
        workout_type: str,
        workout_duration: int | None,
        calories_burned: int | None,
        workout_notes: str | None,
        workout_date
):
    data = {
        "user_id": user_id,
        "workout_type": workout_type,
        "duration_minutes": workout_duration,
        "calories_burned": calories_burned,
        "notes": workout_notes,
        "workout_date": workout_date.isoformat()
    }

    result = supabase.table("workouts").insert(data).execute()
    return result.data

# LOG MEAL DATA
def db_log_meal(
        user_id: int,
        meal_type: str,
        description: str | None,
        calories: int | None,
        meal_date
):
    data = {
        "user_id": user_id,
        "meal_type": meal_type,
        "description": description,
        "calories": calories,
        "meal_date": meal_date.isoformat()
    }

    result = supabase.table("meals").insert(data).execute()
    return result.data

# LOG SLEEP DATA
def db_log_sleep(
        user_id: int,
        sleep_date,
        sleep_hours: int,
        sleep_quality: str | None,
        notes: str | None
):
    data = {
        "user_id": user_id,
        "sleep_date": sleep_date.isoformat(),
        "sleep_hours": sleep_hours,
        "sleep_quality": sleep_quality,
        "notes": notes
    }

    result = supabase.table("sleep_logs").insert(data).execute()
    return result.data

# STORE EMBEDDING DATA
def db_store_memory(
        user_id: int,
        source_type: str,
        source_id: int,
        content: str,
        embedding: list
):
    data = {
        "user_id": user_id,
        "source_type": source_type,
        "source_id": source_id,
        "content": content,
        "embedding": embedding
    }

    result = supabase.table("memories").insert(data).execute()
    return result.data

#--------------------------------------- PRODUCTIVITY --------------------------------------------

def db_habit_tool(
        user_id: int,
        name: str,
        description: str | None,
        frequency: str,
        target_count: int,
        current_streak: int,
        longest_streak: int,
        is_active: bool
):
    data = {
        "user_id":user_id,
        "name":name,
        "description":description,
        "frequency":frequency,
        "target_count":target_count,
        "current_streak":current_streak,
        "longest_streak":longest_streak,
        "is_active":is_active
    }

    result = supabase.table("habits").insert(data).execute()
    return result.data

# Create task
def db_task_tool(
        user_id: int,
        title: str,
        description: str | None,
        status: str,
        priority: str,
        due_date
):
    data = {
        "user_id": user_id,
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "due_date": due_date.isoformat()
    }

    result = supabase.table("tasks").insert(data).execute()
    return result.data

# Update task
def db_complete_task(task_id: int, user_id: int):
    data = {
        "status": "completed",
        "completed_at": datetime.now().isoformat()
    }

    result = supabase.table("tasks").update(data).eq("id", task_id).eq("user_id", user_id).execute()
    return result.data