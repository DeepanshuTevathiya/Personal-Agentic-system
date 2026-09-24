from state import AssistantState
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
            temperature=0
            )

class RequestType(BaseModel):
        request_type: Literal["health", "productivity", "both"] = Field(description="Type of user query")

def route(state :AssistantState):
    llm = get_llm().with_structured_output(RequestType, method="json_mode")

    classifier_prompt = ChatPromptTemplate.from_messages([
          ("system", """Classify the user's query into exactly one category.
          Respond in JSON with a single key "request_type".
          Allowed values for "request_type": "health", "productivity", "both"."""),

          ("human", "{user_message}")
    ])

    chain = classifier_prompt | llm 
    result = chain.invoke({          
        "user_message": state.messages[-1].content
    })

    return result.request_type