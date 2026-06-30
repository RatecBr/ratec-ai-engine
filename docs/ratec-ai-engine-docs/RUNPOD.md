# RunPod — Configuração e Infraestrutura

## Endpoint

| Campo | Valor |
|-------|-------|
| Endpoint ID | `rov7kf93n8xr1n` |
| Min Workers | 0 |
| Max Workers | 3 |
| Idle Timeout | 5s |
| GPU | NVIDIA RTX A5000 24GB (`AMPERE_48`) |
| Scaler | QUEUE_DELAY |

A restrição a `AMPERE_48` garante que todos os jobs rodem com mínimo de 24GB VRAM, requisito dos workflows de imagem.

## Template

| Campo | Valor |
|-------|-------|
| Template ID | `qkfrs0cjbv` |
| Imagem | `ghcr.io/ratecbr/ratec-ai-engine:runtime` |
| Registry Auth | `ghcr-ratecbr` |
| Container Disk | 20GB |

## Registry Auth (GHCR)

O RunPod puxa imagens do GitHub Container Registry (GHCR) usando um PAT do GitHub.

| Campo | Valor |
|-------|-------|
| Auth ID | `cmqzq6psv008cjt2zbo02s6cw` |
| Nome | `ghcr-ratecbr` |
| Registry | `ghcr.io` |
| Usuário | `RatecBr` |

Para renovar o token: gere um novo PAT no GitHub com escopo `read:packages` e execute:

```graphql
mutation {
  saveRegistryAuth(input: {
    id: "cmqzq6psv008cjt2zbo02s6cw"
    name: "ghcr-ratecbr"
    username: "RatecBr"
    password: "ghp_SEU_TOKEN_AQUI"
  }) {
    id
  }
}
```

## Network Volume

Todos os modelos e outputs são armazenados no Network Volume, **nunca na imagem Docker**.

| Item | Path no Volume | Symlink no Container |
|------|---------------|---------------------|
| Checkpoints | `/runpod-volume/models/checkpoints` | `/comfyui/models/checkpoints` |
| LoRAs | `/runpod-volume/models/loras` | `/comfyui/models/loras` |
| VAE | `/runpod-volume/models/vae` | `/comfyui/models/vae` |
| ControlNet | `/runpod-volume/models/controlnet` | `/comfyui/models/controlnet` |
| Output | `/runpod-volume/output` | `/comfyui/output` |
| Input | `/runpod-volume/input` | `/comfyui/input` |

Os symlinks são criados automaticamente pelo `scripts/start.sh` no boot de cada container.

## Boot sequence

1. `start.sh` executa como `CMD`
2. Cria diretórios do volume (`mkdir -p`)
3. Cria symlinks ComfyUI → volume
4. Inicia ComfyUI: `python3 main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch`
5. Aguarda ComfyUI estar pronto: poll `GET /system_stats` a cada 2s (timeout configurável)
6. Define `COMFYUI_URL=http://127.0.0.1:8188`
7. Executa `python3 -u /handler/handler.py`

## Imagem Docker

A imagem `Dockerfile.comfyui` contém:
- Base: `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
- ComfyUI (git clone --depth=1)
- ComfyUI-Manager
- Handler RATEC (`runtime/`, `scripts/`, `workflows/`, `handler.py`)

**Modelos não estão na imagem.** São carregados via Network Volume em runtime.

## CI/CD

Arquivo: `.github/workflows/build-runtime.yml`

Dispara em push para `develop` ou `main` nos caminhos:
- `Dockerfile.runtime`
- `scripts/start.sh`
- `handler.py`
- `requirements-handler.txt`
- `runtime/**`
- `workflows/**`

Tags geradas: `runtime`, `runtime-<sha>`

## Variáveis de ambiente do container

| Variável | Default | Descrição |
|----------|---------|-----------|
| `COMFYUI_URL` | `http://127.0.0.1:8188` | URL do ComfyUI local |
| `COMFYUI_PORT` | `8188` | Porta do ComfyUI |
| `RUNPOD_VOLUME_PATH` | `/runpod-volume` | Mount point do Network Volume |
| `COMFYUI_PATH` | `/comfyui` | Diretório de instalação do ComfyUI |
| `JOB_TIMEOUT` | `300` | Timeout de jobs em segundos |
| `WORKFLOWS_DIR` | `workflows` | Diretório de workflows (relativo ao handler) |
| `COMFYUI_STARTUP_TIMEOUT` | `120` | Timeout de startup do ComfyUI em segundos |
