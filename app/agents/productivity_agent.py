from app.graph.routing import get_llm
from app.tools.productivity_tools import habit_tool, task_tool, complete_task
from langchain_core.prompts import ChatPromptTemplate

productivity_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a productivity assistant.

    When the user wants to create, log, or update a habit,
    you MUST use the habit_tool.

    Do not simply give advice when the user is asking to create a habit.
    """),
        ("placeholder", "{messages}")
    ])

def get_productivity_agent():
    llm = get_llm()

    productivity_agent = llm.bind_tools([habit_tool, task_tool, complete_task])
    return productivity_agent

# productivity_agent = productivity_prompt | get_productivity_agent()