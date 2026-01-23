import json
import subprocess
import uuid
from pathlib import Path
from typing import Dict

import modal
vol = modal.Volume.from_name("comfyui-workflows", create_if_missing=True)

flux = (  # Download image layers to run FLUX_Q8.gguf model
    modal.Image.debian_slim(  #this starts with a basic and supported python version
        python_version="3.10.13"
    )
    .apt_install("git")  # install git
    .apt_install("nano")  # install to have a minimal text editor if we wanted to change something minimal
    .pip_install("comfy-cli")  # install comfy-cli
    .pip_install("onnxruntime-gpu") # install onnxruntime-gpu for reactor
    .run_commands(  # use comfy-cli to install the ComfyUI repo and its dependencies
        "comfy --skip-prompt install --nvidia",
    )
    .run_commands(# download the GGUF Q8 model
    "comfy --skip-prompt model download --url https://huggingface.co/city96/FLUX.1-dev-gguf/resolve/main/flux1-dev-Q8_0.gguf  --relative-path models/unet",
    )
    .run_commands( # gguf node required for q8 model
        "comfy node install https://github.com/city96/ComfyUI-GGUF"
    )
    .run_commands(  # download the vae model required to use with the gguf model
        "comfy --skip-prompt model download --url https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors --relative-path models/vae"
    )
    .run_commands(  # download the cliper model required to use with GGUF model
        "comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors --relative-path models/clip",
        "comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors --relative-path models/clip",
    )
    
    #.run_commands(  # download the lora anime -- optional you can disbale
    #    "comfy --skip-prompt model download --url https://civitai.com/models/640247/mjanimefluxlora?modelVersionId=716064 --relative-path models/loras --set-civitai-api-token [USE YOUR CIVITAI TOKEN]"
    #)

    # put down here additional layers to your likings below
    .run_commands( # XLabs ControlNet node 
        "comfy node install https://github.com/XLabs-AI/x-flux-comfyui"
    )
    .run_commands( #download controlnet v3 xlabs ai
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-controlnet-depth-v3/resolve/main/flux-depth-controlnet-v3.safetensors --relative-path models/xlabs/controlnets",
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-controlnet-canny-v3/resolve/main/flux-canny-controlnet-v3.safetensors --relative-path models/xlabs/controlnets",
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-controlnet-hed-v3/resolve/main/flux-hed-controlnet-v3.safetensors --relative-path models/xlabs/controlnets",
    )
    .run_commands( #install control net requried for above xlabs
        "comfy node install https://github.com/Fannovel16/comfyui_controlnet_aux"
    )
    .run_commands( #xlab loras --optional
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/art_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/anime_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/disney_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/mjv6_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/realism_lora_comfy_converted.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/scenery_lora_comfy_converted.safetensors --relative-path models/loras"
    )
    .run_commands( #someloras optional
        "comfy --skip-prompt model download --url https://huggingface.co/alvdansen/frosting_lane_flux/resolve/main/flux_dev_frostinglane_araminta_k.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --url https://huggingface.co/multimodalart/flux-tarot-v1/resolve/main/flux_tarot_v1_lora.safetensors --relative-path models/loras",
    )
    .run_commands( #CR APPLY lora stack -- useful node -- optional
        "comfy node install https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes"
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
)

app = modal.App(name="flux-comfyui", image=flux)
@app.function(
    max_containers=1,
    scaledown_window=30,
    timeout=3200,
    gpu="T4", # here you can change the gpu, i recommend either a10g or T4
    volumes={"/root/comfy/ComfyUI/user/default": vol}, # Mount the volume to the user data folder
)
@modal.concurrent(max_inputs=10)
@modal.web_server(8000, startup_timeout=60)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)
