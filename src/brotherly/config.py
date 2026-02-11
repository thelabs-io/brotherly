"""Configuration management."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "brotherly" / "config.json5"
DEFAULT_DATA_DIR = Path.home() / ".brotherly"


def _parse_json5(text: str) -> dict:
    """Parse JSON5 by stripping // comments and trailing commas."""
    result = []
    i = 0
    in_string = False
    while i < len(text):
        if text[i] == '"' and (i == 0 or text[i - 1] != "\\"):
            in_string = not in_string
            result.append(text[i])
        elif not in_string and text[i : i + 2] == "//":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        else:
            result.append(text[i])
        i += 1
    cleaned = "".join(result)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return json.loads(cleaned)


@dataclass
class Config:
    data_dir: Path = field(default_factory=lambda: DEFAULT_DATA_DIR)
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
            config_path = CONFIG_PATH

        if not config_path.exists():
            cfg = cls()
            cfg.ensure_dirs()
            return cfg

        data = _parse_json5(config_path.read_text())

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
