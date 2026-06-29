from __future__ import annotations


class ComfyUIError(Exception):
    """Base para todos os erros relacionados ao ComfyUI."""


class ComfyUIConnectionError(ComfyUIError):
    """Instância do ComfyUI inacessível ou retornou status HTTP inesperado."""


class ComfyUIWorkflowNotFoundError(ComfyUIError):
    """Arquivo JSON do workflow não encontrado no diretório workflows/."""


class ComfyUITimeoutError(ComfyUIError):
    """Execução do job excedeu o timeout permitido."""


class ComfyUIExecutionError(ComfyUIError):
    """ComfyUI reportou erro durante a execução do workflow."""
