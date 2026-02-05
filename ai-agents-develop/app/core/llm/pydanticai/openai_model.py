from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from app.utils.chatgpt.openai_secret_key import OPENAI_API_KEY

DEFAULT_OPENAI_MODEL = "gpt-5.1"


# gpt-5.1 by defaullt reasoning effort is set to "none"
def get_pydanticai_openai_llm(
    model_name: str = DEFAULT_OPENAI_MODEL, model_kwargs: dict | None = None
) -> OpenAIModel:
    if OPENAI_API_KEY is None:
        raise ValueError(
            "OPENAI_API_KEY is not set. Please set it in your environment variables."
        )
    if model_kwargs is None:
        model_kwargs = {}
    return OpenAIModel(
        model_name=model_name,
        provider=OpenAIProvider(api_key=OPENAI_API_KEY),
        settings=OpenAIModelSettings(
            **{
                "temperature": 0.0,
                **model_kwargs,
            }
        ),
    )
