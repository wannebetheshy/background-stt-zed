import os
from pathlib import Path
import yaml
from pydantic import BaseModel, ConfigDict
from typing import Literal


class Settings(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True, extra="forbid")

    host: str = "127.0.0.1"
    port: int = 8764

    default_model: Literal["whisper_turbo"] = "whisper_turbo"
    default_language: str = "en"

    whisper_initial_prompt: str = ""

    vad_threshold: float = 0.5
    audio_sample_rate: int = 16000
    audio_chunk_ms: int = 100
    partial_interval_s: float = 1.0
    max_buffer_s: float = 30.0

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        if not path.exists():
            return cls()
        with open(path, encoding="utf-8") as f:
            yaml_config: dict = yaml.safe_load(f) or {}
            yaml_config.pop("$schema", None)
            if yaml_config.get("default_model") == "whisper":
                yaml_config["default_model"] = "whisper_turbo"
            yaml_config.pop("whisper_model_size", None)
        return cls.model_validate(yaml_config)


settings_path = os.getenv("SETTINGS_PATH", "settings.yaml")
settings = Settings.from_yaml(Path(settings_path))
