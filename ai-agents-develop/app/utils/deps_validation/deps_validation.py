from dataclasses import dataclass
from typing import Any, Dict, Type

from alltrue.agents.schema.action_execution import ArgsDeps, PrimitiveDeps, RefDeps
from pydantic import BaseModel, TypeAdapter, ValidationError, create_model

primitive_validators = {
    str: TypeAdapter(str),
    int: TypeAdapter(int),
    float: TypeAdapter(float),
    bool: TypeAdapter(bool),
    dict: TypeAdapter(dict),
    list: TypeAdapter(list),
}


def validate_field_with_temp_model(
    model_cls: type[BaseModel], field_name: str, value: Any
) -> Any:
    """
    Dynamically create a model with just this one field.
    This is a fallback for fields that don't have a pydantic adapter.
    For example, a field with a custom class as the type or Optional[].
    """

    if field_name not in model_cls.model_fields:
        raise ValueError(f"Field '{field_name}' not found in {model_cls.__name__}")

    field_info = model_cls.model_fields[field_name]
    field_type = field_info.annotation
    default = field_info.default if field_info.default is not None else ...

    # Dynamically create a model with just this one field
    TempModel = create_model(
        f"Temp_{model_cls.__name__}_{field_name}", **{field_name: (field_type, default)}
    )

    validated = TempModel.model_validate({field_name: value})
    return getattr(validated, field_name)


@dataclass
class VariablesModelDump:
    control_variables: Dict[str, dict]
    reference_variables: Dict[str, dict]
    independent_variables: Dict[str, dict]


class DepsValidator:
    def __init__(
        self,
        control_variables: Dict[str, PrimitiveDeps],
        reference_variables: Dict[str, RefDeps],
        independent_variables: Dict[str, ArgsDeps],
        model_cls: Type[BaseModel],
    ):
        self.control_variables = control_variables
        self.reference_variables = reference_variables
        self.independent_variables = independent_variables
        self.model_cls = model_cls

    def require_required_fields_from_model(self):
        merged_deps = {
            **self.control_variables,
            **self.reference_variables,
            **self.independent_variables,
        }
        required_fields = [
            name
            for name, field in self.model_cls.model_fields.items()
            if field.is_required()
        ]
        missing = [f for f in required_fields if f not in merged_deps]
        if missing:
            raise ValueError(f"Missing required dependencies: {', '.join(missing)}")

    def validate_control_variables(self) -> Dict[str, PrimitiveDeps]:
        validated: Dict[str, PrimitiveDeps] = {}
        for name, dep in self.control_variables.items():
            if name not in self.model_cls.model_fields:
                continue  # unknown field, skip

            field_info = self.model_cls.model_fields[name]
            field_type = field_info.annotation

            adapter = primitive_validators.get(field_type)

            try:
                if adapter:
                    # use pydantic adapter to coerce value
                    coerced_value = adapter.validate_python(dep.value)
                else:
                    # fallback: use full-field validation via temp model
                    coerced_value = validate_field_with_temp_model(
                        self.model_cls, name, dep.value
                    )

                validated[name] = PrimitiveDeps(
                    value_type="primitive", value=coerced_value
                )
            except ValidationError as e:
                raise ValueError(f"Invalid value for field '{name}': {e}")

        return validated

    def variable_model_dump(self) -> VariablesModelDump:
        return VariablesModelDump(
            control_variables={
                k: v.model_dump() for k, v in self.validate_control_variables().items()
            },
            reference_variables={
                k: v.model_dump() for k, v in self.reference_variables.items()
            },
            independent_variables={
                k: v.model_dump() for k, v in self.independent_variables.items()
            },
        )
