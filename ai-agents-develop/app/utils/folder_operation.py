import shutil
from pathlib import Path
from uuid import UUID

USER_DATA_FOLDER = Path("./UserData")


def construct_control_execution_folder(
    control_id: UUID, entity_id: UUID, control_exec_id: UUID
) -> Path:
    return USER_DATA_FOLDER / str(control_id) / str(entity_id) / str(control_exec_id)


def setup_control_execution_folder_for_rerun(
    control_execution_folder: Path, start_index: int
) -> None:
    """
    Setup the control execution folder for rerun.

    Args:
        control_execution_folder: The folder of the control execution
        start_index: The action index to start from
    """

    if not control_execution_folder.exists():
        raise FileNotFoundError(
            f"Control execution folder {control_execution_folder} not found when setting up for rerun"
        )

    # Delete all subfolders whose name is "{action name}_{n}" where n >= start_index
    for f in control_execution_folder.iterdir():
        if f.is_dir():
            try:
                n = int(f.name.split("_")[1])
                if n >= start_index:
                    shutil.rmtree(f, ignore_errors=True)
            except (IndexError, ValueError):
                # Not a valid action folder, skip
                continue
