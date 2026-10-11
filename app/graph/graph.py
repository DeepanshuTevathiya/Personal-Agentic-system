from langgraph.graph import StateGraph, START, END
from rich import print

from app.graph.state import AssistantState
from langchain_core.messages import HumanMessage
from app.graph.node import (
    route_node,
    health_wrapper,
    productivity_wrapper,
    reset_results,
    finalize_single_domain,
    synthesis_node
)
# from dotenv import load_dotenv
# load_dotenv()

def route_after_classification(state: AssistantState):
    if state.request_type in {"health", "productivity", "both"}:
        return state.request_type

    raise ValueError(f"Invalid request type: {state.request_type!r}")


def dispatch_both(state: AssistantState):
    return {}

def build_assist_graph():
    graph = StateGraph(AssistantState)

    graph.add_node("reset", reset_results)
    graph.add_node("route", route_node)
    graph.add_node("health", health_wrapper)
    graph.add_node("productivity", productivity_wrapper)
    graph.add_node("dispatch_both", dispatch_both)
    graph.add_node("health_both", health_wrapper)
    graph.add_node("productivity_both", productivity_wrapper)
    graph.add_node("finalize", finalize_single_domain)
    graph.add_node("synthesis", synthesis_node)

    graph.add_edge(START, "reset")
    graph.add_edge("reset", "route")

    graph.add_conditional_edges(
        "route",
        route_after_classification,
        {
            "health": "health",
            "productivity": "productivity",
            "both": "dispatch_both",
        }
    )

    graph.add_edge("health", "finalize")
    graph.add_edge("productivity", "finalize")

    graph.add_edge("dispatch_both", "health_both")
    graph.add_edge("dispatch_both", "productivity_both")

    graph.add_edge(
        ["health_both", "productivity_both"],  #wait for both nodes response
        "synthesis"
    )

    graph.add_edge("finalize", END)
    graph.add_edge("synthesis", END)

    return graph.compile()

graph = build_assist_graph()

config = {"configurable":{"thread_id":"1"}}
state = graph.invoke(
    AssistantState(
        user_id=1,
        messages=[
            HumanMessage(content="""working on my new project cheif of staff, deadline: 17/10/2026, priority high""")
        ]
    ),
    config=config # type: ignore
)

print(state)