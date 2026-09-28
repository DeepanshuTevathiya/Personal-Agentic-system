from app.tools.health_tools import log_workout

result = log_workout.invoke({
    "user_id" : 1,
    "workout": {
         "workout_type": "running",
        "workout_duration": 30,
        "calories_burned": 250,
        "workout_notes": "Morning run"
    }
})

print(result)