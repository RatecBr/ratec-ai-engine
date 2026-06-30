def get_installed_models() -> list:
    """
    Lista todos os modelos instalados no volume local
    """
    return [
        {
            "id": "sdxl_base.safetensors",
            "name": "SDXL Base",
            "version": "1.0",
            "status": "available",
            "capabilities": ["txt2img", "img2img"]
        }
    ]
