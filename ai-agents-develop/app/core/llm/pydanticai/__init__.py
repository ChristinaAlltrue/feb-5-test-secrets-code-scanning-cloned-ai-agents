from typing import Literal, Optional, Union

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel

from app.core.llm.pydanticai.gemini_model import get_pydanticai_gemini_llm
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


def get_pydanticai_llm(
    provider: Literal["openai", "gemini"], model_name: Optional[str] = None
) -> Union[OpenAIModel, GoogleModel]:
    """
    Generic PydanticAI LLM generator that allows you to choose the provider.

    Args:
        provider: The LLM provider to use ("openai" or "gemini")
        model_name: Optional model name. If not provided, uses default for the provider.

    Returns:
        The configured PydanticAI model instance for the specified provider.

    Raises:
        ValueError: If an unsupported provider is specified.
    """
    if provider == "openai":
        return (
            get_pydanticai_openai_llm()
            if model_name is None
            else get_pydanticai_openai_llm(model_name=model_name)
        )
    elif provider == "gemini":
        return (
            get_pydanticai_gemini_llm()
            if model_name is None
            else get_pydanticai_gemini_llm(model_name=model_name)
        )
    raise ValueError(
        f"Unsupported provider: {provider}. Supported providers are 'openai' and 'gemini'."
    )


# Export the main function and individual provider functions
__all__ = [
    "get_pydanticai_llm",
    "get_pydanticai_openai_llm",
    "get_pydanticai_gemini_llm",
]
