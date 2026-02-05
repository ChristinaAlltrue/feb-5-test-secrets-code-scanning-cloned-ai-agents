import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

if TYPE_CHECKING:
    pass

import logfire
from openai import AsyncOpenAI
from pydantic_ai import ModelRetry

from app.core.agents.utils.openai_utils.container import (
    create_response_with_container,
    delete_container,
    download_all_files_from_container,
    download_file_from_container,
    get_or_create_container,
    list_container_files,
    upload_files_to_container,
)
from app.utils.chatgpt.openai_secret_key import OPENAI_API_KEY

MODEL_NAME = "gpt-5"


class CodeInterpreterResponseManager:
    """
    Manages OpenAI containers with code interpreter capabilities.

    Provides a clean interface for:
    - Container lifecycle management
    - File upload/download operations
    - Code execution with context persistence
    - Automatic cleanup
    """

    def __init__(
        self,
        container_name: str,
        model_name: str = MODEL_NAME,
        api_key: Optional[str] = None,
        auto_cleanup: bool = True,
    ):
        """
        Initialize the Code Interpreter Manager.

        Args:
            container_name: Unique identifier for the container
            model_name: OpenAI model to use (default: gpt-5)
            api_key: OpenAI API key (uses environment/default if not provided)
            auto_cleanup: Whether to automatically cleanup container on context exit
        """
        self.container_name = container_name
        self.model_name = model_name
        self.auto_cleanup = auto_cleanup
        self._container: Optional[Any] = None

        # Initialize client
        api_key = api_key or os.getenv("CONFIG_OPENAI_API_KEY") or OPENAI_API_KEY
        self._client = AsyncOpenAI(api_key=api_key, max_retries=3)

    async def __aenter__(self):
        """Async context manager entry - creates container."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - optionally cleanup container."""
        if self.auto_cleanup:
            await self.cleanup()

    async def start(self) -> None:
        """Initialize and start the container."""
        if not self._container:
            logfire.info(f"Creating container: {self.container_name}")
            self._container = await get_or_create_container(
                self._client, name=self.container_name, reuse_existing=False
            )
            logfire.info(f"Container ready: {self._container.id}")

    async def upload_files(self, file_paths: List[Union[str, Path]]) -> List[str]:
        """
        Upload files to the container.

        Args:
            file_paths: List of file paths to upload

        Returns:
            List of file IDs in the container
        """
        if not self._container:
            await self.start()

        if not self._container:
            raise RuntimeError("Container not initialized")

        # Convert to Path objects and validate
        valid_paths = []
        for path in file_paths:
            p = Path(path)
            if p.exists() and p.is_file():
                valid_paths.append(p)
            else:
                logfire.warning(f"File not found or invalid: {path}")

        if not valid_paths:
            return []

        logfire.info(f"Uploading {len(valid_paths)} files to container")
        file_ids = await upload_files_to_container(
            self._client, self._container.id, valid_paths
        )
        logfire.info(f"Successfully uploaded {len(file_ids)} files")

        return file_ids

    async def execute_code(
        self,
        prompt: str,
        save_output_to: Optional[Path] = None,
        verbosity: Optional[Literal["low", "medium", "high"]] = "low",
        effort: Optional[Literal["minimal", "low", "medium", "high"]] = "medium",
    ) -> Any:
        """
        Execute code/prompt in the container with code interpreter.

        Args:
            prompt: The code or instruction to execute
            save_output_to: Optional path to save the response output
            verbosity: Optional verbosity level for the response text output.
                       Valid values: "low", "medium", "high"
            effort: Optional effort level for reasoning models.
                    Valid values: "minimal", "low", "medium", "high"

        Returns:
            Response object from the code interpreter
        """
        if not self._container:
            await self.start()

        if not self._container:
            raise RuntimeError("Container not initialized")

        logfire.info(
            f"Executing code with model {self.model_name} in container {self._container.id}, with prompt: {prompt}"
        )

        response = await create_response_with_container(
            self._client,
            self._container.id,
            prompt,
            model=self.model_name,
            save_output_to=save_output_to,
            verbosity=verbosity,
            effort=effort,
        )

        if response.status == "completed":
            logfire.info("Code execution completed successfully")
        else:
            logfire.error(f"Code execution failed with status: {response.status}")

        return response

    async def list_files(self) -> List[Dict[str, Any]]:
        """
        List all files in the container.

        Returns:
            List of file information dictionaries
        """
        if not self._container:
            await self.start()

        if not self._container:
            raise RuntimeError("Container not initialized")

        return await list_container_files(self._client, self._container.id)

    async def download_file(
        self,
        filename: Optional[str] = None,
        destination_dir: Union[str, Path] = "",
        custom_name: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Download a file from the container.

        Args:
            filename: Name of file in container to download (required if file_id not provided)
            destination_dir: Local directory to save the file
            custom_name: Optional custom name for the downloaded file
            file_id: Optional file ID to download directly (skips file listing if provided)

        Returns:
            Path to downloaded file, or None if file not found
        """
        if not self._container:
            await self.start()

        if not self._container:
            raise RuntimeError("Container not initialized")

        # If file_id is provided, use it directly
        if file_id:
            logfire.info(f"Downloading file with ID: {file_id}")
            download_name = custom_name or filename or f"file_{file_id}"
            file_path = await download_file_from_container(
                self._client,
                self._container.id,
                file_id,
                Path(destination_dir),
                download_name,
            )
            logfire.info(f"Downloaded file: {file_path}")
            return str(file_path)

        # Otherwise, find the file by filename
        if not filename:
            raise ValueError("Either filename or file_id must be provided")

        # Find the file in container
        container_files = await self.list_files()
        found_file_id = None

        for file_info in container_files:
            if file_info["name"] == filename:
                found_file_id = file_info["id"]
                break

        if not found_file_id:
            logfire.error(f"File '{filename}' not found in container")
            return None

        # Download the file
        download_name = custom_name or filename
        file_path = await download_file_from_container(
            self._client,
            self._container.id,
            found_file_id,
            Path(destination_dir),
            download_name,
        )

        logfire.info(f"Downloaded file: {file_path}")
        return str(file_path)

    async def download_all_files(
        self,
        destination_dir: Union[str, Path],
        exclude_file_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Download all files from the container.

        Args:
            destination_dir: Local directory to save files
            exclude_file_ids: File IDs to exclude from download
        """
        if not self._container:
            await self.start()

        if not self._container:
            raise RuntimeError("Container not initialized")

        await download_all_files_from_container(
            self._client,
            self._container.id,
            Path(destination_dir),
            exclude_file_ids=exclude_file_ids or [],
        )

    async def cleanup(self) -> None:
        """Clean up and delete the container."""
        if self._container:
            logfire.info(f"Cleaning up container: {self._container.id}")
            await delete_container(self._client, self._container.id)
            self._container = None
            logfire.info("Container cleanup completed")

    @property
    def container_id(self) -> Optional[str]:
        """Get the container ID if available."""
        return self._container.id if self._container else None

    @property
    def is_ready(self) -> bool:
        """Check if container is ready for use."""
        return self._container is not None


# Keep the original function for backward compatibility
async def run_code_with_container(
    working_dir: str,
    file_path_list: list[str],
    instructions: str,
    container_name: str = "ai-agent",
):
    """
    Legacy function - kept for backward compatibility.
    Consider using CodeInterpreterManager for new code.
    """
    # Check if all files exist
    file_paths = []
    for f in file_path_list:
        file_path = Path(f)
        if not file_path.exists():
            raise ModelRetry(f"File {file_path} not found")
        file_paths.append(file_path)

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    container = None
    try:
        container = await get_or_create_container(
            client, name=container_name, reuse_existing=False
        )
        logfire.info(f"Container: {container}")
        ori_file_ids = await upload_files_to_container(client, container.id, file_paths)

        # IMPORTANT: do not use parse function, the files in the container cannot be retrieved. Use create instead.
        resp = await create_response_with_container(
            client,
            container.id,
            instructions,
            model=MODEL_NAME,
        )
        if resp.status == "completed":
            output = resp.output_text
        else:
            raise Exception(f"Response status: {resp.status}")

        logfire.info(f"Output: {output}")
        await download_all_files_from_container(
            client, container.id, Path(working_dir), exclude_file_ids=ori_file_ids
        )

    except Exception as e:
        logfire.error(f"Error in run_code_with_container: {e}")
        raise

    finally:
        if container is not None:
            try:
                await delete_container(client, container.id)
            except Exception as e:
                logfire.error(f"Error in deleting container: {e}")

    return output


class SimpleCodeInterpreter:
    """
    Simplified interface for one-off code interpreter tasks.

    Use this when you don't need persistent container management
    and want to execute code with automatic cleanup.
    """

    @staticmethod
    async def execute(
        prompt: str,
        file_paths: Optional[List[Union[str, Path]]] = None,
        container_name: Optional[str] = None,
        model_name: str = MODEL_NAME,
        download_files: Optional[List[str]] = None,
        destination_dir: Optional[Union[str, Path]] = None,
        save_output_to: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Execute code with automatic container management.

        Args:
            prompt: Code or instruction to execute
            file_paths: Optional files to upload before execution
            container_name: Container identifier (auto-generated if not provided)
            model_name: OpenAI model to use
            download_files: List of filenames to download after execution
            destination_dir: Where to save downloaded files
            save_output_to: Where to save the execution output

        Returns:
            Dictionary containing response and any downloaded file paths
        """

        if not container_name:
            container_name = f"simple_exec_{uuid.uuid4().hex[:8]}"

        result: Dict[str, Any] = {
            "response": None,
            "downloaded_files": [],
            "container_id": None,
        }

        async with CodeInterpreterResponseManager(
            container_name, model_name
        ) as manager:
            result["container_id"] = manager.container_id

            # Upload files if provided
            if file_paths:
                await manager.upload_files(file_paths)

            # Execute the code
            response = await manager.execute_code(prompt, save_output_to)
            result["response"] = response

            # Download files if requested
            if download_files and destination_dir:
                for filename in download_files:
                    file_path = await manager.download_file(filename, destination_dir)
                    if file_path and isinstance(result["downloaded_files"], list):
                        result["downloaded_files"].append(file_path)

        return result
