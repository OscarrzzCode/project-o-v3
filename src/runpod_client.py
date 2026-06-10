import httpx
import asyncio
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


async def run_async(payload: dict) -> str:
    url = f"{RUNPOD_BASE_URL}/run"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json={"input": payload}, headers=headers)
        response.raise_for_status()
        return response.json()["id"]


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
    except (httpx.HTTPStatusError, httpx.ReadTimeout):
        pass

    job_id = await run_async(payload)
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            status = await get_job_status(job_id)
        except httpx.HTTPStatusError:
            await asyncio.sleep(2)
            continue

        if status.get("status") in ("COMPLETED", "FAILED"):
            return status
        await asyncio.sleep(2)

    raise RuntimeError(f"Job {job_id} timed out after {timeout}s")


async def health_check() -> dict:
    url = f"{RUNPOD_BASE_URL}/health"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
