import inspect
import json
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI
from pydantic import create_model

from app.utils.chatgpt.openai_secret_key import OPENAI_API_KEY

MODEL_NAME = "gpt-4.1-mini"


def create_tool_from_function(func: Callable) -> Dict[str, Any]:
    """
    Generate OpenAI tool description from a Python function.

    Args:
        func: The function to create a tool description for.

    Returns:
        Dictionary containing the tool description.
    """
    signature = inspect.signature(func)
    docstring = inspect.getdoc(func)
    description = (
        docstring.split("\n\n")[0] if docstring else f"Execute {func.__name__}"
    )

    fields = {}
    for param in signature.parameters.values():
        param_name = param.name
        param_type = (
            param.annotation if param.annotation is not inspect.Parameter.empty else Any
        )

        # Skip RunContext parameters - they are not part of the user interface
        if (
            param_name == "ctx"
            and hasattr(param_type, "__origin__")
            and "RunContext" in str(param_type)
        ):
            continue

        if param.default is inspect.Parameter.empty:
            fields[param_name] = (param_type, ...)
        else:
            fields[param_name] = (param_type, param.default)

    # Handle functions with no parameters
    if not fields:
        # Create a tool description for functions with no parameters
        tool_description = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }
        return tool_description

    ArgsModel = create_model(f"{func.__name__}Args", **fields)
    parameters_schema = ArgsModel.model_json_schema()

    tool_description = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": parameters_schema,
        },
    }
    return tool_description


def interpret_parameters(
    user_goal: str,
    functions: List[Callable],
    previous_results: str = "",
    api_key: Optional[str] = None,
    model: str = MODEL_NAME,
    system_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Interpret function parameters based on user goal using LLM.

    Args:
        user_goal: The user's goal or request.
        functions: List of functions to interpret parameters for.
        api_key: OpenAI API key. If None, will use the default from the project.
        model: The OpenAI model to use for interpretation.
        system_message: Custom system message for the LLM.

    Returns:
        Dictionary containing the interpreted parameters.
    """
    if not functions:
        raise ValueError("No functions provided for interpretation")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key or OPENAI_API_KEY)

    # Generate tool descriptions
    tools: List[Dict[str, Any]] = []
    for func in functions:
        tool = create_tool_from_function(func)
        if tool:
            tools.append(tool)

    if not tools:
        raise ValueError("No valid tools provided for interpretation")

    prompt = f"""
    You are a helpful assistant that interprets the parameters for a given function.
    The user goal is: {user_goal}
    The previous results are: {previous_results}
    """

    # Prepare messages
    messages = [{"role": "user", "content": prompt}]

    if system_message:
        messages.insert(0, {"role": "system", "content": system_message})

    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model=model, messages=messages, tools=tools, tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        results = {
            "user_goal": user_goal,
            "response_content": response_message.content,
            "interpreted_parameters": [],
        }

        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args_str = tool_call.function.arguments
                function_args = json.loads(function_args_str)

                results["interpreted_parameters"].append(
                    {
                        "function_name": function_name,
                        "parameters": function_args,
                        "tool_call_id": tool_call.id,
                    }
                )

        return results

    except Exception as e:
        return {
            "user_goal": user_goal,
            "error": f"API call failed: {str(e)}",
            "success": False,
        }


def interpret_single_function_parameters(
    func: Callable,
    user_goal: str,
    previous_results: str = "",
    api_key: Optional[str] = None,
    model: str = MODEL_NAME,
    system_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Interpret parameters for a single function.

    Args:
        func: The function to interpret parameters for.
        user_goal: The user's goal or request.
        api_key: OpenAI API key.
        model: The OpenAI model to use.
        system_message: Custom system message for the LLM.

    Returns:
        Dictionary containing the interpretation results.
    """
    return interpret_parameters(
        user_goal=user_goal,
        functions=[func],
        previous_results=previous_results,
        api_key=api_key,
        model=model,
        system_message=system_message,
    )
