# Project O v3 — Identity-Preserving Character Editor

RunPod serverless + FLUX.1 Dev + PuLID face identity locking + web UI.

## Architecture

```
Browser → Render (free) → RunPod Serverless GPU (A6000)
               ↑                      ↑
          FastAPI backend        Network Volume
          + SQLite jobs          (models stored here)
          + Web UI                   ↓
                                AWS S3 (output)
```

## Tech Stack

| Layer | Component |
|---|---|
| Base Model | FLUX.1 Dev FP8 |
| Identity | PuLID-FLUX v0.9.1 |
| Pose | DWPose |
| Face Analysis | InsightFace / ArcFace (CPU-side) |
| NSFW | LoRA on top of FLUX |
| Web UI | HTML/CSS/JS + FastAPI backend |

## Workflows

| Workflow | Input | Description |
|---|---|---|
| `outfit` | 1 reference image + prompt | PuLID identity lock + FLUX generation |
| `pose` | 1 reference + 1 pose image + prompt | PuLID + DWPose skeleton-guided generation |
| `identity_lock` | 1 reference image + prompt | Two-pass: generate → face-detect → refine face |

## Quick Start

### 1. Clone & Install

```bash
git clone <this-repo>
cd project-o-v3
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your RunPod API key and endpoint ID
```

### 2. Run Backend Locally

```bash
python -m src.main
# Open http://localhost:8000
```

### 3. Deploy to RunPod (GPU Worker)

1. Create a RunPod Network Volume (50GB+)
2. Upload models to the volume:
   ```
   /runpod-volume/models/
   ├── diffusion_models/flux1-dev-fp8.safetensors
   ├── clip/t5xxl_fp8_e4m3fn.safetensors
   ├── clip/clip_l.safetensors
   ├── vae/ae.safetensors
   ├── pulid/pulid_flux_v0.9.1.safetensors
   ├── controlnet/dwpose/
   ├── insightface/models/
   └── loras/nsfw_unlock_flux_v1.safetensors
   ```
3. Create a RunPod Serverless Template:
   - Container Image: point to this repo's Dockerfile (GitHub integration)
   - Container Disk: 30GB
   - Environment: `REFRESH_WORKER=true`
4. Create Serverless Endpoint:
   - GPU: A6000 or A100
   - Attach Network Volume
   - Flash Boot: enabled
   - Min Workers: 0, Max Workers: 3

### 4. Deploy Backend (Render)

1. Connect this repo to Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
4. Set environment variables from `.env.example`

## Model Downloads

```bash
# FLUX.1 Dev FP8
wget https://huggingface.co/XLabs-AI/flux-dev-fp8/resolve/main/flux-dev-fp8.safetensors

# T5 XXL FP8
wget https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors

# CLIP-L
wget https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors

# VAE
wget https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors

# PuLID-FLUX v0.9.1
wget https://huggingface.co/guozinan/PuLID/resolve/main/pulid_flux_v0.9.1.safetensors

# InsightFace (download and unzip to insightface/models/)
# https://huggingface.co/MonsterMMORPG/tools/tree/main
```

## Environment Variables

```bash
RUNPOD_API_KEY=          # From RunPod Settings → API Keys
RUNPOD_ENDPOINT_ID=      # From RunPod Endpoints → your endpoint
BUCKET_ENDPOINT_URL=     # AWS S3 endpoint
BUCKET_ACCESS_KEY_ID=    # AWS IAM access key
BUCKET_SECRET_ACCESS_KEY=# AWS IAM secret key
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Backend + RunPod health check |
| GET | `/api/models` | Available checkpoints, LoRAs, upscalers |
| POST | `/api/generate` | Generate image (multipart form) |
| GET | `/api/jobs` | List recent jobs |
| GET | `/api/jobs/{id}` | Job detail |

## Project Structure

```
project-o-v3/
├── Dockerfile              # RunPod serverless worker
├── Dockerfile.backend      # Render backend
├── requirements.txt
├── .env.example
├── models_config.json      # Editable model registry
├── workflows/
│   ├── outfit.json         # PuLID + FLUX
│   ├── pose.json           # PuLID + DWPose + FLUX
│   └── identity_lock.json  # Two-pass identity lock
└── src/
    ├── main.py             # FastAPI server
    ├── config.py           # Env var loading
    ├── models_db.py        # SQLite job store
    ├── runpod_client.py    # RunPod API client
    ├── workflow_engine.py  # JSON loader + param injection
    ├── intent_router.py    # Prompt → workflow routing
    ├── similarity.py       # Face similarity (InsightFace)
    ├── model_registry.py   # Model config reader
    └── static/
        ├── index.html
        ├── style.css
        └── app.js
```
