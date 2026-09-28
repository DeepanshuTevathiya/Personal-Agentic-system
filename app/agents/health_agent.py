from langchain.agents import create_agent
from app.graph.routing import get_llm
from app.tools.health_tools import log_workout

# Need to modify
def get_health_agent():
    llm = get_llm()

    health_agent = llm.bind_tools([log_workout])
    return health_agent