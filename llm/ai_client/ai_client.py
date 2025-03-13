from openai import AsyncOpenAI

from llm.config import get_config

llm_config = get_config()

ai_client = AsyncOpenAI(
    api_key=llm_config.openai_api_key,
    base_url=llm_config.openai_base_url,
)
