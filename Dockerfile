FROM runpod/worker-comfyui:5.8.5-flux1-dev

RUN pip install --no-cache-dir timm facexlib insightface onnxruntime opencv-python einops

WORKDIR /comfyui/custom_nodes
ADD https://github.com/balazik/ComfyUI-PuLID-Flux/archive/refs/heads/master.zip /tmp/pulid-flux.zip
RUN unzip -q /tmp/pulid-flux.zip && mv ComfyUI-PuLID-Flux-master ComfyUI-PuLID-Flux && rm /tmp/pulid-flux.zip && pip install --no-cache-dir -r ComfyUI-PuLID-Flux/requirements.txt

ADD https://github.com/cubiq/ComfyUI_IPAdapter_plus/archive/refs/heads/main.zip /tmp/ipadapter.zip
RUN unzip -q /tmp/ipadapter.zip && mv ComfyUI_IPAdapter_plus-main ComfyUI_IPAdapter_plus && rm /tmp/ipadapter.zip

COPY workflows/ /comfyui/user/default/workflows/

ENV COMFY_LOG_LEVEL=INFO
ENV REFRESH_WORKER=false
