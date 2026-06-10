FROM runpod/worker-comfyui:5.8.5-flux1-dev

RUN pip install --no-cache-dir \
    timm \
    facexlib \
    insightface \
    onnxruntime \
    opencv-python \
    einops

RUN cd /comfyui/custom_nodes \
    && git clone https://github.com/balazik/ComfyUI-PuLID-Flux.git

COPY workflows/ /comfyui/user/default/workflows/

ENV COMFY_LOG_LEVEL=INFO
ENV REFRESH_WORKER=false
