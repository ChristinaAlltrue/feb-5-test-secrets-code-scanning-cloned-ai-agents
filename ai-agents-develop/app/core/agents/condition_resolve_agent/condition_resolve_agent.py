import asyncio
import base64
import re
from typing import Annotated, Any, Dict, List, Literal, Tuple, Union

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm

# ============================
# Condition Models
# ============================


class NodeObject(BaseModel):
    type: Literal["node"]
    value: str


class PrimitiveObject(BaseModel):
    type: Literal["primitive"]
    value: str


Operand = Annotated[Union[NodeObject, PrimitiveObject], Field(discriminator="type")]


class BinaryCondition(BaseModel):
    left: Operand
    op: str
    right: Operand


class FieldPredicateCondition(BaseModel):
    field: NodeObject
    description: str


ConditionType = Union[BinaryCondition, FieldPredicateCondition]


class ParsedConditions(BaseModel):
    conditions: List[ConditionType]
    logic: Literal["and", "or"]


class ComparisonResponse(BaseModel):
    result: Literal["true", "false"]
    reason: str


class ComparisonDeps(BaseModel):
    compare_data: Dict[str, Any] = Field(default_factory=dict)
    state: List[dict] = Field(default_factory=list)
    parsed_conditions: ParsedConditions | None = None


async def parse_condition_instruction(
    state: List[dict], instruction: str
) -> Tuple[Dict[str, Any], ParsedConditions]:
    parse_agent = Agent(
        model=get_pydanticai_openai_llm(),
        output_type=ParsedConditions,
        system_prompt=(
            "You are a condition parsing agent. Your task is to parse natural language instructions "
            "into structured conditions. Each condition can be either a binary comparison or a field predicate.\n\n"
            "For binary comparisons:\n"
            "- Use the 'left', 'op', and 'right' fields.\n"
            "- Each operand must include a 'type' field, which is either 'node' or 'primitive', and a 'value' string.\n"
            "- 'node' type means it refers to a field in the format like 'node.1.field_b'.\n"
            "- 'primitive' means a direct literal value like '30', '0', or 'true'.\n\n"
            "For field predicates:\n"
            "- Use 'field' as an object with type='node' and 'value', and 'description' as free text.\n\n"
            "ALWAYS return a JSON object with keys 'conditions' (list) and 'logic' ('and' or 'or').\n\n"
            "Example:\n"
            "Input: 'If <node>1.field_b</node> < <value>3</value> and <node>4.field_e</node> == <value>0</value>'\n"
            "Output:\n"
            "{\n"
            '  "conditions": [\n'
            '    {"left": {"type": "node", "value": "node.1.field_b"}, "op": "<", "right": {"type": "primitive", "value": "3"}},\n'
            '    {"left": {"type": "node", "value": "node.4.field_e"}, "op": "==", "right": {"type": "primitive", "value": "0"}}\n'
            "  ],\n"
            '  "logic": "and"\n'
            "}\n\n"
            "ALWAYS use exact field names, and do not invent any values or formats."
        ),
    )
    result = await parse_agent.run(instruction)
    unresolved_node_objects = collect_all_unresolved_fields(result.output)
    compare_data = {}
    for node_address in unresolved_node_objects:
        try:
            index, field_name = parse_node_address(node_address)
            resolved_val = resolve_data(state, index, field_name)
            compare_data[node_address] = resolved_val
        except Exception as e:
            logfire.error(f"Error resolving data for {node_address}: {e}")
            raise e

    parsed_conditions = result.output
    logfire.info(
        f"Parsed {len(parsed_conditions.conditions)} conditions. Conditions: {parsed_conditions}"
    )
    return compare_data, parsed_conditions


def parse_node_address(node_address: str) -> Tuple[int, str]:
    """
    Parse the node address string into an index and field name.
    Example:
    "node.1.field_b" -> (1, "field_b")
    """
    m = re.match(r"node\.(\d+)\.(\w+)", node_address)
    if m is None:
        raise ValueError(f"Invalid field reference: {node_address}")
    return int(m.group(1)), m.group(2)


def resolve_data(state: List[dict], index: int, field_name: str) -> Any:
    logfire.info(f"Resolving data for field {field_name} at index {index}")
    if index >= len(state):
        raise ValueError(f"Index {index} out of range.")
    if field_name not in state[index]:
        raise ValueError(f"Field {field_name} not in state[{index}].")

    return state[index][field_name]


def collect_all_unresolved_fields(parsed_conditions: ParsedConditions) -> List[str]:
    logfire.info(f"Collecting all unresolved fields.")
    fields = set()
    for cond in parsed_conditions.conditions:
        if isinstance(cond, BinaryCondition):
            if cond.left.type == "node":
                fields.add(cond.left.value)
            if cond.right.type == "node":
                fields.add(cond.right.value)
        elif isinstance(cond, FieldPredicateCondition):
            fields.add(cond.field.value)
    logfire.info(f"Unresolved fields: {fields}")
    return list(fields)


async def compare_structured_conditions(
    compare_data: Dict[str, Any], parsed_conditions: ParsedConditions
) -> ComparisonResponse:
    def get_compare_data(obj: Operand) -> Any:
        if obj.type == "node":
            if obj.value not in compare_data:
                raise KeyError(f"Key {obj.value} not found in compare_data")
            return compare_data[obj.value]
        else:
            return obj.value

    logfire.info(f"Comparing structured conditions")
    compare_agent = Agent(
        model=get_pydanticai_openai_llm(),
        output_type=ComparisonResponse,
        system_prompt=(
            "Evaluate the condition using the provided values. Return 'true' or 'false' and explain your reasoning clearly."
        ),
    )

    individual_results: List[ComparisonResponse] = []

    for i, cond in enumerate(parsed_conditions.conditions):
        logfire.info(f"Cond {i+1}: {cond}")
        prompt_parts = []

        if isinstance(cond, BinaryCondition):
            left_val = get_compare_data(cond.left)
            right_val = get_compare_data(cond.right)
            prompt_parts.append(f"Condition: {cond.left} {cond.op} {cond.right}")
            prompt_parts.append(f"Values: {left_val} {cond.op} {right_val}")

        elif isinstance(cond, FieldPredicateCondition):
            field_key = cond.field.value
            content = compare_data.get(field_key)
            prompt_parts.append(
                f"Does this value match the description: '{cond.description}'?"
            )
            if isinstance(content, str) and content.startswith("data:image"):
                try:
                    image_data = base64.b64decode(
                        content.split(",")[1]
                    )  # base64 content
                    prompt_parts.append(
                        BinaryContent(data=image_data, media_type="image/png")
                    )
                except Exception as e:
                    logfire.error(f"Error decoding base64 image: {e}")
                    prompt_parts.append(f"Value: [Malformed image data]")
            else:
                prompt_parts.append(f"Value: {content}")

        result: ComparisonResponse = await compare_agent.run(prompt_parts)
        logfire.info(f"Cond {i+1} Result: {result.output}")
        individual_results.append(result.output)

    logic = parsed_conditions.logic.upper()
    bools = [res.result == "true" for res in individual_results]
    final_result = all(bools) if logic == "AND" else any(bools)
    joined_reasons = "\n\n".join(
        f"Condition {i + 1}: {res.reason}" for i, res in enumerate(individual_results)
    )
    logfire.info(f"Final result: {final_result}. Reason: {joined_reasons}")
    return ComparisonResponse(
        result="true" if final_result else "false",
        reason=f"Evaluated with '{logic}' logic:\n\n{joined_reasons}",
    )


# ============================
# Entry Utility
# ============================


async def resolve_condition(state: List[Dict], instruction: str) -> bool:
    compare_data, conditions = await parse_condition_instruction(state, instruction)
    result = await compare_structured_conditions(compare_data, conditions)
    logfire.info(f"Judge Result: {result}")
    return result.result == "true"


if __name__ == "__main__":
    from pathlib import Path

    logfire.configure()
    coffee_man_image_b64 = (
        "data:image/png;base64,"
        + base64.b64encode(Path("images/coffee_man.png").read_bytes()).decode()
    )

    state: List[Dict] = [
        {"field_a": "0", "image_field": coffee_man_image_b64},
        {"field_b": "1"},
        {"field_c": "2"},
        {"field_d": "3"},
        {"field_e": "4"},
        {"field_f": []},
    ]

    instructions = [
        "If <node>1.field_b</node> < <node>3.field_d</node> and <node>4.field_e</node> > <node>2.field_c</node>, return true.",  # True
        "If <node>1.field_b</node> < <node>3.field_d</node> and <node>4.field_e</node> == <node>2.field_c</node>, return true.",  # False
        "If <node>1.field_b</node> < <value>3</value> and <node>4.field_e</node> > <value>0</value>, return true.",  # True
        "If <node>1.field_b</node> < <value>3</value> and <node>4.field_e</node> == <value>0</value>, return true.",  # False
        "If <node>0.image_field</node> is a man holding a laptop, return true.",  # False
        "If <node>0.image_field</node> is a man holding a mug, return true.",  # True
        "If <node>5.field_f</node> is not empty, return true.",  # False
        "If <node>5.field_f</node> is empty, return true.",  # True
    ]

    expected_results = [
        True,
        False,
        True,
        False,
        False,
        True,
        False,
        True,
    ]

    async def run_all():
        for i, instruction in enumerate(instructions):
            logfire.info(f"\n--- Test {i+1}: {instruction} ---\n")
            result = await resolve_condition(state, instruction)
            logfire.warn(f"Result: {result}")
            assert result == expected_results[i]

    asyncio.run(run_all())
