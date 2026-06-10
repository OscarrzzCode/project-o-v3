import httpx
import time
from src.config import RUNPOD_API_KEY, RUNPOD_BASE_URL, TIMEOUT_RUNSYNC


async def run_comfyui_sync(payload: dict, timeout: int = None) -> dict:
    timeout = timeout or TIMEOUT_RUNSYNC
    url = f"{RUNPOD_BASE_URL}/runsync"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json={"input": payload}, headers=headers)
        response.raise_for_status()
        return response.json()


async def run_comfyui_async(payload: dict, timeout: int = None) -> str:
    timeout = timeout or TIMEOUT_RUNSYNC
    url = f"{RUNPOD_BASE_URL}/run"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json={"input": payload}, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["id"]


async def get_job_status(runpod_job_id: str) -> dict:
    url = f"{RUNPOD_BASE_URL}/status/{runpod_job_id}"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


async def run_comfyui_sync_with_retry(payload: dict, timeout: int = None) -> dict:
    timeout = timeout or TIMEOUT_RUNSYNC
    try:
        return await run_comfyui_sync(payload, timeout)
    except httpx.HTTPStatusError as e:
        error_body = ""
        try:
            error_body = e.response.text
        except Exception:
            pass
        raise RuntimeError(f"RunPod API error {e.response.status_code}: {error_body}") from e


async def health_check() -> dict:
    url = f"{RUNPOD_BASE_URL}/health"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
