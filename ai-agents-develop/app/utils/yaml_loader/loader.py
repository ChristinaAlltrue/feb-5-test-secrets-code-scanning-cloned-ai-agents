from pathlib import Path
from typing import Any, Union

import yaml
from yaml.nodes import ScalarNode


class _Loader(yaml.SafeLoader):
    _root: Path


class YamlLoader:
    @staticmethod
    def _include(loader: _Loader, node: ScalarNode) -> Any:
        relative_path = loader.construct_scalar(node)
        # Resolve the path relative to the root of the framework
        full_path = (loader._root / relative_path).resolve()
        with open(full_path, "r") as f:
            previous_root = _Loader._root
            _Loader._root = full_path.parent
            try:
                return yaml.load(f, Loader=_Loader)
            finally:
                # Restore the previous root to support nested includes
                _Loader._root = previous_root

    @classmethod
    def load(cls, path: Union[str, Path]) -> dict:
        path = Path(path).resolve()
        with open(path, "r") as f:
            _Loader._root = path.parent
            _Loader.add_constructor("!include", cls._include)
            return yaml.load(f, Loader=_Loader)
