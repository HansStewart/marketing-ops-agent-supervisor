from langchain_anthropic import ChatAnthropic
from app.config import settings

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    anthropic_api_key=settings.anthropic_api_key,
    temperature=0.2,
    max_tokens=512,
)