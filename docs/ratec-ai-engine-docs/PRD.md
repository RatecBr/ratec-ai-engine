# RATEC AI ENGINE — PRD

## Visão

Plataforma centralizada de IA da RATEC. Todos os produtos (GOODLOOK, Audiover, Internice, Animapages, Karaokêro, Tradulino) consomem esta API — nunca integrando diretamente com modelos ou infraestrutura de IA.

## Objetivos

- **API única** para todos os produtos RATEC
- **Clean Architecture** — isolamento entre domínio e infraestrutura
- **Workflow Engine** — orquestração de processos de negócio
- **Pipeline Engine** — orquestração técnica de capabilities
- **Execution Manager** — roteamento entre backends de compute (RunPod, Modal, etc.)
- **Provider Registry** — catálogo de providers de IA
- **Model Registry** — catálogo de modelos
- **Capability Registry** — mapeamento capability → modelo
- **RunPod Serverless** — compute GPU pay-per-use com scale-to-zero

## Consumidores

| Produto | Domínio | Status |
|---------|---------|--------|
| GOODLOOK | Moda / Visual | Prioritário |
| Audiover | Áudio | Backlog |
| Internice | Comunicação | Backlog |
| Animapages | Animação / Vídeo | Backlog |
| Karaokêro | Áudio / Karaokê | Backlog |
| Tradulino | Tradução | Backlog |

## Estado atual (Sprint 5 concluída)

### Fundação (Sprint 1)
- Arquitetura Clean Architecture operacional
- API Contract v1.0.0 publicado
- RunPod Serverless configurado com GHCR

### Infraestrutura GPU (Sprint 2)
- Endpoint restrito a NVIDIA RTX A5000 (24GB VRAM)
- GPU observability em todas as respostas

### Provider ComfyUI (Sprint 3)
- `src/infrastructure/providers/comfyui/` — 8 arquivos
- Capabilities: image-generation, inpainting, image-to-image, upscaling
- `ComfyUIBackend` integrado ao `ExecutionManager`

### AI Runtime on RunPod (Sprint 4)
- Workflow `image/identity` funcional
- Network Volume com symlinks para modelos
- Boot sequence via `scripts/start.sh`

### Runtime Consolidation (Sprint 5)
- Módulo `runtime/` standalone + `handler.py` thin entry point
- `Dockerfile.runtime` + `build-runtime.yml` CI/CD
- `WorkflowValidator` com checks de VRAM e provider
- Estrutura de workflows por categoria

## Roadmap

### Sprint 6 — Primeiro Workflow Real
- Workflow de produção para GOODLOOK
- Modelos carregados via Network Volume

### Sprint 7 — Integração com Produto
- Autenticação de produto consumidor
- Monitoramento de jobs em produção

### Backlog
- Workflows de áudio, vídeo, tradução
- Dashboard de observability
- Rate limiting por produto

## Princípios técnicos

- Workflows **nunca** referenciam modelos ou backends diretamente
- Providers são intercambiáveis — trocar ComfyUI = novo backend + provider
- Modelos **nunca** ficam na imagem Docker — sempre via Network Volume
- IaC: todo setup do ambiente é declarado em código (`start.sh`, `bootstrap.py`)
- Hardware é responsabilidade da infraestrutura, não do código
