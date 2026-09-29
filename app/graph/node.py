from app.graph.state import AssistantState
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from app.graph.routing import route
from app.agents.health_agent import get_health_agent
from app.tools.health_tools import log_workout

def route_node(state: AssistantState):
    state.request_type = route(state)
    return state

def health_node(state: AssistantState):
    health_agent = get_health_agent()
    response = health_agent.invoke(state.messages)

    state.messages.append(response)
    return state

#should call a tool or not?
def should_continue(state: AssistantState):
    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"

# #Tool Node
# tool_node = ToolNode([log_workout])


def productivity_node(state: AssistantState):
    pass

def synthesis_node(state: AssistantState):
    pass