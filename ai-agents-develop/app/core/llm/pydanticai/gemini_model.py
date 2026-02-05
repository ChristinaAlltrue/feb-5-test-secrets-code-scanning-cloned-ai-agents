from google.genai import Client
from google.genai.types import HttpOptions, HttpRetryOptions
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.settings import ModelSettings

from app.utils.gemini.gemini_secret_key import GEMINI_API_KEY

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def get_pydanticai_gemini_llm(
    model_name: str = DEFAULT_GEMINI_MODEL,
    timeout_ms: int = 300_000,
    retry_attempts: int = 3,
    model_kwargs: dict | None = None,
) -> GoogleModel:
    """
    Creates and returns a GoogleModel instance configured for Gemini LLM integration.
    This function initializes a Gemini client using the provided API key and sets up
    the model with specified parameters such as temperature. It raises a
    ValueError if the required GEMINI_API_KEY is not set.
    Args:
        model_name (str): The name of the Gemini model to use. Defaults to DEFAULT_GEMINI_MODEL.
        timeout_ms (int): Request timeout in milliseconds. Defaults to 300000 (5 minutes).
        retry_attempts (int): Number of retry attempts on failure. Defaults to 3.
    Returns:
        GoogleModel: An instance of GoogleModel configured with the Gemini client and model settings.
    Raises:
        ValueError: If ALLTRUE_AGENTS_GEMINI_API_KEY is not set in the secret manager.
    """
    if GEMINI_API_KEY is None:
        raise ValueError(
            "GEMINI_API_KEY is not set. Ensure 'ALLTRUE_AGENTS_GEMINI_API_KEY' is configured in the secret manager."
        )
    if model_kwargs is None:
        model_kwargs = {}
    # Initialize Gemini client with configurable timeout and retry attempts
    gemini_client = Client(
        api_key=GEMINI_API_KEY,
        http_options=HttpOptions(
            timeout=timeout_ms, retry_options=HttpRetryOptions(attempts=retry_attempts)
        ),
    )

    return GoogleModel(
        model_name=model_name,
        provider=GoogleProvider(client=gemini_client),
        settings=ModelSettings(
            **{
                "temperature": 0.0,
                **model_kwargs,
            },
        ),
    )
