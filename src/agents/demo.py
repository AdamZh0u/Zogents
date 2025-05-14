from agno.agent import Agent
from agno.models.openai.responses import OpenAIResponses


from src.config import CONFIG

model = OpenAIResponses(
    id="gpt-4o",
    api_key=CONFIG["openai"]["api_key"],
)

agent = Agent(
    model=model,
    add_state_in_messages=False,
    # monitoring=True,
)

agent.print_response("Add milk, eggs, and bread to the shopping list", stream=True)

print(agent.session_state)
