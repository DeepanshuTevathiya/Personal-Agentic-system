
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.graph.history import build_clean_history, build_domain_history


# def test_excludes_tool_messages():
#     messages = [
#         HumanMessage(content="Log my workout"),
#         AIMessage(
#             content="",
#             tool_calls=[
#                 {
#                     "name": "log_workout",
#                     "args": {},
#                     "id": "call_1",
#                     "type": "tool_call",
#                 }
#             ],
#         ),
#         ToolMessage(content="Workout logged", tool_call_id="call_1"),
#     ]

#     result = build_clean_history(messages)

#     assert len(result) == 1
#     assert isinstance(result[0], HumanMessage)
#     assert result[0].content == "Log my workout"


# def test_empty_history():
#     assert build_clean_history([]) == []


# def test_message_order():
#     messages = [
#         HumanMessage(content="Old question"),
#         AIMessage(content="Old answer"),
#         HumanMessage(content="Current question"),
#     ]

#     result = build_clean_history(messages)

#     assert [m.content for m in result] == [
#         "Old question",
#         "Old answer",
#         "Current question",
#     ]


# def test_only_current_request():
#     messages = [HumanMessage(content="Current request")]

#     result = build_clean_history(messages)

#     assert len(result) == 1
#     assert result[0].content == "Current request"


# def test_limits_to_three_previous_turns():
#     messages = [
#         HumanMessage(content="Question 1"),
#         AIMessage(content="Answer 1"),
#         HumanMessage(content="Question 2"),
#         AIMessage(content="Answer 2"),
#         HumanMessage(content="Question 3"),
#         AIMessage(content="Answer 3"),
#         HumanMessage(content="Question 4"),
#         AIMessage(content="Answer 4"),
#         HumanMessage(content="Current request"),
#     ]

#     result = build_clean_history(messages)

#     assert [m.content for m in result] == [
#         "Question 2",
#         "Answer 2",
#         "Question 3",
#         "Answer 3",
#         "Question 4",
#         "Answer 4",
#         "Current request",
#     ]


# if __name__ == "__main__":
#     test_excludes_tool_messages()
#     test_empty_history()
#     test_message_order()
#     test_only_current_request()
#     test_limits_to_three_previous_turns()

#     print("All history tests passed!")


#-----------------------------------------------------------------------------------
messages = [
    HumanMessage(
        content="Log my workout",
        additional_kwargs={"request_type": "health"},
    ),
    AIMessage(content="Workout logged."),

    HumanMessage(
        content="Add a task",
        additional_kwargs={"request_type": "productivity"},
    ),
    AIMessage(content="Task added."),

    HumanMessage(
        content="Review my health and tasks",
        additional_kwargs={"request_type": "both"},
    ),
    AIMessage(content="Here is your combined review."),
]

health_history = build_domain_history(messages, "health")
productivity_history = build_domain_history(messages, "productivity")

print("Health history:")
for message in health_history:
    print(type(message).__name__, message.content)

print("\nProductivity history:")
for message in productivity_history:
    print(type(message).__name__, message.content)