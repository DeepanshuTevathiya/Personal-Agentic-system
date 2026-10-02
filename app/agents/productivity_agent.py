from app.graph.routing import get_llm
from app.tools.productivity_tools import habit_tool


def get_productivity_agent():
    llm = get_llm()

    productivity_agent = llm.bind_tools([habit_tool])
    return productivity_agent