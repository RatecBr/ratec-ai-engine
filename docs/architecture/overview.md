# Arquitetura — RATEC AI ENGINE

## Visão geral

O RATEC AI ENGINE é a plataforma centralizada de IA da RATEC. Todos os produtos
(GOODLOOK, Audiover, Internice, Animapages, Karaokêro, Tradulino) consomem apenas
esta API, nunca integrando diretamente com modelos ou infraestrutura de IA.

## Dois modos de operação

### Modo API (desenvolvimento / futuro)

Servidor FastAPI rodando com a Clean Architecture completa.

```
Cliente (GOODLOOK, Audiover, …)
        │
        │  POST /v1/jobs  { workflow_id, input }
        ▼
  ┌─────────────┐
  │   FastAPI   │  Camada de apresentação
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────┐
  │    SubmitJobUseCase  │  Application layer
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │   WorkflowRegistry  │  Resolve workflow por ID
  └──────────┬──────────┘
             │  workflow encontrado
             ▼
  ┌─────────────────────┐
  │   WorkflowEngine    │  Itera steps do workflow
  └──────────┬──────────┘
             │  para cada WorkflowStep → pipeline_id
             ▼
  ┌─────────────────────┐
  │   PipelineRegistry  │  Resolve pipeline por ID
  └──────────┬──────────┘
             │  pipeline encontrado
             ▼
  ┌─────────────────────┐
  │   PipelineEngine    │  Itera steps do pipeline
  └──────────┬──────────┘
             │  para cada PipelineStep → capability + action + model_id
             ▼
  ┌──────────────────────┐
  │   ExecutionManager   │  Roteia pela execution_strategy
  └──────────┬───────────┘
             │
     ┌───────┴────────┐
     ▼                ▼
ComfyUIBackend   RunPodBackend   (futuro: Modal, Replicate, AWS…)
     │                │
     └───────┬────────┘
             │  ExecutionResult
             ▼
       Job.mark_completed()
```

### Modo Runtime (produção RunPod)

Handler serverless minimalista. Toda lógica em `runtime/`.

```
RunPod Job  { action, input }
        │
        ▼
  ┌─────────────┐
  │  handler.py │  thin entry point (10 linhas)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   Runtime   │  facade: initialize() + handle()
  └──────┬──────┘
         │
    ┌────┴─────────────────────────┐
    │  action routing              │
    │  ─────────────────────────   │
    │  echo        → _echo()       │
    │  health      → _health()     │
    │  image-echo  → _image_echo() │
    │  image/*     → _image_*()    │
    └────┬─────────────────────────┘
         │
         ▼
  ┌──────────────────┐
  │  ComfyUIExecutor │  submit + poll + parse_images
  └──────┬───────────┘
         │  POST /prompt  |  GET /history/{id}
         ▼
  ┌──────────────────┐
  │  ComfyUI local   │  http://127.0.0.1:8188
  └──────────────────┘
         │
         ▼
  Observability block em toda resposta:
  execution_time_ms, gpu_model, vram_total/used/free_mb
```

## Estrutura de diretórios

```
ratec-ai-engine/
├── handler.py                    # entry point RunPod (thin)
├── runtime/                      # módulo standalone para RunPod
│   ├── __init__.py               # Runtime facade + _CAPABILITY_ROUTES
│   ├── configuration.py          # RuntimeConfig (env vars)
│   ├── observability.py          # GPUMetrics, ExecutionMetrics
│   ├── health.py                 # full_health()
│   ├── executor.py               # ComfyUIExecutor (submit/poll/parse)
│   ├── server.py                 # ComfyUIServer (start/wait/stop)
│   ├── workflow.py               # WorkflowManager (load/list/overrides)
│   ├── upload.py                 # upload base64 → ComfyUI
│   ├── download.py               # download ComfyUI → base64
│   ├── bootstrap.py              # IaC: volume dirs + symlinks
│   ├── manifest.yaml             # estado estático do runtime
│   ├── lab/                      # AI Lab (camada observacional — não altera produção)
│   │   ├── __init__.py           # Lab facade: record(), cache_get/set()
│   │   ├── database.py           # SQLite: executions + cache_entries
│   │   └── cache.py              # compute_key() SHA-256
│   └── models/
│       └── catalog/              # manifests YAML dos modelos
│           ├── bria-rmbg/        # BRIA RMBG-1.4 (background-remove)
│           ├── realesrgan/       # RealESRGAN x4plus (image-upscale)
│           ├── flux/             # FLUX.1-dev (haircut, beard, makeup)
│           ├── controlnet/       # ControlNet FLUX (planejado)
│           ├── ipadapter/        # IPAdapter FLUX (planejado)
│           └── whisper/          # Whisper Large v3 (áudio, planejado)
├── workflows/                    # biblioteca de capabilities por categoria
│   ├── image/
│   │   ├── identity/             ✅ ativo
│   │   ├── background-remove/    ✅ ativo (aguarda modelo no volume)
│   │   ├── image-upscale/        ✅ ativo (aguarda modelo no volume)
│   │   ├── face-segmentation/    🔜 planejado
│   │   ├── haircut/              🔜 planejado
│   │   ├── beard/                🔜 planejado
│   │   ├── makeup/               🔜 planejado
│   │   └── virtual-try-on/       🔜 planejado
│   ├── audio/
│   ├── video/
│   ├── vision/
│   └── multimodal/
├── playground/                   # AI Lab Playground (ferramenta de desenvolvimento)
│   ├── server.py                 # FastAPI: 5 abas — Execute/History/Compare/Benchmark/Catalog
│   ├── catalog.py                # leitor YAML do catálogo de modelos
│   ├── requirements.txt          # fastapi, uvicorn, pyyaml, aiofiles
│   └── README.md
├── src/                          # Clean Architecture (modo API)
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   │   ├── providers/
│   │   │   └── comfyui/          # Provider ComfyUI (8 arquivos)
│   │   ├── execution/
│   │   │   ├── comfyui_backend.py
│   │   │   └── execution_manager.py
│   │   └── validators/
│   │       └── workflow_validator.py
│   └── config/
│       └── dependencies.py
├── scripts/
│   └── start.sh                  # boot IaC do container
├── Dockerfile.runtime            # imagem de produção
└── .github/workflows/
    └── build-runtime.yml         # CI/CD
```

## Camadas (modo API)

| Camada | Responsabilidade | Conhece |
|--------|-----------------|---------|
| **Workflow** | Processo de negócio | Pipeline IDs |
| **Pipeline** | Orquestração técnica | Capabilities, Model IDs |
| **PipelineEngine** | Execução de steps | ExecutionManager (abstrato) |
| **ExecutionManager** | Roteamento de compute | ExecutionBackends |
| **ExecutionBackend** | Infraestrutura concreta | ComfyUI API, RunPod API, etc. |
| **ModelRegistry** | Catálogo de modelos | AIModel metadata |
| **CapabilityRegistry** | Mapeamento capability → modelos | ModelRegistry |

## Princípios arquiteturais

- **Inversão de dependência**: camadas superiores dependem de interfaces, nunca de implementações
- **Substituibilidade de provider**: trocar ComfyUI por outro motor = novo `ExecutionBackend`
- **Substituibilidade de modelo**: trocar modelos = atualizar Network Volume (sem rebuild de imagem)
- **Desacoplamento de workflows**: workflows nunca conhecem modelos ou backends
- **IaC**: todo setup do ambiente é código, nunca configuração manual
- **Hardware-agnostic**: código nunca verifica qual GPU está rodando; política é da infraestrutura
- **Extensibilidade**: novos produtos da RATEC consomem a mesma API sem modificações no motor
- **Arquitetura congelada** (desde Epic 3): nenhuma mudança estrutural sem ADR aprovada
- **Lab não-invasivo**: `runtime/lab/` é observacional — não altera nenhum comportamento de produção
- **Capability-first**: apps solicitam capabilities, nunca workflows, modelos ou providers
