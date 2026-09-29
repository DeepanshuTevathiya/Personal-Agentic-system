from app.tools.health_tools import log_workout, log_meal

#WORKOUT TESTING --------------------------
# workout_result = log_workout.invoke({
#     "user_id" : 1,
#     "workout": {
#          "workout_type": "running",
#         "workout_duration": 30,
#         "calories_burned": 250,
#         "workout_notes": "Morning run"
#     }
# })
# print(workout_result)


#MEAL TESTING --------------------------
meal_result = log_meal.invoke({
    "user_id": 1,
    "meal": {
        "meal_type": "lunch",
        "description": "Chicken and rice",
        "calories": 600,
    }
})
print(meal_result)