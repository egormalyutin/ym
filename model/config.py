from dataclasses import dataclass


@dataclass
class Config:
    cache_dir: str
    ym_token: str
