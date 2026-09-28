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
        "workout_date": workout_date
    }

    result = supabase.table("workouts").insert(data).execute()

    return result.data