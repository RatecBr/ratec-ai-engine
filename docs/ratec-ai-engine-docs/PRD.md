# RATEC AI ENGINE — PRD

## Visão

Plataforma centralizada de IA da RATEC. Todos os produtos (GOODLOOK, Audiover, Internice, Animapages, Karaokêro, Tradulino) consomem esta API — nunca integrando diretamente com modelos ou infraestrutura de IA.

## Objetivos

- **API única** para todos os produtos RATEC
- **Clean Architecture** — isolamento entre domínio e infraestrutura
- **Workflow Engine** — orquestração de processos de negócio
- **Execution Manager** — roteamento entre backends de compute
- **Capability Routing** — apps solicitam capabilities, o Engine decide o workflow
- **Model Catalog** — catálogo oficial de modelos com manifests
- **AI Lab** — laboratório de pesquisa, benchmark e validação
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

## Estado atual (Epic 3 concluído)

### Epic 1 — Fundação (Sprints 1–5)
- Clean Architecture operacional
- ComfyUI Provider + Backend integrado ao ExecutionManager
- AI Runtime standalone (`runtime/`) com executor genérico
- `Dockerfile.runtime` + CI/CD + IaC via `scripts/start.sh`

### Epic 2 — Biblioteca de Workflows
- Capability routing: `background-remove`, `image-upscale`, `haircut`, `beard`, `makeup`, `virtual-try-on`, `face-segmentation`
- Workflows ativos: `image/identity`, `image/background-remove`, `image/image-upscale`
- AI Playground v1: interface de testes local

### Epic 3 — AI Lab ✅ (atual)
- `runtime/lab/` — histórico de execuções (SQLite), benchmark, avaliações manuais, cache experimental
- `runtime/models/catalog/` — 6 manifests: BRIA RMBG, RealESRGAN, FLUX, ControlNet, IPAdapter, Whisper
- AI Playground v2 — 5 abas: Execute, History, Compare, Benchmark, Catalog
- Arquitetura congelada — nenhuma alteração estrutural sem ADR aprovada

## Capabilities

| Capability | Workflow | Status | VRAM | Modelo |
|-----------|---------|--------|------|--------|
| `image-identity` | `image/identity` | ✅ Ativo | 0 | nenhum |
| `background-remove` | `image/background-remove` | 🔧 Aguarda modelo | 8GB | BRIA RMBG-1.4 |
| `image-upscale` | `image/image-upscale` | 🔧 Aguarda modelo | 4GB | RealESRGAN x4plus |
| `face-segmentation` | `image/face-segmentation` | 🔜 Planejado | 8GB | — |
| `haircut` | `image/haircut` | 🔜 Planejado | 24GB | FLUX + IPAdapter |
| `beard` | `image/beard` | 🔜 Planejado | 24GB | FLUX + IPAdapter |
| `makeup` | `image/makeup` | 🔜 Planejado | 24GB | FLUX + IPAdapter |
| `virtual-try-on` | `image/virtual-try-on` | 🔜 Planejado | 24GB | FLUX + IPAdapter |

## Fluxo obrigatório de nova capability

```
Workflow → AI Playground → Benchmark → Aprovação → API → Aplicativo
```

Nenhuma capability chega ao aplicativo sem ser validada e benchmarkada no AI Lab.

## Princípios técnicos permanentes

- Workflows **nunca** referenciam modelos ou backends diretamente
- Apps **nunca** conhecem modelos, providers, workflows ou implementação interna
- Modelos **nunca** ficam na imagem Docker — sempre via Network Volume
- IaC: todo setup declarado em código (`start.sh`, `bootstrap.py`)
- Hardware é responsabilidade da infraestrutura, não do código
- Arquitetura congelada desde o Epic 3 — evolução apenas de capabilities
