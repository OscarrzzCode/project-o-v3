FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

RUN apt-get update && apt-get install -y unzip git wget && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI

WORKDIR /opt/ComfyUI
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir timm facexlib insightface onnxruntime onnxruntime-gpu opencv-python einops huggingface_hub

COPY startup.sh /opt/startup.sh
RUN chmod +x /opt/startup.sh

WORKDIR /workspace
CMD ["/opt/startup.sh"]
