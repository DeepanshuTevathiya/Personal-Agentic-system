from app.graph.state import AssistantState
from langchain_groq import ChatGroq
from laya import Router

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import Literal
from functools import lru_cache

from dotenv import load_dotenv
load_dotenv()

@lru_cache(maxsize=1)
def get_llm():
      return ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,
            max_tokens=300,
            reasoning_effort="low",
            # reasoning_format="hidden",
            max_retries=2,
            )

request_router = Router()

ROUTING_QUESTIONS = {
    "request_type": {
        "type": "choice",
        "instructions": (
            "Route by what the user wants Nexus to do. The requested "
            "action has higher priority than the topic. A habit, routine, "
            "reminder, plan, task, or goal is productivity even when it "
            "mentions exercise, food, water, sleep, or wellness. Choose "
            "both only when two separate actions are requested."
        ),
        "criteria": {
            "health": (
                "Choose only when the user wants to log, retrieve, review, "
                "or receive guidance about a health fact. Health facts are "
                "workouts already done, meals already eaten, sleep already "
                "completed, recovery, nutrition, or health history. Do not "
                "choose health for creating habits, routines, reminders, "
                "tasks, plans, or goals."
            ),
            "productivity": (
                "Choose when the user wants to create, start, change, "
                "schedule, complete, or review a habit, routine, reminder, "
                "task, plan, goal, project, or reflection. This rule "
                "overrides the topic. Example: create a daily habit of "
                "walking for 30 minutes is productivity, not health."
            ),
            "both": (
                "Choose only when the request needs one health action and "
                "one productivity action. Example: log today's 30 minute "
                "walk and create a daily walking habit. A health related "
                "habit alone is not both."
            ),
        },
    },
}

def laya_route(user_message: str) -> tuple[str, dict[str, float], float]:
    result = request_router.predict(
        {"user_message": user_message},
        ROUTING_QUESTIONS,
    )

    answer = result["answers"]["request_type"]
    probabilities = answer["probabilities"]

    ranked = sorted(
        probabilities.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    top_label, top_score = ranked[0]
    second_label, second_score = ranked[1]
    margin = top_score - second_score

    print("USER MESSAGE:", user_message)
    print("ROUTING PROBABILITIES:", probabilities)
    print("TOP RESULT:", top_label)
    print("SECOND RESULT:", second_label)
    print("MARGIN:", margin)

    return top_label, probabilities, margin

class RequestType(BaseModel):
        request_type: Literal["health", "productivity", "both"] = Field(description="Type of user query")

def groq_route(user_message: str) -> Literal["health", "productivity", "both"]:
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

    result = (classifier_prompt | llm).invoke({
        "user_message": user_message,
    })

    print("===========================================================================================")
    print("USER MESSAGE:", user_message)
    print("CLASSIFIER RESULT:", result)
    print("===========================================================================================")
    return result.request_type # type: ignore

def route(state: AssistantState) -> Literal[
    "health",
    "productivity",
    "both",
]:
    user_message = str(state.messages[-1].content)

    laya_type, probabilities, margin = laya_route(user_message)

    if margin < 0.10:
        request_type = groq_route(user_message)
        print("Laya margin is below 0.10")
        print("Groq fallback result:", request_type)
    else:
        request_type = laya_type
        print("Laya result accepted:", request_type)

    if request_type not in {"health", "productivity", "both"}:
        raise ValueError(f"Unexpected request type: {request_type}")

    return request_type #type: ignore