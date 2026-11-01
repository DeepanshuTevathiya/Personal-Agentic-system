from app.graph.state import AssistantState
from app.graph.subgraph_state import HealthState, ProductivityState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from app.graph.routing import route, get_llm    
from app.agents.health_agent import get_health_agent, HEALTH_SYSTEM_PROMPT
from app.agents.productivity_agent import get_productivity_agent, PRODUCTIVITY_SYSTEM_PROMPT

from app.graph.history import build_clean_history, build_domain_history
from app.services.output_guard import filter_sensitive_output

def route_node(state: AssistantState):
    request_type = route(state)
    state.request_type = request_type

    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            if "request_type" not in message.additional_kwargs:
                message.additional_kwargs["request_type"] = request_type
            break

    return state

def health_node(state: HealthState):
    health_agent = get_health_agent()
    response = health_agent.invoke([HEALTH_SYSTEM_PROMPT, *state.messages])

    return {"messages": [response]}

#should call a tool or not?
def should_continue_health(state: HealthState):
    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"

def productivity_node(state: ProductivityState):
    productivity_agent = get_productivity_agent()
    response = productivity_agent.invoke([PRODUCTIVITY_SYSTEM_PROMPT, *state.messages])

    return {"messages": [response]}

def should_continue_productivity(state: ProductivityState):
    last_message = state.messages[-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"

def reset_results(state: AssistantState):
    return {
        "health_result": "",
        "productivity_result": "",
        "final_response": "",
    }

def general_node(state: AssistantState):
    user_message = next(
        (
            message
            for message in reversed(state.messages)
            if isinstance(message, HumanMessage)
        ),
        HumanMessage(content=""),
    )

    prompt = SystemMessage(content="""
You are Nexus, a personal Chief of Staff.

Answer general conversation and app capability questions.

Do not retrieve user data.
Do not call tools.
Do not claim that you checked records.
Keep the response friendly and under three short sentences.

When asked what Nexus can do, explain that it can help log and review
health, tasks, habits, and reflections.
""")

    response = get_llm().invoke([prompt, user_message])
    answer = filter_sensitive_output(str(response.content))

    return {
        "final_response": answer,
        "messages": [AIMessage(content=answer)],
    }

def finalize_single_domain(state: AssistantState):
    if state.request_type == "health":
        answer = state.health_result
    else:
        answer = state.productivity_result

    answer = filter_sensitive_output(str(answer))

    return {
        "final_response": answer,
        "messages": [AIMessage(content=answer)],
    }

def synthesis_node(state: AssistantState):
    llm = get_llm()

    # Get the latest user request.
    user_message = next(
        (
            msg.content
            for msg in reversed(state.messages)
            if isinstance(msg, HumanMessage)
        ),
        "",
    )

    prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are Nexus, a personal Chief of Staff.

Answer the user's request using only the Health and Productivity results.

Rules:
• Give the direct answer first.
• Explain the meaning of the result briefly.
• Use clear Markdown headings, bold labels, and short bullet lists.
• Keep Health and Productivity separate.
• Connect them only when supported by evidence.
• Never show raw dictionaries, database rows, tool output, or reasoning.
• Never invent missing information.
• Mention missing data briefly.
• Keep the response concise.
"""),
    ("human", """
    User request: {user_message}
    Health result: {health_result}
    Productivity result: {productivity_result}
    """),
])

    response = (prompt | llm).invoke({
        "user_message": user_message,
        "health_result": state.health_result,
        "productivity_result": state.productivity_result,
    })

    answer = response.content

    # Ensure the final response is text.
    if not isinstance(answer, str):
        answer = str(answer)
        
    answer = filter_sensitive_output(answer)

    return {
        "final_response": answer,
        "messages": [AIMessage(content=answer)],
    }

# Wrappers - Get the current msg, last 4 common msg, last 3 domain specific msg => pass to subgraph

def health_wrapper(state: AssistantState):
    from app.graph.subgraphs import health_subgraph

    current_message = next(
        msg for msg in reversed(state.messages)
        if isinstance(msg, HumanMessage)
    )
    shared_history = build_clean_history(state.messages, max_turns=4) # has current msg also
    domain_history = build_domain_history(state.messages, "health", max_turns=3)

    # Remove the current request from history before combining.
    history = [
        msg for msg in shared_history + domain_history
        if msg is not current_message
    ]
    # history = list(dict.fromkeys(history))
    unique_history = []  # select only unique msgs(not duplicates)
    seen = set()

    for msg in history:
        if id(msg) not in seen:
            unique_history.append(msg)
            seen.add(id(msg))

    history = unique_history
    messages = history + [current_message]

    result = health_subgraph.invoke({
        "messages": messages,
        "user_id": state.user_id,
    }) # type: ignore

    return {"health_result": result["messages"][-1].content}


def productivity_wrapper(state: AssistantState):
    from app.graph.subgraphs import productivity_subgraph
    
    current_message = next(
        msg for msg in reversed(state.messages)
        if isinstance(msg, HumanMessage)
    )
    shared_history = build_clean_history(state.messages, max_turns=4) # has current msg also
    domain_history = build_domain_history(state.messages, "productivity", max_turns=3)

    # Remove the current request from history before combining.
    history = [
        msg for msg in shared_history + domain_history
        if msg is not current_message
    ]
    # history = list(dict.fromkeys(history)) 
    unique_history = []  # select only unique msgs(not duplicates)
    seen = set()

    for msg in history:
        if id(msg) not in seen:
            unique_history.append(msg)
            seen.add(id(msg))

    history = unique_history
    messages = history + [current_message]

    result = productivity_subgraph.invoke({
        "messages": messages,
        "user_id": state.user_id,
    }) # type: ignore

    return {"productivity_result": result["messages"][-1].content}