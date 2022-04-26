from typing import Dict, Hashable, Any, Union

import yaml


PulumiStackConfig = Union[Dict[Hashable, Any], list, None]


def read(config_file_path: str) -> PulumiStackConfig:
    with open(config_file_path, 'r') as f:
        return yaml.safe_load(f)
