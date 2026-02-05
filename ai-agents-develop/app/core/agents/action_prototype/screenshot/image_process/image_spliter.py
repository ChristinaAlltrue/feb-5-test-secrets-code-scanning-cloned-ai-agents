import os
from typing import List, Literal
from uuid import uuid4

import cv2
import logfire
import numpy as np


def split_image_by_spacing(
    input_image: bytes,
    axis: Literal["horizontal", "vertical"] = "horizontal",
    block_min_size: int = 512,
    block_max_size: int = 768,
    buffer: int = 50,
    threshold: int = 245,
) -> List[bytes]:
    """
    Split an image into segments based on detected spacing/gaps.
    Args:
        input_image: Image data as bytes
        axis: Direction for splitting - 'horizontal' (default) or 'vertical'
        block_min_size: Minimum size of content blocks to keep (in pixels)
        block_max_size: Maximum size of content blocks to keep (in pixels)
        threshold: Binary threshold for content detection (default: 245)
        buffer: Buffer size around detected blocks to include (in pixels)
    Returns:
        List of image segments as bytes (PNG encoded)
    Raises:
        ValueError: If input image cannot be decoded or axis is invalid
    """
    if axis not in ("horizontal", "vertical"):
        raise ValueError(f"Invalid axis: {axis}")
    if block_min_size <= 0:
        raise ValueError("block_min_size must be positive")
    if block_max_size < block_min_size:
        raise ValueError("block_max_size must be greater than block_min_size")
    if buffer < 0:
        raise ValueError("buffer must be non-negative")
    if not (0 <= threshold <= 255):
        raise ValueError("threshold must be between 0 and 255")
    image_array = np.frombuffer(input_image, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode input image from bytes")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    # Sum over rows or columns
    if axis == "horizontal":
        projection = np.sum(binary, axis=1)
    else:
        projection = np.sum(binary, axis=0)

    # Identify split points based on gaps
    blocks = []
    in_block = False
    start = 0

    for i, val in enumerate(projection):
        if val > 0 and not in_block:
            in_block = True
            start = i
        elif (val == 0 or i - start >= block_max_size) and in_block:
            if i - start >= block_min_size:
                end = i
                if axis == "horizontal":
                    max_start = max(0, start - buffer)
                    min_end = min(image.shape[0], end + buffer)
                    crop = image[max_start:min_end, :]
                else:
                    max_start = max(0, start - buffer)
                    min_end = min(image.shape[1], end + buffer)
                    crop = image[:, max_start:min_end]
                success, encoded = cv2.imencode(".png", crop)
                if success:
                    blocks.append(encoded.tobytes())
                else:
                    logfire.info(
                        "Error happening while encoding the image to PNG format"
                    )
                in_block = False
    if in_block:
        end = len(projection)
        if end - start >= block_min_size:
            if axis == "horizontal":
                max_start = max(0, start - buffer)
                min_end = min(image.shape[0], end + buffer)
                crop = image[max_start:min_end, :]
            else:
                max_start = max(0, start - buffer)
                min_end = min(image.shape[1], end + buffer)
                crop = image[:, max_start:min_end]
            success, encoded = cv2.imencode(".png", crop)
            if success:
                blocks.append(encoded.tobytes())
            else:
                logfire.info("Error happening while encoding the image to PNG format")
    return blocks


def save_blocks_as_images(
    blocks: List[bytes], work_dir: str, screen_id: str
) -> list[str]:
    os.makedirs(work_dir, exist_ok=True)  # Ensure the directory exists
    successful_saves = 0
    ret = []
    for i, block in enumerate(blocks):
        # byte_data = block.encode("latin1")
        byte_data = block
        # Convert bytes back to a numpy array
        img_array = np.frombuffer(byte_data, dtype=np.uint8)
        # Decode the image from the array
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        if img is not None:
            # Save the image to file
            filename = os.path.join(work_dir, f"image_{uuid4()}_{screen_id}_{i}.png")
            cv2.imwrite(filename, img)
            ret.append(filename)
            successful_saves += 1
        else:
            logfire.warning(f"Failed to decode image block")
    logfire.info(f"Successfully saved {successful_saves}/{len(blocks)} images")
    return ret
