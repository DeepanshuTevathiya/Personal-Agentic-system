from pydantic import BaseModel, Field
from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class DomainState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)
    user_id: int

class HealthState(DomainState):
    pass

class ProductivityState(DomainState):
    pass