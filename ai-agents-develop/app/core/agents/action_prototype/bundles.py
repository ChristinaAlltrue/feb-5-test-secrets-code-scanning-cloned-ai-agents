import inspect
from dataclasses import dataclass
from types import UnionType
from typing import Any, Callable, Dict, Optional, Type, Union, cast

from alltrue.agents.schema.action_prototype import (
    ActionPrototype,
    extract_deps_schema_from_model,
)
from pydantic import BaseModel, create_model
from pydantic_ai import Tool
from pydantic_graph import BaseNode

from app.core.registry import register_action, register_prototype, register_tool

DependencyModel = Union[Type["BaseModel"], None]
OutputModel = Union[Type["BaseModel"], None, UnionType]


@dataclass
class ActionPrototypeBundle:
    name: str
    prototype: "ActionPrototype"
    deps_model: DependencyModel
    output_model: OutputModel
    logic_cls: Type["BaseNode"]

    def register(self):
        register_prototype(self.name, self)
        register_action(self.name, self.logic_cls)


@dataclass
class ToolBundle:
    tool_id: str
    tool_display_name: str
    tool_description: str
    function: "Tool"
    tool_schema: list[dict]
    default_model: Optional[str] = None
    allowed_model_criteria: Optional[Dict[str, Any]] = None

    def register(self):
        register_tool(self.tool_id, self)

    @classmethod
    def from_function(
        cls,
        func: Callable[..., Any],
        tool_id: str,
        tool_display_name: str,
        *,
        description: Optional[str] = None,
        parameters_model: Optional[Type["BaseModel"]] = None,
        takes_ctx: bool = True,
        max_retries: int = 3,
        type_overrides: Optional[dict[str, Any]] = None,
        default_model: Optional[str] = None,
        allowed_model_criteria: Optional[Dict[str, Any]] = None,
    ) -> "ToolBundle":
        """
        Build a ToolBundle from a plain function, inferring description and
        generating a parameters model from the function signature when not provided.
        Skips a leading RunContext-like "ctx" param from the generated model.
        """

        docstring = inspect.getdoc(func) or ""
        first_para = docstring.split("\n\n")[0].strip() if docstring else ""
        tool_description = description or (first_para or f"Execute {tool_id}")

        params_model = parameters_model
        if params_model is None:
            fields: dict[str, tuple[Any, Any]] = {}
            signature = inspect.signature(func)
            for param in signature.parameters.values():
                param_name = param.name
                anno = (
                    param.annotation
                    if param.annotation is not inspect.Parameter.empty
                    else Any
                )

                # Skip RunContext-like ctx param
                if param_name == "ctx":
                    # If explicitly annotated with a context, skip; otherwise skip by name
                    context_like = True
                    if getattr(anno, "__origin__", None) is not None:
                        context_like = "RunContext" in str(anno)
                    if context_like:
                        continue

                if type_overrides and param_name in type_overrides:
                    anno = type_overrides[param_name]

                default = (
                    ... if param.default is inspect.Parameter.empty else param.default
                )
                fields[param_name] = (anno, default)

            params_model = create_model(f"{tool_id}_Params", **fields)
        tool_schema_list = cast(
            list[dict[str, Any]], extract_deps_schema_from_model(params_model)
        )

        tool = Tool(func, takes_ctx=takes_ctx, max_retries=max_retries)
        return cls(
            tool_id=tool_id,
            tool_display_name=tool_display_name,
            tool_description=tool_description,
            function=tool,
            tool_schema=tool_schema_list,
            allowed_model_criteria=allowed_model_criteria,
            default_model=default_model,
        )
