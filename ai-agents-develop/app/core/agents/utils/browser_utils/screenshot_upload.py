import base64
from pathlib import Path
from typing import Annotated, Literal, Union
from uuid import uuid4

from alltrue.local.file_storage.cloud_file_storage import CloudFileStorage
from pydantic import BaseModel, Field

from app.utils.file_storage_manager import get_file_storage


class S3ScreenshotUploadResult(BaseModel):
    type: Literal["s3"] = "s3"
    key: str
    bucket_name: str


class LocalScreenshotUploadResult(BaseModel):
    type: Literal["local"] = "local"
    file_name: str
    file_path: str


ScreenshotUploadResult = Annotated[
    Union[S3ScreenshotUploadResult, LocalScreenshotUploadResult],
    Field(discriminator="type"),
]


def upload_screenshot(screenshot_b64: str, context: dict) -> ScreenshotUploadResult:
    """
    Upload a base64-encoded screenshot to file storage and return an access path.

    Args:
        screenshot_b64: Base64-encoded PNG screenshot data
        context: Context dictionary passed to storage methods

    Returns:
        ScreenshotUploadResult containing storage-specific metadata
        (S3: key and bucket info, Local: file name and path)
    """
    file_storage = get_file_storage()
    try:
        screenshot_bytes = base64.b64decode(screenshot_b64)
    except Exception as e:
        raise ValueError("Invalid screenshot base64")
    file_name = f"screenshot_{uuid4()}.png"
    file_storage.upload_object(
        context=context,
        object_bytes=screenshot_bytes,
        object_name=file_name,
    )
    if isinstance(file_storage, CloudFileStorage):
        return S3ScreenshotUploadResult(key=file_name, bucket_name=file_storage.bucket)
    else:
        return LocalScreenshotUploadResult(
            file_name=file_name,
            file_path=str(Path(file_storage.local_storage_dir) / file_name),
        )


def upload_screenshot_from_bytes(
    screenshot_bytes: bytes, context: dict
) -> ScreenshotUploadResult:
    """
    Upload a base64-encoded screenshot to file storage and return an access path.

    Args:
        screenshot_bytes: PNG screenshot data
        context: Context dictionary passed to storage methods

    Returns:
        ScreenshotUploadResult containing storage-specific metadata
        (S3: key and bucket info, Local: file name and path)
    """
    file_storage = get_file_storage()
    file_name = f"screenshot_{uuid4()}.png"
    file_storage.upload_object(
        context=context,
        object_bytes=screenshot_bytes,
        object_name=file_name,
        content_type="image/png",
    )
    if isinstance(file_storage, CloudFileStorage):
        return S3ScreenshotUploadResult(key=file_name, bucket_name=file_storage.bucket)
    else:
        return LocalScreenshotUploadResult(
            file_name=file_name,
            file_path=str(Path(file_storage.local_storage_dir) / file_name),
        )
