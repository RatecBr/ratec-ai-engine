def get_runtime_info() -> dict:
    """
    Retorna informacoes detalhadas sobre o Runtime e ComfyUI
    """
    # Em um cenario real, obteria da instancia do Engine.
    return {
        "is_serverless": False,
        "volume_path": "/runpod-volume", # mock
        "python_version": "3.11",
        "comfyui_manager": {
            "status": "ok",
            "latency_ms": 12
        },
        "capabilities": ["txt2img", "img2img", "inpaint"]
    }
