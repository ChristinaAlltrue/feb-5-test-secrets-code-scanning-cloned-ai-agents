import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import logfire
from openai import AsyncOpenAI
from openai.types.container_create_response import ContainerCreateResponse
from openai.types.responses.response import Response


async def get_or_create_container(
    client: AsyncOpenAI, name: str = "ai-agent", reuse_existing: bool = True
) -> ContainerCreateResponse:
    """
    Create or optionally reuse an existing container.

    Args:
        client: AsyncOpenAI client instance
        name: Container name identifier
        reuse_existing: If True (default), attempts to reuse existing container with same name.
                       If False, always creates a new container.

    Returns:
        ContainerCreateResponse object

    Note:
        Setting reuse_existing=False avoids the containers.list() API call and ensures
        each execution gets a fresh container. This can be useful if the list() API
        fails with 500 errors.
    """
    if reuse_existing:
        try:
            async for c in await client.containers.list():
                if c.name == name and c.status != "expired":
                    logfire.info(f"Using existing container: {c.id}")
                    return c
        except Exception as e:
            logfire.warning(f"Failed to list containers, will create new one: {e}")

    logfire.info(f"Creating new container: {name}")
    return await client.containers.create(name=name)


async def upload_files_to_container(
    client: AsyncOpenAI, container_id: str, file_paths: list[Path]
) -> list[str]:
    file_ids = []
    for path in file_paths:
        logfire.info(f"Uploading file: {path}")
        with open(path, "rb") as f:
            file = await client.containers.files.create(
                container_id=container_id, file=f
            )
        file_ids.append(file.id)
        logfire.info(f"Uploaded file: {path.name} with id: {file.id}")
    return file_ids


async def create_response_with_container(
    client: AsyncOpenAI,
    container_id: str,
    instructions: str,
    model: str,
    save_output_to: Optional[Path] = None,
    verbosity: Optional[Literal["low", "medium", "high"]] = None,
    effort: Optional[Literal["minimal", "low", "medium", "high"]] = None,
) -> Response:
    """
    Create a response using OpenAI's code interpreter with a container.

    Args:
        client: AsyncOpenAI client instance
        container_id: ID of the container to use for code execution
        instructions: Instructions/prompt for the model
        model: Model name to use (e.g., "gpt-4o", "o1")
        save_output_to: Optional path to save the response output as JSON
        verbosity: Optional verbosity level for the response text output.
                   Valid values: "low", "medium", "high"
        effort: Optional effort level for reasoning models.
                Valid values: "minimal", "low", "medium", "high"

    Returns:
        Response object containing the model's output

    Note:
        - verbosity controls the text output detail level
        - effort is used in reasoning metadata for compatible models (e.g., o1 series)
          to control computational effort
    """
    # Prepare request kwargs
    request_kwargs: Dict[str, Any] = {
        "model": model,
        "tools": [
            {
                "type": "code_interpreter",
                "container": container_id,
            }
        ],
        "tool_choice": "auto",
        "input": instructions,
    }

    # Add verbosity as text parameter if provided
    if verbosity is not None:
        request_kwargs["text"] = {"verbosity": verbosity}

    # Add reasoning metadata if effort is provided
    if effort is not None:
        request_kwargs["reasoning"] = {"effort": effort}

    async with client.responses.stream(**request_kwargs) as stream:
        async for _ in stream:
            pass  # Consume the stream to completion
        response = await stream.get_final_response()

    logfire.info(f"Response: {response.output_text}")

    if save_output_to:
        output_data = []
        for item in response.output:
            output_data.append({"type": item.type, "content": item.model_dump()})

        save_output_to.parent.mkdir(parents=True, exist_ok=True)
        with open(save_output_to, "w") as f:
            json.dump(output_data, f, indent=2)
        logfire.info(f"Saved response.output to {save_output_to}")

    return response


async def _download_specific_file(
    client: AsyncOpenAI, container_id: str, file_id: str, output_path: Path
):
    content = await client.containers.files.content.retrieve(
        file_id=file_id, container_id=container_id
    )
    content.write_to_file(output_path)


async def download_file_from_container(
    client: AsyncOpenAI, container_id: str, file_id: str, dest_dir: Path, file_name: str
) -> str:
    f_path = dest_dir / file_name
    f_path.parent.mkdir(parents=True, exist_ok=True)
    await _download_specific_file(client, container_id, file_id, f_path)
    return str(f_path)


async def download_all_files_from_container(
    client: AsyncOpenAI,
    container_id: str,
    dest_dir: Path,
    exclude_file_ids: list[str] | None = None,
):
    if exclude_file_ids is None:
        exclude_file_ids = []
    exclude_file_ids_set: set[str] = set(
        exclude_file_ids
    )  # convert to set for O(1) lookup
    async for f in await client.containers.files.list(container_id=container_id):
        file_name = Path(f.path).name
        if f.id in exclude_file_ids_set:
            logfire.info(f"Skipping file: {file_name} with id: {f.id}")
            continue
        logfire.info(f"Downloading file: {file_name} with id: {f.id}")
        f_path = dest_dir / file_name
        logfire.info(f"Writing to {f_path}")
        await _download_specific_file(client, container_id, f.id, f_path)


async def delete_container(client: AsyncOpenAI, container_id: str):
    await client.containers.delete(container_id)
    logfire.info(f"Deleted container: {container_id}")


async def list_container_files(
    client: AsyncOpenAI, container_id: str
) -> List[Dict[str, Any]]:
    """List all files in a container (async)"""
    files = []
    async for file in client.containers.files.list(container_id=container_id):
        files.append(
            {
                "id": file.id,
                "name": Path(file.path).name,
                "path": file.path,
                "size": file.bytes,
                "created_at": file.created_at,
            }
        )
    return files


async def find_file_in_container(
    client: AsyncOpenAI, container_id: str, filename: str
) -> Optional[Dict[str, Any]]:
    """Find a specific file in the container by filename (async)"""
    files = await list_container_files(client, container_id)
    for file in files:
        if file["name"] == filename:
            return file
    return None


async def download_specific_file(
    client: AsyncOpenAI, container_id: str, file_id: str, output_path: Path
) -> str:
    """Download a specific file from the container (async)"""
    # Get file content
    content = await client.containers.files.content.retrieve(
        file_id=file_id, container_id=container_id
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file content
    content.write_to_file(output_path)

    logfire.info(f"File downloaded to: {output_path}")
    return str(output_path)
