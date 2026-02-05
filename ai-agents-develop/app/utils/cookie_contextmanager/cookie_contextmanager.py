import json
import os
import tempfile
from contextlib import contextmanager

import logfire


@contextmanager
def cookie_file_from_json_str(json_str: str, result_holder: dict):
    """
    Create a temporary cookie file from a json string.
    The tool can now read/update this file.
    result_holder is a mutable object that will hold the updated cookie string.
    """
    cookie_obj = json.loads(json_str)

    # Create a temporary file in the system temp dir
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w+", encoding="utf-8"
    ) as tmp:
        tmp_file = tmp.name
        try:
            # Write the initial cookie content
            json.dump(cookie_obj, tmp)
            tmp.flush()
            os.fsync(tmp.fileno())  # ensure content is written to disk
        except Exception as e:
            logfire.exception("Failed to write temp cookie file", exception=e)
            tmp.close()
            os.unlink(tmp_file)
            raise

    try:
        yield tmp_file

        # Read updated content back into result_holder
        with open(tmp_file, "r", encoding="utf-8") as f:
            result_holder["cookie"] = f.read()

    finally:
        os.unlink(tmp_file)
