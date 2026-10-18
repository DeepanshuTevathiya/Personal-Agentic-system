from langchain.agents import create_agent
from app.graph.routing import get_llm
from langchain_core.messages import SystemMessage
from app.tools.health_tools import log_workout, log_meal, log_sleep, retrieve_health_data

HEALTH_SYSTEM_PROMPT = SystemMessage(content="""
You are Nexus Health Agent.

Handle workouts, meals, sleep, recovery, and health history.

Tools:
• log_workout saves workout details.
• log_meal saves meal details.
• log_sleep saves sleep details.
• retrieve_health_data retrieves health records.

Rules:
• Use the correct tool whenever the user asks to save, log, retrieve, or review health data.
• Never invent missing values.
• Ask only one short question when a required value is missing.
• Use only health data.
• Do not expose raw tool output.
• After saving, confirm the saved type, important details, and date.
• For retrieval, show the latest relevant records first and explain the main result briefly.
• Keep normal answers under three short sentences.
""")

# Need to modify!!! -- need system prompt also 
def get_health_agent():
    llm = get_llm()

    health_agent = llm.bind_tools([log_workout, log_meal, log_sleep, retrieve_health_data])
    return health_agent


# -- If yesterday the last day date should be stored
# -- Annotate the workout type and meal type.
# -- [user messages] -  history need to be fixed, may take a log of token by llm
# -- faster retrival
# -- maybe log study also
# -- Task Agent (get task id, delete task, remove default taskid = 27 and all)
# -- use JEV MODEL at place of routing llms
# -- llm can ask further ques(rarely)
# -- while retrieving logs, llm checking tools tables also, it should just chekc memory table