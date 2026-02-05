from pathlib import Path
from typing import List

import logfire

from app.core.agents.action_prototype.generic_browser_agent.schema import File


def process_downloaded_files(
    files: List[File],
    working_dir: str | Path | None = None,
    raise_on_missing: bool | None = True,
) -> List[str]:
    """
    Process downloaded files by converting filenames to full paths and validating existence.

    Args:
        files: List of File objects containing name and full_path. If a path doesn't exist,
               falls back to constructing path with working_dir/downloads/{filename}
        working_dir: Working directory containing the downloads folder. When provided,
                    paths are validated to ensure they're within this directory (path traversal protection)
        raise_on_missing: Whether to raise an error if files are missing (default: True)

    Returns:
        List of full file paths for existing files

    Raises:
        ValueError: If raise_on_missing is True and any file is not found or outside working_dir
    """
    files_with_path = []

    for file in files:
        # First, check if file is already a valid path
        file_path = Path(file.full_path)

        # If it doesn't exist and working_dir is provided, try constructing with working_dir
        if not file_path.exists() and working_dir is not None:
            file_path = Path(working_dir) / "downloads" / file.name
        if file_path.exists():
            # Security check: ensure the resolved path is within working_dir
            if working_dir is not None:
                resolved_file = file_path.resolve()
                resolved_working_dir = (Path(working_dir) / "downloads").resolve()
                try:
                    resolved_file.relative_to(resolved_working_dir)
                except ValueError:
                    # Log detailed information for security monitoring
                    logfire.error(
                        "Path traversal attempt detected",
                        provided_path=file,
                        resolved_path=str(resolved_file),
                        working_dir=str(resolved_working_dir),
                    )
                    # Generic error message for user
                    error_msg = "Access denied: Invalid file path"
                    if raise_on_missing:
                        raise ValueError(error_msg)
                    else:
                        logfire.warning(error_msg)
                        continue

            files_with_path.append(str(file_path))
        else:
            # Log detailed information for debugging
            logfire.info(
                "File not found",
                provided_path=file,
                working_dir=str(working_dir) if working_dir else None,
            )
            # Generic error message for user
            error_msg = "File not found"
            if raise_on_missing:
                raise ValueError(error_msg)
            else:
                logfire.warning(error_msg)

    return files_with_path


# TODO Remove v1 when the migration is complete
def process_downloaded_files_v2(
    files: List[File],
    working_dir: str | Path | None = None,
    raise_on_missing: bool | None = True,
) -> List[str]:
    """
    Process downloaded files by converting filenames to full paths and validating existence.

    Args:
        files: List of File objects containing name and full_path. If a path doesn't exist,
               falls back to constructing path with working_dir/{filename}
        working_dir: Working directory containing the action files. When provided,
                    paths are validated to ensure they're within this directory (path traversal protection)
        raise_on_missing: Whether to raise an error if files are missing (default: True)

    Returns:
        List of full file paths for existing files

    Raises:
        ValueError: If raise_on_missing is True and any file is not found or outside working_dir
    """
    files_with_path = []

    for file in files:
        # First, check if file is already a valid path
        file_path = Path(file.full_path)

        # If it doesn't exist and working_dir is provided, try constructing with working_dir
        if not file_path.exists() and working_dir is not None:
            file_path = Path(working_dir) / file.name
        if file_path.exists():
            # Security check: ensure the resolved path is within working_dir
            if working_dir is not None:
                resolved_file = file_path.resolve()
                resolved_working_dir = Path(working_dir).resolve()
                try:
                    resolved_file.relative_to(resolved_working_dir)
                except ValueError:
                    # Log detailed information for security monitoring
                    logfire.error(
                        "Path traversal attempt detected",
                        provided_path=file,
                        resolved_path=str(resolved_file),
                        working_dir=str(resolved_working_dir),
                    )
                    # Generic error message for user
                    error_msg = "Access denied: Invalid file path"
                    if raise_on_missing:
                        raise ValueError(error_msg)
                    else:
                        logfire.warning(error_msg)
                        continue

            files_with_path.append(str(file_path))
        else:
            # Log detailed information for debugging
            logfire.info(
                "File not found",
                provided_path=file,
                working_dir=str(working_dir) if working_dir else None,
            )
            # Generic error message for user
            error_msg = "File not found"
            if raise_on_missing:
                raise ValueError(error_msg)
            else:
                logfire.warning(error_msg)

    return files_with_path
