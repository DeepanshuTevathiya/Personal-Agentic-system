from app.agents.health_agent import get_health_agent
from langchain_core.messages import HumanMessage

health_agent = get_health_agent()

response = health_agent.invoke([
    HumanMessage(content="I went running for 30 minutes today.")
])

print(response)