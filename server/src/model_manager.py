import gc
import torch
import asyncio
from typing import Optional

from src.engines import ENGINE_REGISTRY
from src.engines.base import STTEngine


class ModelManager:
    def __init__(self):
        self.active_engine: Optional[STTEngine] = None
        self._lock = asyncio.Lock()

    def load_model(self, model_name: str, language: str) -> None:
        if model_name not in ENGINE_REGISTRY:
            raise ValueError(f"Unknown model name: {model_name}")

        # If already loaded the exact same model, maybe just update language?
        # For simplicity, we just reload if model_name differs or we force it.
        # It's better to always do a clean load for MVP predictability.
        self.unload()

        print(f"Loading model {model_name} for language {language}...")
        engine_cls = ENGINE_REGISTRY[model_name]
        engine = engine_cls()
        engine.load(language)
        self.active_engine = engine
        print(f"Model {model_name} loaded successfully.")

    def unload(self) -> None:
        if self.active_engine is not None:
            print("Unloading active model...")
            self.active_engine.unload()
            self.active_engine = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("Model unloaded and VRAM cleared.")

    def get_status(self) -> dict:
        if self.active_engine is None:
            return {
                "model": None,
                "language": None,
                "vram_estimate_mb": 0,
                "available_models": list(ENGINE_REGISTRY.keys())
            }

        info = self.active_engine.get_info()
        # Retrieve actual VRAM usage if possible
        vram_used_mb = 0
        vram_total_mb = 0
        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            vram_used_mb = (total - free) // (1024 * 1024)
            vram_total_mb = total // (1024 * 1024)
        else:
            vram_used_mb = info.vram_estimate_mb

        return {
            "model": info.name,
            "language": self.active_engine._language if hasattr(self.active_engine, '_language') else None,
            # Hacky, but works for MVP
            "vram_used_mb": vram_used_mb,
            "vram_total_mb": vram_total_mb,
            "available_models": list(ENGINE_REGISTRY.keys())
        }


model_manager = ModelManager()
