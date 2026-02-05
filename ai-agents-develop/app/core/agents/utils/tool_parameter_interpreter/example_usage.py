"""
Example usage of the ToolParameterInterpreter.

This file demonstrates how to use the tool parameter interpreter
to interpret function parameters based on user goals.
"""

import json
from typing import Callable, List

from app.core.agents.utils.tool_parameter_interpreter.interpreter import (
    interpret_parameters,
    interpret_single_function_parameters,
)


# Example functions to demonstrate the interpreter
def get_current_weather(location: str, unit: str = "celsius"):
    """
    Get current weather information for a specified location.

    Args:
        location (str): City name, e.g., 'San Francisco'.
        unit (str): Temperature unit, can be 'celsius' or 'fahrenheit'.
    """
    print(
        f"--- Executing get_current_weather(location='{location}', unit='{unit}') ---"
    )

    # Mock data for demonstration
    if "vancouver" in location.lower():
        weather_info = {
            "location": location,
            "temperature": "15",
            "unit": unit,
            "condition": "Cloudy",
        }
    else:
        weather_info = {
            "location": location,
            "temperature": "25",
            "unit": unit,
            "condition": "Sunny",
        }
    return json.dumps(weather_info)


def send_email(to: str, subject: str, body: str, priority: str = "normal"):
    """
    Send an email to a recipient.

    Args:
        to (str): Email address of the recipient.
        subject (str): Email subject line.
        body (str): Email body content.
        priority (str): Email priority level ('low', 'normal', 'high').
    """
    print(
        f"--- Executing send_email(to='{to}', subject='{subject}', body='{body}', priority='{priority}') ---"
    )
    return f"Email sent to {to} with subject '{subject}'"


def search_database(query: str, limit: int = 10, sort_by: str = "relevance"):
    """
    Search a database with the given query.

    Args:
        query (str): Search query string.
        limit (int): Maximum number of results to return.
        sort_by (str): Sort criteria ('relevance', 'date', 'name').
    """
    print(
        f"--- Executing search_database(query='{query}', limit={limit}, sort_by='{sort_by}') ---"
    )
    return f"Found {limit} results for '{query}' sorted by {sort_by}"


def get_system_status():
    """
    Get the current system status and health information.
    """
    print("--- Executing get_system_status() ---")
    return "System is running normally. All services are operational."


def example_basic_usage():
    """
    Basic usage example with a single function.
    """
    print("=== Basic Usage Example ===")

    # Interpret parameters for a user goal
    user_goal = "What's the weather like in Vancouver?"
    results = interpret_single_function_parameters(get_current_weather, user_goal)

    print(f"User Goal: {user_goal}")
    print("Interpreted Parameters:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print()


def example_multiple_functions():
    """
    Example with multiple functions registered.
    """
    print("=== Multiple Functions Example ===")

    # Interpret parameters for different user goals with multiple functions
    user_goals = [
        "Send an urgent email to john@example.com about the meeting",
        "Search for Python tutorials, limit to 5 results",
        "What's the weather in Tokyo in fahrenheit?",
    ]

    functions: List[Callable] = [get_current_weather, send_email, search_database]

    for goal in user_goals:
        print(f"User Goal: {goal}")
        results = interpret_parameters(goal, functions)
        print("Interpreted Parameters:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        print()


def example_quick_usage():
    """
    Example using the convenience function for quick parameter interpretation.
    """
    print("=== Quick Usage Example ===")

    # Quick usage with a single function
    results = interpret_single_function_parameters(
        get_current_weather, "Tell me about the weather in Paris in celsius"
    )

    print("Quick Usage Results:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print()


def example_specific_function():
    """
    Example targeting a specific function for interpretation.
    """
    print("=== Specific Function Example ===")

    # Target a specific function for interpretation
    user_goal = "I need to send an email about the project status"
    results = interpret_single_function_parameters(send_email, user_goal)

    print(f"User Goal: {user_goal}")
    print("Target Function: send_email")
    print("Interpreted Parameters:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print()


def example_with_system_message():
    """
    Example using a custom system message to guide the interpretation.
    """
    print("=== System Message Example ===")

    # Use a custom system message
    system_message = "You are a database search assistant. Always use 'relevance' as the default sort order and limit results to 20 unless specified otherwise."

    user_goal = "Find information about machine learning"
    results = interpret_single_function_parameters(
        search_database, user_goal, system_message=system_message
    )

    print(f"User Goal: {user_goal}")
    print("System Message: You are a database search assistant...")
    print("Interpreted Parameters:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print()


def example_no_parameters():
    """
    Example with a function that has no parameters.
    """
    print("=== No Parameters Example ===")

    # Test with a function that has no parameters
    user_goal = "Check the system status"
    results = interpret_single_function_parameters(get_system_status, user_goal)

    print(f"User Goal: {user_goal}")
    print("Target Function: get_system_status (no parameters)")
    print("Interpreted Parameters:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print()


def main():
    """
    Run all example usage scenarios.
    """
    print("Tool Parameter Interpreter - Example Usage")
    print("=" * 50)
    print()

    try:
        example_basic_usage()
        example_multiple_functions()
        example_quick_usage()
        example_specific_function()
        example_with_system_message()
        example_no_parameters()

        print("All examples completed successfully!")

    except Exception as e:
        print(f"Error running examples: {e}")
        print(
            "Make sure you have set up your OpenAI API key in your environment variables."
        )


if __name__ == "__main__":
    main()
