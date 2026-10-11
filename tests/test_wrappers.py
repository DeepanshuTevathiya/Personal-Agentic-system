from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage

from app.graph.state import AssistantState
from app.graph.node import health_wrapper, productivity_wrapper


def create_state():
    return AssistantState(
        user_id=1,
        messages=[
            HumanMessage(
                content="Log my workout",
                additional_kwargs={"request_type": "health"},
            )
        ],
    )


def test_health_wrapper():
    state = create_state()

    mock_subgraph = MagicMock()
    mock_subgraph.invoke.return_value = {
        "messages": [AIMessage(content="Workout logged.")]
    }

    with patch(
        "app.graph.subgraphs.health_subgraph",
        mock_subgraph,
    ):
        result = health_wrapper(state)

    assert result == {"health_result": "Workout logged."}
    mock_subgraph.invoke.assert_called_once()

    payload = mock_subgraph.invoke.call_args.args[0]
    assert payload["user_id"] == 1
    assert payload["messages"][-1].content == "Log my workout"


def test_productivity_wrapper():
    state = create_state()

    mock_subgraph = MagicMock()
    mock_subgraph.invoke.return_value = {
        "messages": [AIMessage(content="Task added.")]
    }

    with patch(
        "app.graph.subgraphs.productivity_subgraph",
        mock_subgraph,
    ):
        result = productivity_wrapper(state)

    assert result == {"productivity_result": "Task added."}
    mock_subgraph.invoke.assert_called_once()

    payload = mock_subgraph.invoke.call_args.args[0]
    assert payload["user_id"] == 1
    assert payload["messages"][-1].content == "Log my workout"