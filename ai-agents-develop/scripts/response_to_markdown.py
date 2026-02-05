#!/usr/bin/env python3
"""
Simple script to convert response_output.json to readable markdown format
Specifically designed for the OpenAI response format
"""

import json
import sys
from pathlib import Path


def convert_response_to_markdown(json_file_path, output_file_path=None):
    """Convert OpenAI response JSON to markdown format"""

    # Read the JSON file
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate that data is a list
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")

    # Generate output file path if not provided
    if output_file_path is None:
        json_path = Path(json_file_path)
        output_file_path = json_path.parent / f"{json_path.stem}.md"

    # Convert to markdown
    markdown_lines = []
    markdown_lines.append("# OpenAI Response Output\n")
    for i, item in enumerate(data):
        item_type = item.get("type", "unknown")
        content = item.get("content", {})

        markdown_lines.append(f"## Item {i+1}: {item_type.replace('_', ' ').title()}\n")

        if item_type == "reasoning":
            markdown_lines.append(f"- **ID**: {content.get('id', 'N/A')}")
            markdown_lines.append(f"- **Status**: {content.get('status', 'N/A')}")
            markdown_lines.append("")

        elif item_type == "code_interpreter_call":
            markdown_lines.append(f"- **ID**: {content.get('id', 'N/A')}")
            markdown_lines.append(
                f"- **Container ID**: {content.get('container_id', 'N/A')}"
            )
            markdown_lines.append(f"- **Status**: {content.get('status', 'N/A')}")
            markdown_lines.append("")

            code = content.get("code", "")
            if code:
                markdown_lines.append("### Code:")
                markdown_lines.append("```python")
                markdown_lines.append(code)
                markdown_lines.append("```")
                markdown_lines.append("")

        elif item_type == "message":
            markdown_lines.append(f"- **ID**: {content.get('id', 'N/A')}")
            markdown_lines.append(f"- **Role**: {content.get('role', 'N/A')}")
            markdown_lines.append(f"- **Status**: {content.get('status', 'N/A')}")
            markdown_lines.append("")

            content_list = content.get("content", [])
            for j, msg_content in enumerate(content_list):
                if msg_content.get("type") == "output_text":
                    text = msg_content.get("text", "")
                    markdown_lines.append(f"### Message Content {j+1}:")
                    markdown_lines.append(text)
                    markdown_lines.append("")

        markdown_lines.append("---\n")

    # Write to markdown file
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines))

    print(f"Converted {json_file_path} to {output_file_path}")
    return output_file_path


if __name__ == "__main__":
    # Default file path
    default_json_file = "./test_suite/sample_files/GAM/response_output.json"

    # Use command line argument if provided, otherwise use default
    json_file = sys.argv[1] if len(sys.argv) > 1 else default_json_file
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result_file = convert_response_to_markdown(json_file, output_file)
        print(f"Successfully created markdown file: {result_file}")
    except FileNotFoundError:
        print(f"Error: File {json_file} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {json_file}")
    except Exception as e:
        print(f"Error: {e}")
