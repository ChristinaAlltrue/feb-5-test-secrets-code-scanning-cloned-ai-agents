#  Copyright 2023-2024 AllTrue.ai Inc
#  All Rights Reserved.
#
#  NOTICE: All information contained herein is, and remains
#  the property of AllTrue.ai Incorporated. The intellectual and technical
#  concepts contained herein are proprietary to AllTrue.ai Incorporated
#  and may be covered by U.S. and Foreign Patents,
#  patents in process, and are protected by trade secret or copyright law.
#  Dissemination of this information or reproduction of this material
#  is strictly forbidden unless prior written permission is obtained
#  from AllTrue.ai Incorporated.

import os
import threading
from typing import Optional, Union

import logfire
from alltrue.local.file_storage.cloud_file_storage import CloudFileStorage
from alltrue.local.file_storage.file_storage_factory import (
    get_file_storage as get_file_storage_factory,
)
from alltrue.local.file_storage.local_file_storage import LocalFileStorage


class FileStorageManager:
    """Singleton file storage manager that can be used across the application."""

    _instance: Optional["FileStorageManager"] = None
    _storage: Optional[Union[LocalFileStorage, CloudFileStorage]] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(
        self, bucket_name: Optional[str] = None
    ) -> Union[LocalFileStorage, CloudFileStorage]:
        """Initialize storage with optional bucket name."""
        # Use double-checked locking pattern for initialization
        if self._storage is None:
            with self._lock:
                # check again after acquiring the lock to avoid race conditions
                if self._storage is None:
                    # Use provided bucket or get from environment
                    bucket = bucket_name or os.getenv("STORAGE_BUCKET_NAME")

                    try:
                        self._storage = get_file_storage_factory(bucket=bucket)

                        # Log which type was selected
                        if isinstance(self._storage, CloudFileStorage):
                            logfire.info("Initialized S3 storage", bucket=bucket)
                        elif isinstance(self._storage, LocalFileStorage):
                            logfire.info("Initialized local storage")
                        else:
                            logfire.warn(
                                "Unknown storage type", type=type(self._storage)
                            )

                    except Exception as e:
                        logfire.error("Failed to initialize storage", exception=e)
                        raise RuntimeError(f"Storage initialization failed: {e}")

        return self._storage

    def get_storage(self) -> Union[LocalFileStorage, CloudFileStorage]:
        """Get the storage instance, initializing if needed."""
        if self._storage is None:
            return self.initialize()
        return self._storage

    def is_s3_storage(self) -> bool:
        """Check if current storage is S3-based."""
        if self._storage is None:
            return False
        return isinstance(self._storage, CloudFileStorage)

    def is_local_storage(self) -> bool:
        """Check if current storage is local-based."""
        if self._storage is None:
            return False
        return isinstance(self._storage, LocalFileStorage)

    def close(self):
        """Close the storage connection."""
        if self._storage is not None:
            try:
                self._storage.close()
                logfire.info("Storage closed successfully")
            except Exception as e:
                logfire.error("Error closing storage", exception=e)
            finally:
                self._storage = None

    def reset(self):
        """Reset the storage instance (useful for testing)."""
        self.close()
        self._storage = None


# Global storage manager instance
_file_storage_manager = FileStorageManager()


def get_file_storage(
    bucket_name: Optional[str] = None,
) -> Union[LocalFileStorage, CloudFileStorage]:
    """
    Get the application file storage instance.

    Args:
        bucket_name: Optional bucket name to use for initialization

    Returns:
        LocalFileStorage or CloudFileStorage instance
    """
    return (
        _file_storage_manager.get_storage()
        if _file_storage_manager._storage
        else _file_storage_manager.initialize(bucket_name)
    )


def close_file_storage():
    """Close the file storage connection."""
    _file_storage_manager.close()


def reset_file_storage():
    """Reset the file storage instance (useful for testing)."""
    _file_storage_manager.reset()


def is_s3_storage() -> bool:
    """Check if current storage is S3-based."""
    return _file_storage_manager.is_s3_storage()


def is_local_storage() -> bool:
    """Check if current storage is local-based."""
    return _file_storage_manager.is_local_storage()
