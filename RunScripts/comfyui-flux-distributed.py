import json
import subprocess
import uuid
from pathlib import Path
from typing import Dict

import modal
vol = modal.Volume.from_name("comfyui-workflows", create_if_missing=True)

comfy = (  # Download image layers to run FLUX_Q8.gguf model
    modal.Image.debian_slim(  #this starts with a basic and supported python version
        python_version="3.10.13"
    )
    .apt_install("git")  # install git
    .apt_install("nano")  # install to have a minimal text editor if we wanted to change something minimal
    .apt_install("python3-opencv")  # install python3-opencv
    .pip_install("comfy-cli")  # install comfy-cli
    .pip_install("opencv-python")  # install comfy-cli
    .pip_install("onnxruntime-gpu") # install onnxruntime-gpu for reactor
    .run_commands(  # use comfy-cli to install the ComfyUI repo and its dependencies
        "comfy --skip-prompt install --nvidia",
    )
    .run_commands( #download lustify
        "comfy --skip-prompt model download --url https://civitai.com/models/573152?modelVersionId=1588039 --relative-path models/checkpoints --set-civitai-api-token b1a6f9774ae40892590536e7618a58ba",
    )
    
    .run_commands( # install node comfyui_segment_anything
        "comfy node install https://github.com/storyicon/comfyui_segment_anything"
    )
    
    .run_commands( #download GroundingDino
        "comfy --skip-prompt model download --url https://huggingface.co/ShilongLiu/GroundingDINO/resolve/main/groundingdino_swinb_cogcoor.pth --relative-path models/grounding-dino",
    )

    .run_commands( #download SAM
        "comfy --skip-prompt model download --url https://huggingface.co/lkeab/hq-sam/resolve/main/sam_hq_vit_h.pth --relative-path models/sams",
    )
    
    .run_commands( # install node ReActor Faceswap
        "comfy node registry-install comfyui-reactor-node"
    )
    
    .run_commands( # install node ComfyUI Browser
        "comfy node install https://github.com/talesofai/comfyui-browser"
    )
    
    .run_commands( # install node rgthree-comfy
        "comfy node install https://github.com/rgthree/rgthree-comfy"
    )
    
    .run_commands( # install node ComfyUI-Impact-Pack
        "comfy node install https://github.com/ltdrdata/ComfyUI-Impact-Pack"
    )

    .run_commands( #download models for SUPIR
        "comfy --skip-prompt model download --url https://huggingface.co/SG161222/RealVisXL_V5.0/resolve/main/RealVisXL_V5.0_fp16.safetensors --relative-path models/checkpoints",
        "comfy --skip-prompt model download --url https://huggingface.co/RunDiffusion/Juggernaut-XL-v9/resolve/main/Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors --relative-path models/checkpoints",
        "comfy --skip-prompt model download --url https://huggingface.co/Kijai/SUPIR_pruned/resolve/main/SUPIR-v0F_fp16.safetensors --relative-path models/checkpoints",
        "comfy --skip-prompt model download --url https://huggingface.co/Phips/4xNomos8kDAT/resolve/main/4xNomos8kDAT.safetensors --relative-path models/upscale_models",
    )

    .run_commands( # install ComfyUI-SUPIR
        "comfy node install https://github.com/kijai/ComfyUI-SUPIR"
    )
    
    .run_commands( # install ComfyUI-KJNodes
        "comfy node install https://github.com/kijai/ComfyUI-KJNodes"
    )
    
    .run_commands( # install ComfyUI-Distributed
        "comfy node install https://github.com/robertvoy/ComfyUI-Distributed"
    )
)

app = modal.App(name="comfyui-distributed", image=comfy)
@app.function(
    max_containers=1,
    min_containers=1,
    scaledown_window=30,
    timeout=3200,
    gpu="T4", # here you can change the gpu, i recommend either a10g or T4
    volumes={"/root/comfy/ComfyUI/user/default": vol}, # Mount the volume to the user data folder
)
@modal.concurrent(max_inputs=10)
@modal.web_server(8000, startup_timeout=60)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000 --enable-cors-header", shell=True)