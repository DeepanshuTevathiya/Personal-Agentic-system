from langchain.agents import create_agent
from app.graph.routing import get_llm
from langchain_core.messages import SystemMessage
from app.tools.health_tools import log_workout, log_meal, log_sleep, retrieve_health_data

HEALTH_SYSTEM_PROMPT = SystemMessage(content="""
You are the Health Agent of a personal assistant.

Your responsibilities are limited to health:
- Workouts and physical activity
- Meals and nutrition
- Sleep and recovery
- Retrieving health history

Use only health tools and health records.
Do not analyze tasks, assignments, habits, or productivity.
If the user asks about both health and productivity, answer only
the health part.

Base conclusions on retrieved records and information explicitly
provided by the user. Do not invent missing data.
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