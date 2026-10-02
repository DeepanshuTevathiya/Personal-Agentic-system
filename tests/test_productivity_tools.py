from app.tools.productivity_tools import habit_tool

result = habit_tool.invoke({
    "habit": {
        "habit_name": "Morning Exercise",
        "habit_description": "Exercise every morning",
        "habit_frequency": "daily",
        "target_count": 1
    },
    "user_id": 1
})

print(result)