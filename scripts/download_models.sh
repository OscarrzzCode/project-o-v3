#!/bin/bash
# Run this on a temp RunPod GPU pod in EU-RO-1 with the Network Volume attached
# The volume "rude_brown_hamster" should be mounted (typically at /workspace)
# If mounted elsewhere, change the VOLUME variable below

set -e

VOLUME="${1:-/workspace}"
MODELS="$VOLUME/models"

echo "=== Project O v3 - Model Download ==="
echo "Network Volume: $VOLUME"
echo ""

mkdir -p "$MODELS/diffusion_models"
mkdir -p "$MODELS/clip"
mkdir -p "$MODELS/vae"
mkdir -p "$MODELS/pulid"
mkdir -p "$MODELS/controlnet"
mkdir -p "$MODELS/insightface/models"
mkdir -p "$MODELS/loras"

echo "[1/7] FLUX.1 Dev FP8 (~6GB)..."
wget -nc -P "$MODELS/diffusion_models" \
  https://huggingface.co/XLabs-AI/flux-dev-fp8/resolve/main/flux-dev-fp8.safetensors

echo "[2/7] T5 XXL FP8 Text Encoder (~5GB)..."
wget -nc -P "$MODELS/clip" \
  https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors

echo "[3/7] CLIP-L (~250MB)..."
wget -nc -P "$MODELS/clip" \
  https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors

echo "[4/7] FLUX VAE (~320MB)..."
wget -nc -P "$MODELS/vae" \
  https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors

echo "[5/7] PuLID-FLUX v0.9.1 (~1.2GB)..."
wget -nc -P "$MODELS/pulid" \
  https://huggingface.co/guozinan/PuLID/resolve/main/pulid_flux_v0.9.1.safetensors

echo "[6/7] InsightFace models (~500MB)..."

wget -nc -P "$MODELS/insightface/models" \
  https://huggingface.co/MonsterMMORPG/tools/resolve/main/antelopev2.zip

echo "[7/7] Unzipping InsightFace..."
mkdir -p "$MODELS/insightface/models/antelopev2"
unzip -o "$MODELS/insightface/models/antelopev2.zip" -d "$MODELS/insightface/models/antelopev2/" 2>&1 || echo "  (unzip may have failed, check manually)"
rm -f "$MODELS/insightface/models/antelopev2.zip"

echo ""
echo "=== All models downloaded ==="
echo "Volume contents:"
find "$MODELS" -type f -name "*.safetensors" -o -name "*.onnx" -o -name "*.pth" | sort
echo ""
echo "Disk usage:"
du -sh "$MODELS"/*
echo ""
echo "Ready. You can now stop this pod."
