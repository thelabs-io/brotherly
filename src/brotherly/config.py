"""Configuration management."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    data_dir: Path = field(default_factory=lambda: Path.cwd())
    z2_host: str = "zara2stra.duckdns.org"
    z2_port: int = 22440
    z2_user: str = "chris"
    phone_number: str = "+19203858522"
    z2_log_dir: str = "~/Bros/brotherly/logs"

    @property
    def queue_dir(self) -> Path:
        return self.data_dir / "queue"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    def ensure_dirs(self) -> None:
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls, config_path: Path | None = None) -> Config:
        if config_path is None:
            config_path = Path.cwd() / "config.toml"

        if not config_path.exists():
            cfg = cls()
            cfg.ensure_dirs()
            return cfg

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        kwargs = {}
        if "data_dir" in data:
            kwargs["data_dir"] = Path(data["data_dir"]).expanduser()
        if "z2" in data:
            z2 = data["z2"]
            if "host" in z2:
                kwargs["z2_host"] = z2["host"]
            if "port" in z2:
                kwargs["z2_port"] = z2["port"]
            if "user" in z2:
                kwargs["z2_user"] = z2["user"]
            if "log_dir" in z2:
                kwargs["z2_log_dir"] = z2["log_dir"]
        if "phone_number" in data:
            kwargs["phone_number"] = data["phone_number"]

        cfg = cls(**kwargs)
        cfg.ensure_dirs()
        return cfg
