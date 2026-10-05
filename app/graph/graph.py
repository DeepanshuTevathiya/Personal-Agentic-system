from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from rich import print

from app.graph.state import AssistantState
from langchain_core.messages import HumanMessage
from app.graph.node import route_node, health_node, should_continue_health, productivity_node, should_continue_productivity
from app.tools.health_tools import log_workout, log_meal, log_sleep, retrieve_health_data
from app.tools.productivity_tools import habit_tool

from dotenv import load_dotenv
load_dotenv()

def build_assit_graph():
    graph = StateGraph(AssistantState)

    graph.add_node("route", route_node)
    graph.add_node("health", health_node) # generate tool call msg from user msg.
    graph.add_node("health_tools", ToolNode([    #-> LOGs IN DB
        log_workout,
        log_meal,
        log_sleep,
        retrieve_health_data
        ])
    )
    graph.add_node("productivity", productivity_node)
    graph.add_node("productivity_tools", ToolNode([
        habit_tool        
        ])
    )


    graph.add_edge(START, "route")
    graph.add_conditional_edges(
        "route",
        lambda state: state.request_type,
        {
            "health": "health",
            "productivity": "productivity",
            # "both": ...
        }
    )

    graph.add_conditional_edges(
        "health",
        should_continue_health,
        {
            "tools": "health_tools",
            "end": END
        }
    )
    graph.add_edge("health_tools", "health")

    graph.add_conditional_edges(
        "productivity",
        should_continue_productivity,
        {
            "tools": "productivity_tools",
            "end": END
        }
    )
    graph.add_edge("productivity_tools", "productivity")

    return graph.compile()


graph = build_assit_graph()

config = {"configurable":{"thread_id":"1"}}
state = graph.invoke(
    AssistantState(
        user_id=1,
        messages=[
            HumanMessage(content="""I want to create a new habit called "Morning Exercise". The habit is to exercise every morning, with a daily frequency and a target of 1 completion per day. The current streak is 0 and the longest streak is 0. Keep the habit active.""")
        ]
    ),
    config=config
)

print(state)