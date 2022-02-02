from typing import Any
import yaml

def load(name: str) -> Any:
    with open(name, 'r') as file:
        return yaml.safe_load(file)

def get_id_map_by_key(key: str):
    return id_maps[key]

id_maps = load("data/map/id.yml")
