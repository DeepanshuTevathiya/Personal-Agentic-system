from app.database.config import supabase

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