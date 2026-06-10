import json
import base64
import os
from io import BytesIO
from pathlib import Path
from PIL import Image
from src.config import WORKFLOWS_DIR


WORKFLOW_MAP = {
    "outfit": "outfit.json",
    "pose": "pose.json",
    "identity_lock": "identity_lock.json",
    "upscale": "upscale.json",
}


def encode_image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    buffer = BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def image_to_data_uri(image: Image.Image, format: str = "PNG") -> str:
    b64 = encode_image_to_base64(image, format)
    return f"data:image/{format.lower()};base64,{b64}"


def load_workflow(workflow_name: str) -> dict:
    filename = WORKFLOW_MAP.get(workflow_name)
    if not filename:
        raise ValueError(f"Unknown workflow: {workflow_name}. Available: {list(WORKFLOW_MAP.keys())}")
    path = Path(WORKFLOWS_DIR) / filename
    if not path.exists():
        raise FileNotFoundError(f"Workflow file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_payload(
    workflow: dict,
    images: list[dict],
    params: dict = None,
) -> dict:
    params = params or {}
    payload_images = []
    for img_data in images:
        if isinstance(img_data.get("image"), Image.Image):
            b64 = encode_image_to_base64(img_data["image"])
        elif isinstance(img_data.get("image"), str):
            b64 = img_data["image"]
        else:
            continue
        payload_images.append({
            "name": img_data.get("name", "input.png"),
            "image": b64,
        })

    return {
        "workflow": workflow,
        "images": payload_images,
    }


def inject_pulid_params(workflow: dict, pulid_weight: float = 1.0, start_timestep: int = 0) -> dict:
    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        inputs = node.get("inputs", {})
        if "PuLID" in class_type or "pulid" in class_type.lower():
            if "weight" in inputs:
                inputs["weight"] = pulid_weight
            if "start_at" in inputs:
                inputs["start_at"] = start_timestep / 100.0
            if "method" in inputs:
                inputs["method"] = "fidelity"
    return workflow


def inject_lora_params(workflow: dict, lora_name: str, lora_strength: float = 0.7) -> dict:
    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        inputs = node.get("inputs", {})
        if "LoraLoader" in class_type or "FluxLoraLoader" in class_type:
            if "lora_name" in inputs:
                inputs["lora_name"] = lora_name
            if "strength_model" in inputs:
                inputs["strength_model"] = lora_strength
    return workflow
