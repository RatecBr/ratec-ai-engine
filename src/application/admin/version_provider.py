import os
import json
import platform
from datetime import datetime
from typing import Dict, Any

class VersionProvider:
    """
    Provedor centralizado de informações de versão da plataforma.
    Lê os metadados injetados pelo pipeline CI/CD (build_info.json)
    e acrescenta informações de runtime.
    """
    
    _instance = None
    
    def __init__(self):
        self._build_info = self._load_build_info()
    
    @classmethod
    def get_instance(cls) -> "VersionProvider":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_build_info(self) -> Dict[str, Any]:
        """Tenta carregar o arquivo build_info.json injetado pelo CI/CD."""
        build_info = {
            "engine_version": "2.0.0",
            "git_commit": "unknown",
            "git_short_commit": "unknown",
            "git_branch": "unknown",
            "docker_image": "unknown",
            "docker_tag": "unknown",
            "docker_digest": "unknown",
            "build_date": "unknown",
            "github_run_id": "unknown",
            "github_run_number": "unknown",
            "github_repository": "unknown"
        }
        
        # O arquivo pode estar no diretório atual (Serverless) ou raiz do container
        paths = ["build_info.json", "/handler/build_info.json", "/app/build_info.json"]
        
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        build_info.update(data)
                        break
                except Exception:
                    pass
                    
        return build_info

    def get_version_info(self, boot_time: datetime = None, comfyui_version: str = "unknown", gpu_model: str = "unknown") -> Dict[str, Any]:
        """
        Retorna as informações completas de versão combinando metadados de build e ambiente.
        """
        info = dict(self._build_info)
        info["python_version"] = platform.python_version()
        info["worker_started_at"] = boot_time.isoformat() if boot_time else "unknown"
        info["comfyui_version"] = comfyui_version
        info["gpu_model"] = gpu_model
        return info
        
    @property
    def build_info(self) -> Dict[str, Any]:
        return self._build_info

version_provider = VersionProvider.get_instance()
