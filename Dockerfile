FROM runpod/worker-comfyui:5.8.5-flux1-dev

RUN pip install --no-cache-dir timm facexlib insightface onnxruntime opencv-python

RUN cd /comfyui/custom_nodes && \
    git clone https://github.com/balazik/ComfyUI-PuLID-Flux.git && \
    cd ComfyUI-PuLID-Flux && \
    pip install -r requirements.txt 2>/dev/null || true

COPY workflows/ /comfyui/user/default/workflows/

ENV COMFY_LOG_LEVEL=INFO
ENV REFRESH_WORKER=true
