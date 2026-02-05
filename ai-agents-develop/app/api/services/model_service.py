from typing import List

from alltrue.agents.schema.llm_models import LLMModel

from app.core.llm.model_registry import ModelRegistry


def get_all_models() -> List[LLMModel]:
    """
    Return a serializable list of registered models.
    """
    models: List[LLMModel] = []
    for model_name, model_meta in ModelRegistry.MODELS.items():
        models.append(
            LLMModel(
                model_name=model_name,
                provider=model_meta["provider"],
                capabilities=model_meta.get("capabilities"),
                model_id=model_meta["model_id"],
                additional_params=model_meta.get("additional_params"),
            )
        )

    return models
