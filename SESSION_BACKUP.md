# Project O — Session Complete Backup

> **Date:** 2026-06-11/12  
> **Purpose:** Full record for continuing in a new conversation without repeating work.

---

## 1. Project Vision

### Product: Identity-Preserving Character Editor

A web-based character editing platform that transforms an existing character while maintaining facial identity consistency.

**Core Principle:** Identity preservation above all else.

### Features (Priority Order)
1. Face similarity preservation (PuLID-FLUX)
2. Outfit modification
3. Pose modification
4. Background replacement
5. Expression adjustments
6. NSFW content support (key requirement)
7. Asian face optimization

### Technology Stack
| Layer | Component | Status |
|---|---|---|
| Base Model | FLUX.1 Dev (FP8) | ✅ Working |
| Identity | PuLID-FLUX v0.9.1 | ⏳ In progress (runtime bug) |
| Face Analysis | InsightFace (antelopev2) | ✅ Working |
| Pose (future) | DWPose | Not started |
| NSFW | LoRA on FLUX | Not started |
| Web UI | HTML/CSS/JS | ✅ Working |
| Backend | FastAPI + SQLite | ✅ Working |

---

## 2. Architecture Evolution & Key Decisions

### Decision 1: Serverless → GPU Pod
**Original:** RunPod Serverless endpoint with `worker-comfyui`  
**Final:** RunPod GPU Pod with standard ComfyUI

**Why changed:**
- Serverless = black box (no SSH, no logs, can't debug)
- `worker-comfyui` is a non-standard ComfyUI wrapper
- PuLID extension is incompatible with worker-comfyui
- Could not see error messages when PuLID crashed
- Pod gives full SSH + ComfyUI log access

### Decision 2: Docker Models → Network Volume Models
**Original:** All models baked into Docker image (85GB)  
**Final:** Docker = environment only (~3GB), Volume = all data

**Why changed:**
- 85GB images take 10+ min to build, 30+ min to download
- Every model change requires Docker rebuild
- Volume survives pod restarts permanently
- Models downloaded once, available forever
- SSH can modify anything on volume instantly

### Decision 3: PuLID over IP-Adapter
**Original:** Considered IP-Adapter for face identity  
**Final:** PuLID-FLUX (superior identity preservation)

**Why:**
- PuLID specifically trained for face ID (90-95% similarity)
- IP-Adapter is general-purpose image conditioning (70-80%)
- PuLID uses EVA CLIP for face encoding
- User's primary requirement is face similarity

### Decision 4: Pod with Auto-Stop (10 min) over Always-Warm
**Cost:** ~$0.25-0.50/day for casual testing
- Pod stops after 10 min idle → $0 cost
- First generation after idle: ~2 min pod boot
- Warm: instant generation
- If always warm: $0.40/hr ($9.60/day)

### Decision 5: PuLID-FLUX Extension Choice
**Extension:** `balazik/ComfyUI-PuLID-Flux` (GitHub)
**Node types verified:**
- `PulidFluxModelLoader` — input: `pulid_file` (looks in `models/pulid/`)
- `PulidFluxInsightFaceLoader` — input: `provider` (CPU/CUDA)
- `PulidFluxEvaClipLoader` — auto-downloads EVA02-CLIP-L-14-336
- `ApplyPulidFlux` — inputs: `model`, `pulid_flux`, `eva_clip`, `face_analysis`, `image`, `weight`, `start_at`, `end_at`

---

## 3. Infrastructure: RunPod

### Account
- **Username:** OscarrzzCode (GitHub), oscarrzz (Docker Hub)
- **API Key:** See `.env` file (`RUNPOD_API_KEY`)
- **Docker Hub Token:** See `.env` file or Docker Desktop credential store
- **HuggingFace Token:** See `.env` file (must have "Access public gated repositories" enabled)
- **SSH Key:** `C:\Users\ACSNB-04\.ssh\rp_pulid`

### Network Volume
- **ID:** `7wb7pc6tzt`
- **Name:** `high_salmon_cod`
- **Region:** EUR-IS-1
- **Size:** 50GB

### Docker Hub Images
| Image | Size | Purpose |
|---|---|---|
| `oscarrzz/project-o:latest` | ~3GB | Clean: ComfyUI + tools, no models |
| `oscarrzz/worker-comfyui-pulid:latest` | ~85GB | Old: full image (deprecated) |
| `runpod/worker-comfyui:5.8.5-flux1-dev` | ~25GB | Reference: has VAE baked in |

### Templates
- **Project-O-Flux:** `64g6zvvpcs` — still points to `oscarrzz/worker-comfyui-pulid:latest` (can be reused)

### Serverless Endpoints (All Deleted)
Last working: `t8om2wordly20e` (used `runpod/worker-comfyui:5.8.5-flux1-dev`, basic FLUX worked)

### GPU Availability Issue
EUR-IS-1 has unpredictable GPU availability for Ampere/Ada 48GB GPUs. Currently only Blackwell GPUs are available (RTX PRO 6000, 96GB). Blackwell needs PyTorch 2.5+.

---

## 4. Network Volume Contents

```
/workspace/                           (RunPod mount: high_salmon_cod)
│
├── models/
│   ├── diffusion_models/
│   │   └── flux-dev-fp8.safetensors         (12GB, FP8 FLUX model)
│   ├── clip/
│   │   ├── t5xxl_fp8_e4m3fn.safetensors     (4.6GB, T5 text encoder)
│   │   └── clip_l.safetensors               (235MB, CLIP-L)
│   ├── vae/
│   │   └── ae.safetensors                   (320MB, FLUX VAE)
│   ├── pulid/
│   │   └── pulid_flux_v0.9.1.safetensors    (1.1GB, PuLID model)
│   └── insightface/
│       └── models/
│           └── antelopev2/                   (Face detection models)
│
├── ComfyUI/                       (cloned from GitHub)
│   ├── main.py
│   ├── models/                    (symlinks to /workspace/models/)
│   │   ├── unet/flux1-dev.safetensors → ../../models/diffusion_models/flux-dev-fp8.safetensors
│   │   ├── vae/ae.safetensors → ../../models/vae/ae.safetensors
│   │   ├── clip/t5xxl_fp8_e4m3fn.safetensors → ../../models/clip/t5xxl_fp8_e4m3fn.safetensors
│   │   ├── clip/clip_l.safetensors → ../../models/clip/clip_l.safetensors
│   │   └── pulid/pulid_flux_v0.9.1.safetensors → ../../models/pulid/pulid_flux_v0.9.1.safetensors
│   └── custom_nodes/
│       └── ComfyUI-PuLID-Flux/    (balazik extension)
│
├── startup.sh                    (legacy — from earlier Docker builds)
└── custom_nodes/
    └── ComfyUI-PuLID-Flux/       (symlinked to ComfyUI custom_nodes)
```

---

## 5. Current State & Blocking Issue

### What Works
- ✅ Web UI: localhost:8000 (FastAPI + static files)
- ✅ Backend: image upload, prompt routing, RunPod API calls
- ✅ Basic FLUX img2img (denoise 0.45, identity prompt)
- ✅ Job tracking: SQLite database
- ✅ VAE download: 320MB on volume (HF token now works)
- ✅ All models on volume: FLUX, CLIP, T5, VAE, PuLID
- ✅ ComfyUI + PuLID installed on volume
- ✅ Pod creation/management via RunPod REST API

### What Doesn't Work
- ❌ PuLID-FLUX generation (never successfully tested)
- ❌ Serverless endpoint deployment (region GPU supply)
- ❌ Docker-in-Docker on RunPod (dockerd won't start)
- ❌ RunPod SSH: unreliable (connection drops on long ops)

### Current Blocking Issue
**Blackwell GPU (RTX PRO 6000) + PyTorch 2.4 incompatibility**

RunPod currently only offers Blackwell GPUs. PyTorch 2.4.1 supports up to sm_90 (Hopper). Blackwell needs sm_120+ (PyTorch 2.5+).

**Fix (tested):** `pip install --upgrade torch` → PyTorch 2.12.0 installs and CUDA works

---

## 6. Boot Sequence for Pod

### Manual Startup (Web Terminal — most reliable)
```bash
# 1. Upgrade PyTorch for Blackwell
pip install --upgrade torch torchvision torchaudio -q

# 2. Reinstall ComfyUI dependencies
pip install -q -r /workspace/ComfyUI/requirements.txt

# 3. Install additional deps
pip install -q timm facexlib insightface onnxruntime opencv-python einops

# 4. Start ComfyUI
cd /workspace/ComfyUI
nohup python3 main.py --listen 0.0.0.0 --port 8188 &>/tmp/cf.log &
sleep 25 && curl -s http://localhost:8188/queue
```

### Expected Queue Response
```json
{"queue_running": [], "queue_pending": []}
```

### Automated startup.sh (to be created on volume)
```bash
#!/bin/bash
set -e

# Upgrade PyTorch for Blackwell GPU compatibility
python3 -c "import torch; exit(0 if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 9 else 1)" 2>/dev/null \
  || pip install --upgrade torch torchvision torchaudio -q

# Link models
mkdir -p /workspace/ComfyUI/models/{unet,vae,clip,pulid}
ln -sf /workspace/models/diffusion_models/flux-dev-fp8.safetensors /workspace/ComfyUI/models/unet/flux1-dev.safetensors
ln -sf /workspace/models/vae/ae.safetensors /workspace/ComfyUI/models/vae/ae.safetensors
ln -sf /workspace/models/clip/t5xxl_fp8_e4m3fn.safetensors /workspace/ComfyUI/models/clip/t5xxl_fp8_e4m3fn.safetensors
ln -sf /workspace/models/clip/clip_l.safetensors /workspace/ComfyUI/models/clip/clip_l.safetensors
ln -sf /workspace/models/pulid/pulid_flux_v0.9.1.safetensors /workspace/ComfyUI/models/pulid/pulid_flux_v0.9.1.safetensors

# Install deps
pip install -q -r /workspace/ComfyUI/requirements.txt
pip install -q timm facexlib insightface onnxruntime opencv-python einops

# Install PuLID extension requirements
cd /workspace/ComfyUI/custom_nodes/ComfyUI-PuLID-Flux
pip install -q -r requirements.txt || true

# Start ComfyUI
cd /workspace/ComfyUI
echo "Starting ComfyUI on port 8188..."
exec python3 main.py --listen 0.0.0.0 --port 8188
```

---

## 7. Technical Reference: ComfyUI Nodes

### PuLID-FLUX Node Types (balazik/ComfyUI-PuLID-Flux)
Source: custom_nodes/ComfyUI-PuLID-Flux/pulidflux.py

| Class Type | Inputs | Purpose |
|---|---|---|
| `PulidFluxModelLoader` | `pulid_file` | Loads PuLID model from `models/pulid/` |
| `PulidFluxInsightFaceLoader` | `provider` (CPU/CUDA/ROCM) | Loads InsightFace antelopev2 |
| `PulidFluxEvaClipLoader` | `image` | Loads EVA02-CLIP-L-14-336, extracts face features |
| `ApplyPulidFlux` | `model`, `pulid_flux`, `eva_clip`, `face_analysis`, `image`, `weight`, `start_at`, `end_at` | Patches FLUX DiT with identity conditioning |

### Standard ComfyUI Nodes Used
- `LoadImage` — `image` (filename)
- `UNETLoader` — `unet_name`, `weight_dtype`
- `DualCLIPLoader` — `clip_name1`, `clip_name2`, `type`
- `VAELoader` — `vae_name`
- `CLIPTextEncode` — `text`, `clip`
- `KSampler` — `seed`, `steps`, `cfg`, `sampler_name`, `scheduler`, `denoise`, `model`, `positive`, `negative`, `latent_image`
- `VAEDecode` — `samples`, `vae`
- `SaveImage` — `images`, `filename_prefix`
- `EmptyLatentImage` — `width`, `height`, `batch_size`
- `ConditioningConcat` — `conditioning_from`, `conditioning_to`

---

## 8. Project Files Reference

### Files on Local Machine
```
C:\Users\ACSNB-04\Desktop\Project O\project-o-v3\
│
├── .env                                    # API keys + endpoint IDs (not in git)
├── .env.example                            # Template
├── .gitignore                              # Excludes .env, data/, .db files
├── Dockerfile                              # Clean: ComfyUI + tools (3GB image)
├── startup.sh                              # Pod boot script
├── requirements.txt                        # Python backend deps
├── models_config.json                      # Checkpoint/LoRA registry
├── README.md
│
├── workflows/
│   ├── outfit.json                         # PuLID + FLUX (node 5-16 IDs)
│   ├── pose.json                           # Same structure (placeholder)
│   └── identity_lock.json                  # Same structure (placeholder)
│
├── src/
│   ├── __init__.py
│   ├── config.py                           # Env vars loaded from .env via dotenv
│   ├── main.py                             # FastAPI server (upload, generate, /health, /jobs)
│   ├── models_db.py                        # SQLite: jobs table
│   ├── runpod_client.py                    # RunPod API (runsync, run, health_check)
│   ├── workflow_engine.py                  # Load JSON, build payload, inject params
│   ├── intent_router.py                    # Prompt → workflow routing
│   ├── similarity.py                       # Face similarity (InsightFace, CPU-side)
│   ├── model_registry.py                   # Read models_config.json
│   └── static/
│       ├── index.html                      # Web UI
│       ├── style.css                       # Dark theme
│       └── app.js                          # Upload, generate, display results
│
├── scripts/
│   └── download_models.sh                  # Model download script
│
└── .github/workflows/
    └── build-docker.yml                    # CI: build + push Docker to GHCR
```

### Key Code Details

**workflows/outfit.json** — PuLID + FLUX:
- Node 1: LoadImage
- Node 2: UNETLoader (flux1-dev.safetensors)
- Node 3: DualCLIPLoader (t5 + clip_l)
- Node 4: VAELoader (ae.safetensors)
- Node 5: PulidFluxModelLoader (pulid_file)
- Node 6: PulidFluxInsightFaceLoader (provider: CPU)
- Node 7: PulidFluxEvaClipLoader (image from node 1)
- Node 8: ApplyPulidFlux (connects: model, pulid_flux, eva_clip, face_analysis, image)
- Node 9: CLIPTextEncode (identity prompt)
- Node 10: CLIPTextEncode (edit prompt)
- Node 11: CLIPTextEncode (negative)
- Node 12: ConditioningConcat (9+10)
- Node 13: KSampler (from ApplyPulidFlux output)
- Node 14: EmptyLatentImage
- Node 15: VAEDecode
- Node 16: SaveImage

**main.py** — Key routes:
- `GET /` — Web UI
- `POST /api/generate` — Upload image + prompt → generate via RunPod
- `GET /api/jobs` — List recent jobs
- `GET /api/jobs/{id}` — Job detail
- `GET /health` — Backend + RunPod health
- `GET /api/models` — Model registry

**main.py** — Workflow parameter injection (lines ~123-127):
```python
workflow["7"]["inputs"]["image"] = ["1", 0]  # EVA CLIP
workflow["5"]["inputs"]["pulid_file"] = "pulid_flux_v0.9.1.safetensors"
workflow["8"]["inputs"]["weight"] = pulid_weight
workflow["10"]["inputs"]["text"] = prompt or ""
workflow["13"]["inputs"]["seed"] = seed
workflow["13"]["inputs"]["steps"] = steps
workflow["13"]["inputs"]["denoise"] = denoise_strength
```

---

## 9. Known Issues & Fixes

| Issue | Fix |
|---|---|
| HF token "Access public gated repositories" | Go to https://huggingface.co/settings/tokens → Edit token → enable the checkbox |
| VAE download fails (403) | Above HF token fix + accept FLUX.1-dev license at https://huggingface.co/black-forest-labs/FLUX.1-dev |
| Blackwell GPU: CUDA error (no kernel image) | `pip install --upgrade torch` → installs PyTorch 2.12+ |
| ComfyUI: `ModuleNotFoundError: No module named 'sqlalchemy'` | `pip install sqlalchemy` |
| ComfyUI: `ModuleNotFoundError: No module named 'transformers'` | `pip install transformers` |
| ComfyUI: `ModuleNotFoundError: No module named 'tqdm'` | `pip install -r requirements.txt` |
| Docker build: unzip not found | `apt-get install -y unzip` before RUN |
| Docker build: pip DNS failure | Use `--network host` flag |
| EUR-IS-1 no GPU supply | Endpoint/pod can't deploy. Try without region restriction |
| RunPod SSH timeout on long ops | Use Web Terminal in console instead |
| Serverless "Job processing failed" | Generic crash — switch to pod for debug visibility |

---

## 10. Credentials Summary

All credentials are stored in `.env` file (not in git):
```
RUNPOD_API_KEY=           (from RunPod Settings → API Keys)
RUNPOD_ENDPOINT_ID=       (from RunPod Serverless → your endpoint)
HuggingFace Token:        (from https://huggingface.co/settings/tokens)
Docker Hub Username:      oscarrzz
Docker Hub Token:         (from https://hub.docker.com/settings/security)
GitHub:                   OscarrzzCode/project-o-v3
RunPod Account:           OscarrzzCode
SSH Key:                  C:\Users\ACSNB-04\.ssh\rp_pulid (ED25519)
```

---

## 11. Next Steps for New Conversation

### Immediate (Pick Up Where We Left Off)
1. Create RunPod pod with `runpod/pytorch:2.4.0`, attach volume `high_salmon_cod`, any GPU, with PUBLIC_KEY=ssh key
2. Open Web Terminal → paste the startup commands from Section 6
3. Confirm `curl -s localhost:8188/queue` returns `{"queue_running": [], "queue_pending": []}`
4. Test basic FLUX txt2img:
   ```
   curl -s localhost:8188/prompt -H "Content-Type: application/json" -d '{"prompt":{"1":{"inputs":{"text":"a cat","clip":["2",0]},"class_type":"CLIPTextEncode"}, ... }}'
   ```
5. Test PuLID workflow with a face image
6. If PuLID works → build `src/pod_manager.py` + `src/comfyui_client.py` → update `main.py` → end-to-end test

### Medium-Term (After PuLID Works)
1. Build `src/pod_manager.py` (pod lifecycle: create, check, stop)
2. Build `src/comfyui_client.py` (ComfyUI API: /prompt, /history, /queue)
3. Update `src/main.py` to use pod manager instead of serverless RunPod API
4. Deploy backend to Render (public URL)
5. Add DWPose workflow (pose modification)
6. Add NSFW LoRA support

### Long-Term
1. Character embedding profiles (Workflow D from spec)
2. Face similarity scoring pipeline
3. Multi-image identity locking
4. SUPIR upscaling

---

## 12. API Reference Summary

### RunPod REST API (Used for Pod Management)
```
Base: https://rest.runpod.io/v1

POST /pods                    → Create pod
GET  /pods                    → List pods
GET  /pods/{id}               → Get pod details
POST /templates               → Create template
PATCH /templates/{id}         → Update template
```

### RunPod GraphQL API (Used for Endpoint Management)
```
Base: https://api.runpod.io/graphql

query { myself { endpoints { id name } } }   → List endpoints
query { myself { pods { id name runtime { uptimeInSeconds } } } }  → List pods
mutation { saveEndpoint(input: {...}) { id name } } → Create endpoint
mutation { deleteEndpoint(id: "...") }               → Delete endpoint
mutation { podStop(input: { podId: "..." }) { id } } → Stop pod
```

### ComfyUI API (Standard)
```
POST /prompt                  → Queue workflow {prompt: workflow_obj}
GET  /history                 → All history
GET  /history/{prompt_id}     → Specific result
GET  /queue                   → Current queue status
GET  /object_info             → Available nodes
POST /upload/image            → Upload image file
```

### Worker Payload Format
```json
{
  "input": {
    "workflow": {
      "node_id": {
        "inputs": {"param": "value"},
        "class_type": "NodeClassName"
      }
    },
    "images": [
      {"name": "input_image.png", "image": "base64_encoded_data"}
    ]
  }
}
```

---

## 13. Phase 2 Progress (2026-06-13)

### Accomplishments

| Item | Detail |
|---|---|
| Docker image built | oscarrzz/project-o:latest � 67GB, FLUX 16-bit baked in |
| Image on Docker Hub | sha256:f2ca675f8c � pushed |
| Pod running | kvqmnc6que4ldb � RTX PRO 6000 Blackwell (97GB VRAM), 188GB RAM |
| ComfyUI running | Port 8188 ?? � verified via curl localhost:8188/queue |
| FLUX tested | ? Basic txt2img works (1 image) |
| PuLID extension loaded | ? 0.5s load time |
| PyTorch for Blackwell | ? 2.12.0+cu130 auto-upgraded |
| Disk cleaned | 75GB freed (caches + Docker prune) |

### Not Yet Tested
- ? PuLID-FLUX workflow (queued but result pending)
- ? Backend pod manager (pod_manager.py, comfyui_client.py)
- ? Benchmark framework

### Pod Access
- Web Terminal: https://www.runpod.io/console/user/pod/kvqmnc6que4ldb
- SSH: 157.157.221.177:15704 (unstable � use Web Terminal instead)
- Cost: ~$0.50/hr (remember to STOP when done)

### Next: Test PuLID ? build backend ? benchmark
