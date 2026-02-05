from pathlib import Path
from typing import Optional, Union

import logfire
from alltrue.agents.schema.control_execution import LocalEvidence, S3Evidence
from alltrue.local.file_storage.cloud_file_storage import CloudFileStorage

from app.utils.file_storage_manager import get_file_storage


@logfire.instrument()
def upload_file(
    file_path: str,
    context: dict,
    new_file_name: Optional[str] = None,
    content_type: Optional[str] = None,
) -> Union[S3Evidence, LocalEvidence]:
    """
    Upload a file to the file storage.

    Args:
        file_path: The path to the file to upload.
        context: The context to upload the file to.
        new_file_name: The name of the file to upload. If not provided, the name of the file will be the same as the original file.
    """
    file_name = new_file_name or Path(file_path).name
    file_path_obj = Path(file_path)

    # TODO: sometimes the LLM will give a file name called <no evidence>. We need to handle this.
    if not file_path_obj.exists():
        logfire.info(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logfire.info(f"Uploading file: {file_path} as {file_name}")
    with open(file_path, "rb") as file:
        file_bytes = file.read()
        file_storage = get_file_storage()
        file_storage.upload_object(
            context=context,
            object_bytes=file_bytes,
            object_name=file_name,
            content_type=content_type,
        )
        if isinstance(file_storage, CloudFileStorage):
            logfire.info(f"File uploaded to S3: s3://{file_storage.bucket}/{file_name}")
            return S3Evidence(bucket_name=file_storage.bucket, key=file_name)
        else:
            logfire.info(
                f"File uploaded to local storage: {file_storage.local_storage_dir}/{file_name}"
            )
            return LocalEvidence(
                file_path=str(Path(file_storage.local_storage_dir) / file_name)
            )
