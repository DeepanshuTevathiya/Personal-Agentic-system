from state import AssistantState
from node import route_node
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

def build_assit_graph():
    graph = StateGraph(AssistantState)

    graph.add_node("route", route_node)

    graph.add_edge(START, "route")
    graph.add_edge("route", END)

    graph = graph.compile()
    return graph


graph = build_assit_graph()

config = {"configurable":{"thread_id":"1"}}
state = graph.invoke(
    {
        "user_id": 1,
        "messages": [HumanMessage(content="Show me my sleep pattern")]
    },
    config=config
)

print(state)