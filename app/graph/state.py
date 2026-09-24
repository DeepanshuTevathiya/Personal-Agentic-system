from pydantic import BaseModel, Field
from typing import Literal, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
class AssistantState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)
    user_id: int

    request_type: Literal["health", "productivity", "both"] | None=None

    health_result: str = ""
    productivity_result: str = ""

    final_response: str = ""