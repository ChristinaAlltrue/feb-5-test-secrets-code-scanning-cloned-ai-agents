from browser_use.llm.google import ChatGoogle

from app.utils.gemini.gemini_secret_key import GEMINI_API_KEY

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def get_browser_use_gemini_llm(model_name: str = DEFAULT_GEMINI_MODEL) -> ChatGoogle:
    if GEMINI_API_KEY is None:
        raise ValueError(
            "GEMINI_API_KEY is not set. Ensure 'ALLTRUE_AGENTS_GEMINI_API_KEY' is configured in the secret manager."
        )
    return ChatGoogle(
        model=model_name,
        api_key=GEMINI_API_KEY,
    )
