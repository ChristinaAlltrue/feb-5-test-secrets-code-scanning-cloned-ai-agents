from pathlib import Path

import logfire
from alltrue.agents.schema.predefined import Framework
from pydantic import ValidationError
from yaml import YAMLError

from app.utils.yaml_loader.loader import YamlLoader


def load_all_predefined_frameworks(
    base_dir: str = "./app/predefined_framework/activate",
):
    base_path = Path(base_dir)
    all_frameworks = []

    # Iterate over all directories in the base path, each directory contains a framework
    for framework_dir in base_path.iterdir():
        # Load first level, second level files are control files
        if not framework_dir.is_dir():
            continue

        for yaml_file in framework_dir.iterdir():
            if yaml_file.is_file() and yaml_file.suffix == ".yaml":
                try:
                    raw = YamlLoader.load(yaml_file)
                    model = Framework(**raw)
                    all_frameworks.append(model)
                except (ValueError, ValidationError, YAMLError) as err:
                    logfire.error(f"Failed to load {yaml_file}", exc_info=err)

    return all_frameworks
