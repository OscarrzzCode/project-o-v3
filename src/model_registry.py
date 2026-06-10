import json
from pathlib import Path
from src.config import MODELS_CONFIG_PATH

_registry_cache = None


def load_registry() -> dict:
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache
    path = Path(MODELS_CONFIG_PATH)
    if not path.exists():
        return {"checkpoints": [], "loras": [], "upscale_models": []}
    with open(path, "r", encoding="utf-8") as f:
        _registry_cache = json.load(f)
    return _registry_cache


def get_checkpoints() -> list:
    return load_registry().get("checkpoints", [])


def get_loras() -> list:
    return load_registry().get("loras", [])


def get_upscale_models() -> list:
    return load_registry().get("upscale_models", [])


def get_checkpoint_by_name(name: str) -> dict | None:
    for ckpt in get_checkpoints():
        if ckpt["name"] == name:
            return ckpt
    return None


def get_lora_by_name(name: str) -> dict | None:
    for lora in get_loras():
        if lora["name"] == name:
            return lora
    return None
