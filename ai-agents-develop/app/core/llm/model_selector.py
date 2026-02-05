from typing import Any, Dict, Optional  # Re-added Dict

import logfire

from app.core.llm.model_registry import ModelRegistry

# from app.core.llm.pydanticai.openai_model import DEFAULT_OPENAI_MODEL


class ModelSelector:

    @staticmethod
    def get_all_allowed_models(
        allowed_model_criteria: Optional[Dict[str, Any]] = None,
    ) -> list[str]:
        if not allowed_model_criteria:
            logfire.info("No allowed_model_criteria provided; returning all model IDs.")
            return list(ModelRegistry.MODELS.keys())

        eligible_model_names = ModelRegistry.filter(allowed_model_criteria)
        if not eligible_model_names:
            logfire.warning(
                f"No models found matching allowed_model_criteria: {allowed_model_criteria}. "
                "This might indicate misconfiguration in ModelRegistry or criteria."
            )
        return eligible_model_names

    @staticmethod
    def validate_and_get_model_id(
        proposed_model_id: Optional[str],
        default_model: str,
        allowed_model_criteria: Optional[Dict[str, Any]] = None,
    ) -> str:
        if proposed_model_id is None:
            logfire.info("No proposed model ID provided; using default model.")
            proposed_model_id = default_model

        if not allowed_model_criteria:
            logfire.info(
                "No allowed_model_criteria provided; accepting proposed model."
            )
            return proposed_model_id

        # Start with the proposed model as the one to use, unless validation fails
        final_model_to_use = proposed_model_id
        # is_proposed_model_valid = True

        # --- Phase 1: Determine eligible models based on allowed_model_criteria ---
        eligible_model_names = ModelSelector.get_all_allowed_models(
            allowed_model_criteria=allowed_model_criteria
        )

        # --- Phase 2: Validate proposed_model_id against default_model and allowed_model_criteria ---

        # If allowed_model_criteria exist, proposed_model_id must be in eligible_model_names
        if allowed_model_criteria and proposed_model_id not in eligible_model_names:
            logfire.error(
                f"Proposed model '{proposed_model_id}' is not in the allowed list defined by criteria {allowed_model_criteria}. "
                "Proposed model is invalid for this tool."
            )
            raise ValueError(
                f"Proposed model '{proposed_model_id}' is not allowed based on the provided criteria."
            )

        # No fallback model
        # # --- Phase 3: Determine fallback if proposed_model_id is invalid ---
        # # Attempt to use the strict preselected model (if string) as a primary fallback
        # if not allowed_model_criteria or default_model in eligible_model_names:
        #     final_model_to_use = default_model
        #     logfire.info(f"Falling back to preselected model: {final_model_to_use}")
        # elif eligible_model_names:
        #     # Fallback to the first eligible model if default_model is not valid or unavailable
        #     final_model_to_use = eligible_model_names[0]
        #     logfire.info(f"Falling back to first eligible model: {final_model_to_use}")
        # else:
        #     # Ultimate fallback
        #     final_model_to_use = DEFAULT_OPENAI_MODEL
        #     logfire.warn(f"No valid fallback found. Using universal default: {final_model_to_use}")

        return final_model_to_use
