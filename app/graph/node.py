from app.graph.state import AssistantState
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from app.graph.routing import route, get_llm    
from app.agents.health_agent import get_health_agent
from app.agents.productivity_agent import get_productivity_agent

def route_node(state: AssistantState):
    state.request_type = route(state)
    return state

def health_node(state: AssistantState):
    health_agent = get_health_agent()
    response = health_agent.invoke(state.messages)

    state.messages.append(response)

    if not response.tool_calls:   #need data of final response, not after intermidate tool call 
        state.health_result = response.content

    return state

#should call a tool or not?
def should_continue_health(state: AssistantState):
    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    if state.request_type == "both":
        return "productivity"
    return "end"

def productivity_node(state: AssistantState):
    productivity_agent = get_productivity_agent()
    response = productivity_agent.invoke(state.messages)

    state.messages.append(response)

    if not response.tool_calls:
        state.productivity_result = response.content

    return state

def should_continue_productivity(state: AssistantState):
    last_message = state.messages[-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    if state.request_type == "both":
            return "synthesis"
    return "end"

def synthesis_node(state: AssistantState):
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are a personal chief of staff.

        Combine the health and productivity results into one
        clear, useful response to the user's original request.

        Do not invent information. Use only the results provided by the two agents.
        """),
        ("human", """
        User request: {user_message}
        Health result: {health_result}
        Productivity result: {productivity_result}
        """)
    ])

    chain = prompt | llm
    response = chain.invoke({
        "user_message": state.messages[0].content,
        "health_result": state.health_result,
        "productivity_result": state.productivity_result
    })

    state.final_response = response.content
    return state