from browser_use.llm import ChatOpenAI

from app.utils.chatgpt.openai_secret_key import OPENAI_API_KEY

DEFAULT_OPENAI_MODEL = "gpt-4.1"


def get_browser_use_openai_llm(model_name: str = DEFAULT_OPENAI_MODEL) -> ChatOpenAI:
    if OPENAI_API_KEY is None:
        raise ValueError(
            "OPENAI_API_KEY is not set. Please set it in your environment variables."
        )
    return ChatOpenAI(
        model=model_name,
        api_key=OPENAI_API_KEY,
    )
