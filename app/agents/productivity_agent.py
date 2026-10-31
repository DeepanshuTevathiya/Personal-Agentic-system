from app.graph.routing import get_llm
from app.tools.productivity_tools import habit_tool, task_tool, complete_task,reflection_tool, retrieve_productivity_data
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage

PRODUCTIVITY_SYSTEM_PROMPT = SystemMessage(content="""
You are Nexus Productivity Agent.

Handle tasks, habits, reflections, goals, planning, and productivity history.

Tools:
• task_tool creates tasks.
• complete_task completes an existing task.
• habit_tool creates habits.
• reflection_tool saves reflections.
• retrieve_productivity_data retrieves all productivity history from memories.

Rules:
• Use retrieve_productivity_data for all productivity retrieval.
• To complete a task, retrieve it first and use its source_id as task_id.
• Every new task must have a due date.
• Never invent task IDs or tool results.
""")

def get_productivity_agent():
    llm = get_llm()

    productivity_agent = llm.bind_tools([habit_tool, task_tool, complete_task, reflection_tool, retrieve_productivity_data])
    return productivity_agent

# productivity_agent = productivity_prompt | get_productivity_agent()