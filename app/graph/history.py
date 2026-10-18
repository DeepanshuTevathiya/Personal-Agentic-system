# to get last 3 history msg 

from langchain_core.messages import AIMessage, HumanMessage

## Get the common conversation history
def build_clean_history(messages, max_turns=4):
    # Find the latest user request.
    current_index = next(
        (
            i
            for i in range(len(messages) - 1, -1, -1)
            if isinstance(messages[i], HumanMessage)
        ),
        None,
    )

    if current_index is None:
        return []

    # Keep only clean messages before the current request.
    previous = []

    for message in messages[:current_index]:
        if isinstance(message, HumanMessage):
            previous.append(message)
        elif isinstance(message, AIMessage) and not message.tool_calls:
            previous.append(message)

    # Keep up to max_turns complete user-assistant pairs.
    turns = []
    i = 0

    while i < len(previous) - 1:
        if (
            isinstance(previous[i], HumanMessage)
            and isinstance(previous[i + 1], AIMessage)
        ):
            turns.append(previous[i:i + 2])
            i += 2
        else:
            i += 1

    recent_turns = turns[-max_turns:] if max_turns > 0 else []
    history = [message for turn in recent_turns for message in turn]

    # Always include the current request last.
    return history + [messages[current_index]]

from langchain_core.messages import AIMessage, HumanMessage


## Get the domain specific conversation history
def build_domain_history(messages, domain: str, max_turns: int = 3):
    turns = []
    current_user_message = None

    for message in messages:
        if isinstance(message, HumanMessage):
            current_user_message = message

        elif isinstance(message, AIMessage) and not message.tool_calls:
            if current_user_message is not None:
                request_type = current_user_message.additional_kwargs.get(
                    "request_type"
                )

                if request_type in (domain, "both"):
                    turns.append([current_user_message, message])

                current_user_message = None

    recent_turns = turns[-max_turns:] if max_turns > 0 else []

    return [
        message
        for turn in recent_turns
        for message in turn
    ]