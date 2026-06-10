FROM runpod/worker-comfyui:5.8.5-base

RUN comfy-node-install \
    ComfyUI-KJNodes \
    ComfyUI_essentials \
    comfyui_controlnet_aux \
    comfyui-pulid-flux \
    comfyui-reactor-node \
    was-node-suite-comfyui

COPY workflows/ /comfyui/user/default/workflows/

ENV COMFY_LOG_LEVEL=INFO
ENV REFRESH_WORKER=true
