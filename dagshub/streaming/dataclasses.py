from dataclasses import dataclass


@dataclass
class Storage:
    name: str
    protocol: str
    list_path: str
