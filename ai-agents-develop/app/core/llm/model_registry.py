from typing import Any, Dict, List, NotRequired, TypedDict, Union

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel

from app.core.llm.pydanticai.gemini_model import get_pydanticai_gemini_llm
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


class ModelMeta(TypedDict):
    provider: str
    model_id: str
    additional_params: Dict[str, Any]
    capabilities: NotRequired[List[str]]


class ModelRegistry:
    MODELS: Dict[str, ModelMeta] = {
        "GPT-5.2 Thinking": {
            "provider": "openai",
            "capabilities": ["reasoning"],
            "model_id": "gpt-5.2",
            "additional_params": {"reasoning": {"effort": "high"}, "temperature": 0},
        },
        "GPT-5.2 Instant": {
            "provider": "openai",
            "model_id": "gpt-5.2-chat-latest",
            "additional_params": {"reasoning": {"effort": "high"}, "temperature": 0},
        },
        "GPT-5.1 Thinking": {
            "provider": "openai",
            "capabilities": ["reasoning"],
            "model_id": "gpt-5.1",
            "additional_params": {"reasoning": {"effort": "high"}, "temperature": 0},
        },
        "GPT-5.1 Instant": {
            "provider": "openai",
            "model_id": "gpt-5.1",
            "additional_params": {"temperature": 0},
        },
        "GPT-5 Thinking": {
            "provider": "openai",
            "capabilities": ["reasoning"],
            "model_id": "gpt-5",
            "additional_params": {"reasoning": {"effort": "high"}, "temperature": 0},
        },
        "GPT-4.1": {
            "provider": "openai",
            "model_id": "gpt-4.1",
            "additional_params": {"temperature": 0},
        },
        "GPT-4.1 Mini": {
            "provider": "openai",
            "model_id": "gpt-4.1-mini",
            "additional_params": {"temperature": 0},
        },
        "GPT-4o Mini": {
            "provider": "openai",
            "model_id": "gpt-4o-mini",
            "additional_params": {"temperature": 0},
        },
        "Gemini 3": {
            "provider": "google",
            "capabilities": ["reasoning"],
            "model_id": "gemini-3-pro-preview",
            "additional_params": {"temperature": 0},
        },
        "Gemini 2.5 Pro": {
            "provider": "google",
            "capabilities": ["reasoning"],
            "model_id": "gemini-2.5-pro",
            "additional_params": {"temperature": 0},
        },
        "Gemini 2.5 Flash": {
            "provider": "google",
            "capabilities": ["reasoning"],
            "model_id": "gemini-2.5-flash",
            "additional_params": {"temperature": 0},
        },
        "Gemini 2.5 Flash-Lite": {
            "provider": "google",
            "capabilities": ["reasoning"],
            "model_id": "gemini-2.5-flash-lite",
            "additional_params": {"temperature": 0},
        },
    }

    @classmethod
    def filter(cls, criteria: Dict[str, Any]) -> List[str]:
        """
        Return model IDs that match the criteria
        Example criteria:
          {"provider": ["openai"], "capabilities": ["reasoning"]}
        """
        result = []
        for model_name, meta in cls.MODELS.items():
            # provider filter
            if "provider" in criteria and meta["provider"] not in criteria["provider"]:
                continue
            # capabilities filter
            if "capabilities" in criteria:
                model_capabilities = meta.get("capabilities", [])
                if not all(
                    cap in model_capabilities for cap in criteria["capabilities"]
                ):
                    continue
            result.append(model_name)
        return result

    # Example usage of allowed_model_criteria and preselected_model (not part of ModelRegistry)
    # allowed_model_criteria_example = {
    #         "provider": ["openai"],
    #         "capabilities": ["reasoning"]
    #     }
    #
    # # Preselected model per scenario with metadata
    # preselected_model_example = "GPT-5.1 Thinking"  # Model with reasoning capability

    @classmethod
    def get_pydantic_ai_llm(cls, model_name: str) -> Union[OpenAIModel, GoogleModel]:
        """
        Return the pydantic_ai LLM config for the given model name
        """
        model_meta = cls.MODELS.get(model_name)
        if not model_meta:
            raise ValueError(f"Model '{model_name}' not found in ModelRegistry.")

        provider = model_meta["provider"]
        model_id = model_meta["model_id"]
        additional_params = model_meta.get("additional_params", {})

        if provider == "openai":
            return get_pydanticai_openai_llm(
                model_name=model_id, model_kwargs=additional_params
            )
        elif provider == "google":
            return get_pydanticai_gemini_llm(
                model_name=model_id, model_kwargs=additional_params
            )
        else:
            raise ValueError(
                f"Unsupported provider '{provider}' for model '{model_name}'."
            )
