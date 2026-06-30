def get_registered_workflows() -> list:
    """
    Lista todos os workflows com esquemas e metadados admin
    """
    return [
        {
            "id": "wf_txt2img_01",
            "name": "Text to Image (Standard)",
            "version": "1.0",
            "description": "Fluxo padrão de geração de imagem a partir de texto",
            "estimated_time_seconds": 15,
            "input_schema": {"prompt": "string", "negative_prompt": "string"},
            "output_schema": {"image": "base64"}
        }
    ]
