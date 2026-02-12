from dataclasses import dataclass


@dataclass
class Config:
    debug: bool = False
    simple_mode: bool = False
    default_width: int = 1920
    default_height: int = 1080
    default_crf: int = 23
    default_preset: str = "ultrafast"


cfg = Config()


def apply_simple_mode_defaults() -> None:
    """Aktiviert einsteigerfreundliche ressourcenschonende Defaults."""
    cfg.simple_mode = True
    cfg.default_width = 1280
    cfg.default_height = 720
    cfg.default_crf = 24
    cfg.default_preset = "veryfast"
