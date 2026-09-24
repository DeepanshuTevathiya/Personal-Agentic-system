from state  import AssistantState
from routing import route

def route_node(state: AssistantState):
    state.request_type = route(state)
    return state

def health_node(state: AssistantState):
    pass

def productivity_node(state: AssistantState):
    pass

def synthesis_node(state: AssistantState):
    pass