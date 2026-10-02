from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from rich import print

from app.graph.state import AssistantState
from langchain_core.messages import HumanMessage
from app.graph.node import route_node, health_node, should_continue
from app.tools.health_tools import log_workout, log_meal, log_sleep, retrieve_health_data
from app.tools.productivity_tools import habit_tool

from dotenv import load_dotenv
load_dotenv()

def build_assit_graph():
    graph = StateGraph(AssistantState)

    graph.add_node("route", route_node)
    graph.add_node("health", health_node) # generate tool call msg from user msg.
    graph.add_node("tools", ToolNode([
        log_workout,
        log_meal,
        log_sleep,
        retrieve_health_data
        ])
    ) #-> LOGs IN DB

    graph.add_edge(START, "route")
    graph.add_edge("route", "health")
    graph.add_conditional_edges(
        "health",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    graph.add_edge("tools", "health")

    return graph.compile()


graph = build_assit_graph()

config = {"configurable":{"thread_id":"1"}}
state = graph.invoke(
    AssistantState(
        user_id=1,
        messages=[
            HumanMessage(content="Slept 7 hr today")
        ]
    ),
    config=config
)

print(state)