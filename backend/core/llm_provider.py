from backend.config.settings import settings
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI


class LLMProvider:

    def __init__(self):

        provider = settings.LLM_PROVIDER.lower()

        if provider == "anthropic":

            self.chat_llm = ChatAnthropic(
                model="claude-3-haiku-20240307",
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.2
            )

            self.summary_llm = self.chat_llm


        elif provider == "openai":

            # 🔥 MAIN CHAT MODEL
            self.chat_llm = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.3
            )

            # 🔥 CHEAP SUMMARY MODEL
            self.summary_llm = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0
            )

        else:
            raise ValueError("Invalid LLM_PROVIDER in .env")

    def get_chat_llm(self):
        return self.chat_llm

    def get_summary_llm(self):
        return self.summary_llm


llm_provider = LLMProvider()