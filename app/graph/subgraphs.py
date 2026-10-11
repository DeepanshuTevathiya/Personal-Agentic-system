from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.graph.subgraph_state import HealthState, ProductivityState
from app.graph.node import (
    health_node,
    should_continue_health,
    productivity_node,
    should_continue_productivity
)
from app.tools.health_tools import (
    log_meal,
    log_sleep,
    log_workout,
    retrieve_health_data
)
from app.tools.productivity_tools import (
    habit_tool,
    task_tool,
    complete_task,
    get_tasks,
    reflection_tool,
    retrieve_productivity_data,
)


def build_health_subgraph():
    graph = StateGraph(HealthState)

    graph.add_node("health", health_node)
    graph.add_node(
        "health_tools",
        ToolNode([log_workout, log_sleep, log_meal, retrieve_health_data])
    )

    graph.add_edge(START, "health")
    graph.add_conditional_edges(
        "health",
        should_continue_health,
        {
            "tools": "health_tools",
            "end": END,
        }
    )
    graph.add_edge("health_tools", "health")

    return graph.compile()

def build_productivity_subgraph():
    graph = StateGraph(ProductivityState)

    graph.add_node("productivity", productivity_node)
    graph.add_node(
        "productivity_tools",
        ToolNode([habit_tool, task_tool, complete_task, get_tasks, reflection_tool, retrieve_productivity_data])
    )

    graph.add_edge(START, "productivity")
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

health_subgraph = build_health_subgraph()
productivity_subgraph = build_productivity_subgraph()