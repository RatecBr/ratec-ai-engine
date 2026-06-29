from __future__ import annotations

from pathlib import Path

from runtime.configuration import RuntimeConfig

_VOLUME_DIRS = [
    "models/checkpoints",
    "models/clip",
    "models/clip_vision",
    "models/controlnet",
    "models/ipadapter",
    "models/loras",
    "models/vae",
    "models/upscale_models",
    "models/embeddings",
    "workflows",
    "output",
    "input",
    "temp",
    "logs",
]

_COMFYUI_SYMLINKS: dict[str, str] = {
    "models": "models",
    "output": "output",
    "input": "input",
    "temp": "temp",
}


def prepare_volume(config: RuntimeConfig) -> None:
    """Cria a estrutura de diretórios obrigatória no Network Volume."""
    if not config.volume_available:
        print(f"[ratec-bootstrap] AVISO: volume não encontrado em {config.volume_path}", flush=True)
        return

    for rel_dir in _VOLUME_DIRS:
        (config.volume_path / rel_dir).mkdir(parents=True, exist_ok=True)

    print(f"[ratec-bootstrap] Estrutura de diretórios pronta em {config.volume_path}", flush=True)


def setup_comfyui_symlinks(config: RuntimeConfig) -> None:
    """Configura symlinks do diretório ComfyUI para o Network Volume."""
    if not config.volume_available:
        return
    if not config.comfyui_path.exists():
        print(f"[ratec-bootstrap] AVISO: ComfyUI não encontrado em {config.comfyui_path}", flush=True)
        return

    for link_name, volume_dir in _COMFYUI_SYMLINKS.items():
        target = config.volume_path / volume_dir
        link = config.comfyui_path / link_name
        try:
            link.unlink(missing_ok=True)
            link.symlink_to(target)
        except Exception as exc:
            print(f"[ratec-bootstrap] AVISO: falha ao criar symlink {link} → {target}: {exc}", flush=True)

    print("[ratec-bootstrap] Symlinks configurados", flush=True)


def validate_environment(config: RuntimeConfig) -> list[str]:
    """
    Valida o ambiente de execução.
    Retorna lista de avisos (não bloqueia o início do Runtime).
    """
    warnings: list[str] = []

    if not config.volume_available:
        warnings.append(f"Network Volume não encontrado em {config.volume_path}")

    if not config.comfyui_path.exists():
        warnings.append(f"ComfyUI não encontrado em {config.comfyui_path}")

    if not config.workflows_dir.exists():
        warnings.append(f"Diretório de workflows não encontrado em {config.workflows_dir}")

    return warnings


def run(config: RuntimeConfig) -> None:
    """
    Executa o bootstrap completo do AI Runtime.
    Chamado automaticamente no start.sh antes do handler.
    """
    print("[ratec-bootstrap] Iniciando bootstrap do AI Runtime...", flush=True)
    prepare_volume(config)
    setup_comfyui_symlinks(config)

    warnings = validate_environment(config)
    for w in warnings:
        print(f"[ratec-bootstrap] AVISO: {w}", flush=True)

    print("[ratec-bootstrap] Bootstrap concluído", flush=True)
