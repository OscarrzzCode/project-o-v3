import os
import json
import base64
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image
from io import BytesIO

from src.config import HOST, PORT
from src.models_db import init_db, create_job, update_job_status, get_job, get_jobs
from src.runpod_client import run_comfyui_sync_with_retry, health_check as rp_health
from src.workflow_engine import (
    load_workflow,
    build_payload,
    inject_pulid_params,
    inject_lora_params,
    image_to_data_uri,
)
from src.intent_router import detect_intent
from src.similarity import compute_face_similarity, evaluate_similarity, SIMILARITY_THRESHOLDS
from src.model_registry import get_checkpoints, get_loras, get_upscale_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(title="Project O v3", lifespan=lifespan)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(STATIC_DIR, "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>UI not found</h1>", status_code=404)


@app.get("/health")
async def health():
    result = {"backend": "ok"}
    try:
        rp_health_result = await rp_health()
        result["runpod"] = rp_health_result
    except Exception as e:
        result["runpod"] = {"error": str(e)}
    return result


@app.get("/api/models")
async def api_models():
    return {
        "checkpoints": get_checkpoints(),
        "loras": get_loras(),
        "upscale_models": get_upscale_models(),
        "similarity_thresholds": SIMILARITY_THRESHOLDS,
    }


@app.post("/api/generate")
async def generate(
    ref_image: UploadFile = File(...),
    pose_image: UploadFile = File(None),
    prompt: str = Form(""),
    workflow_override: str = Form(None),
    model_name: str = Form(None),
    lora_name: str = Form(None),
    lora_strength: float = Form(None),
    seed: int = Form(0),
    steps: int = Form(25),
    guidance: float = Form(3.5),
    pulid_weight: float = Form(1.0),
    denoise_strength: float = Form(1.0),
):
    has_pose = pose_image is not None and pose_image.filename != ""

    ref_bytes = await ref_image.read()
    ref_img = Image.open(BytesIO(ref_bytes)).convert("RGB")

    intent = detect_intent(prompt, has_pose)
    workflow_type = workflow_override or intent.workflow_type
    logger.info(
        f"Intent: {workflow_type}, keywords: {intent.keywords_matched},"
        f" needs_2nd: {intent.needs_second_image}"
    )

    if intent.needs_second_image and not has_pose:
        raise HTTPException(
            status_code=400,
            detail=f"This prompt requires a second image ({intent.second_image_label})",
        )

    job_id = await create_job(
        workflow_type=workflow_type,
        model=model_name,
        lora=lora_name,
        lora_strength=lora_strength,
        prompt=prompt,
        seed=seed,
        steps=steps,
        guidance=guidance,
        pulid_weight=pulid_weight,
        denoise_strength=denoise_strength,
    )

    try:
        await update_job_status(job_id, "running")

        workflow = load_workflow(workflow_type)
        workflow["5"]["inputs"]["text"] = prompt or ""
        workflow["8"]["inputs"]["seed"] = seed
        workflow["8"]["inputs"]["steps"] = steps
        workflow["8"]["inputs"]["denoise"] = denoise_strength
        workflow = inject_pulid_params(workflow, pulid_weight)

        if lora_name:
            workflow = inject_lora_params(workflow, lora_name, lora_strength)

        images = [{"name": "input_image_1.png", "image": base64.b64encode(ref_bytes).decode()}]
        if has_pose:
            pose_bytes = await pose_image.read()
            images.append({"name": f"{workflow_type}_pose.png", "image": pose_bytes})

        payload = build_payload(workflow, images)
        result = await run_comfyui_sync_with_retry(payload)

        output_images = result.get("output", {}).get("images", [])
        errors = result.get("output", {}).get("errors", [])

        s3_urls = []
        gen_img = None
        for img in output_images:
            if img.get("type") == "s3_url":
                s3_urls.append(img.get("data", ""))
            elif img.get("type") == "base64":
                s3_urls.append(img.get("data", ""))

        similarity_score = None
        similarity_label = "unknown"

        if output_images and len(output_images) > 0:
            try:
                first_img = output_images[0]
                if first_img.get("type") == "base64":
                    img_data = first_img.get("data", "")
                    if img_data:
                        if img_data.startswith("data:"):
                            img_data = img_data.split(",", 1)[1]
                        gen_bytes = base64.b64decode(img_data)
                        gen_img = Image.open(BytesIO(gen_bytes)).convert("RGB")
                elif first_img.get("type") == "s3_url":
                    import httpx
                    s3_url = first_img.get("data", "")
                    if s3_url:
                        async with httpx.AsyncClient(timeout=30) as client:
                            resp = await client.get(s3_url)
                            resp.raise_for_status()
                            gen_img = Image.open(BytesIO(resp.content)).convert("RGB")
            except Exception as e:
                logger.warning(f"Failed to load generated image for similarity: {e}")

        if gen_img and ref_img:
            similarity_score = compute_face_similarity(ref_img, gen_img)
            similarity_label = evaluate_similarity(similarity_score)

        execution_time = result.get("executionTime", 0)

        await update_job_status(
            job_id,
            "completed",
            s3_urls=json.dumps(s3_urls) if s3_urls else None,
            similarity_score=similarity_score,
            execution_time_ms=execution_time,
            error=json.dumps(errors) if errors else None,
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "workflow_type": workflow_type,
            "intent": {
                "detected": intent.workflow_type,
                "keywords": intent.keywords_matched,
                "needs_second_image": intent.needs_second_image,
            },
            "output": {
                "images": output_images,
                "errors": errors,
            },
            "similarity": {
                "score": similarity_score,
                "label": similarity_label,
            },
            "execution_time_ms": execution_time,
        }

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        await update_job_status(job_id, "failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
async def api_jobs(limit: int = 50):
    jobs = await get_jobs(limit)
    for job in jobs:
        if job.get("s3_urls"):
            try:
                job["s3_urls_parsed"] = json.loads(job["s3_urls"])
            except Exception:
                job["s3_urls_parsed"] = []
    return {"jobs": jobs}


@app.get("/api/jobs/{job_id}")
async def api_job_detail(job_id: str):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("s3_urls"):
        try:
            job["s3_urls_parsed"] = json.loads(job["s3_urls"])
        except Exception:
            job["s3_urls_parsed"] = []
    return job


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app" if __name__ != "__main__" else "main:app",
        host=HOST,
        port=PORT,
        reload=True,
    )
