import os


def save_locally(data: str, work_dir: str, name: str) -> None:
    """
    Save the given data as a file in the specified working directory with the given name.

    Args:
        data (str): The content to save.
        work_dir (str): The directory where the file will be saved.
        name (str): The name of the file to save.
    """
    try:
        os.makedirs(work_dir, exist_ok=True)  # Ensure the directory exists
        filename = os.path.join(work_dir, name)
        with open(filename, "w", encoding="utf-8") as file:
            file.write(data)
    except Exception as e:
        raise IOError(f"Failed to save file {name} in {work_dir}: {e}") from e
