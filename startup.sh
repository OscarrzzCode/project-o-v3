#!/bin/bash
set -e
echo "=== Project O Worker ==="

# Ensure directory structure
mkdir -p /opt/ComfyUI/models/unet /opt/ComfyUI/models/clip /opt/ComfyUI/models/vae /opt/ComfyUI/models/pulid /opt/ComfyUI/models/insightface/models/antelopev2
mkdir -p /opt/ComfyUI/custom_nodes

# Link models from volume
echo "Linking models..."
for dir in unet clip vae pulid; do
    if [ -d "/workspace/models/$dir" ]; then
        ln -sf /workspace/models/$dir/* /opt/ComfyUI/models/$dir/ 2>/dev/null || true
    fi
done

# Link custom nodes from volume  
if [ -d "/workspace/custom_nodes" ]; then
    ln -sf /workspace/custom_nodes/* /opt/ComfyUI/custom_nodes/ 2>/dev/null || true
fi

# Link workflows
if [ -d "/workspace/workflows" ]; then
    cp -r /workspace/workflows/* /opt/ComfyUI/user/default/workflows/ 2>/dev/null || true
fi

# Download VAE if missing (from volume path)
if [ ! -f "/workspace/models/vae/ae.safetensors" ] || [ $(stat -c%s "/workspace/models/vae/ae.safetensors" 2>/dev/null || echo 0) -lt 1000000 ]; then
    echo "Downloading VAE..."
    python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download('black-forest-labs/FLUX.1-dev', 'ae.safetensors', local_dir='/workspace/models/vae')
print('VAE downloaded')
" 2>/dev/null && ln -sf /workspace/models/vae/ae.safetensors /opt/ComfyUI/models/vae/ae.safetensors || echo "VAE download failed - retry later"
fi

# Install custom nodes from volume if not present
if [ ! -d "/opt/ComfyUI/custom_nodes/ComfyUI-PuLID-Flux" ]; then
    echo "Cloning PuLID-FLux..."
    git clone https://github.com/balazik/ComfyUI-PuLID-Flux.git /workspace/custom_nodes/ComfyUI-PuLID-Flux 2>/dev/null || true
    ln -sf /workspace/custom_nodes/ComfyUI-PuLID-Flux /opt/ComfyUI/custom_nodes/ComfyUI-PuLID-Flux 2>/dev/null || true
    cd /opt/ComfyUI/custom_nodes/ComfyUI-PuLID-Flux && pip install -r requirements.txt -q 2>/dev/null || true
fi

echo "Starting ComfyUI on port 8188..."
cd /opt/ComfyUI
python main.py --listen 0.0.0.0 --port 8188
