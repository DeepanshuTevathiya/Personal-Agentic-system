from app.graph.state import AssistantState
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import Literal

from dotenv import load_dotenv
load_dotenv()

def get_llm():
      return ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,
            max_tokens=900
            )

class RequestType(BaseModel):
        request_type: Literal["health", "productivity", "both"] = Field(description="Type of user query")

def route(state :AssistantState):
    llm = get_llm().with_structured_output(RequestType, method="json_mode")

    classifier_prompt = ChatPromptTemplate.from_messages([
          ("system", """You are a request router for a personal assistant.
            Classify the user's request into exactly one category:

            - **health** → requests about workouts, exercise, meals, food, sleep, or other health-related activities.
            - **productivity** → requests about tasks, habits, goals, planning, reminders, or productivity.
            - **both** → requests that clearly involve both health and productivity.

            Classify based on **what the user wants to do**, not just the words used in the request.

            For example:
            - Creating an exercise habit → productivity
            - Logging a workout → health
            - Creating a meal plan → health
            - Creating a habit to drink more water → productivity
            - Creating an exercise habit and logging today's workout → both

            Respond in JSON with a single key:
            "request_type": "health" | "productivity" | "both" """),

          ("human", "{user_message}")
    ])

    chain = classifier_prompt | llm 
    result = chain.invoke({          
        "user_message": state.messages[-1].content
    })
    print("===========================================================================================")
    print("USER MESSAGE:", state.messages[-1].content)
    print("CLASSIFIER RESULT:", result)
    print("===========================================================================================")
    return result.request_type