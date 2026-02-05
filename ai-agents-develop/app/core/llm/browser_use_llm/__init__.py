from typing import Literal, Optional, Union

from browser_use.llm import ChatGoogle, ChatOpenAI

from app.core.llm.browser_use_llm.gemini_model import get_browser_use_gemini_llm
from app.core.llm.browser_use_llm.openai_model import get_browser_use_openai_llm


def get_browser_use_llm(
    provider: Literal["openai", "gemini"], model_name: Optional[str] = None
) -> Union[ChatOpenAI, ChatGoogle]:
    """
    Generic LLM generator that allows you to choose the provider.

    Args:
        provider: The LLM provider to use ("openai" or "gemini")
        model_name: Optional model name. If not provided, uses default for the provider.

    Returns:
        The configured LLM instance for the specified provider.

    Raises:
        ValueError: If an unsupported provider is specified.
    """
    if provider == "openai":
        return (
            get_browser_use_openai_llm()
            if model_name is None
            else get_browser_use_openai_llm(model_name=model_name)
        )
    elif provider == "gemini":
        return (
            get_browser_use_gemini_llm()
            if model_name is None
            else get_browser_use_gemini_llm(model_name=model_name)
        )
    raise ValueError(
        f"Unsupported provider: {provider}. Supported providers are 'openai' and 'gemini'."
    )


# Export the main function and individual provider functions
__all__ = [
    "get_browser_use_llm",
    "get_browser_use_openai_llm",
    "get_browser_use_gemini_llm",
]
