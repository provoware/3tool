from dataclasses import dataclass


@dataclass
class Config:
    debug: bool = False


cfg = Config()
