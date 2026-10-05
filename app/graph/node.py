from app.graph.state import AssistantState
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from app.graph.routing import route
from app.agents.health_agent import get_health_agent
from app.agents.productivity_agent import get_productivity_agent

def route_node(state: AssistantState):
    state.request_type = route(state)
    return state

def health_node(state: AssistantState):
    health_agent = get_health_agent()
    response = health_agent.invoke(state.messages)

    state.messages.append(response)
    return state

#should call a tool or not?
def should_continue_health(state: AssistantState):
    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"

def productivity_node(state: AssistantState):
    productivity_agent = get_productivity_agent()
    response = productivity_agent.invoke(state.messages)

    state.messages.append(response)
    return state

def should_continue_productivity(state: AssistantState):
    last_message = state.messages[-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"

def synthesis_node(state: AssistantState):
    pass