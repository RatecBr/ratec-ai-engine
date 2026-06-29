# CHANGELOG

## v1.0.0 — Epic 2: Biblioteca de Workflows de IA
- Mudança estratégica: plataforma oficial de IA de todos os produtos RATEC (não apenas GOODLOOK)
- Decisão arquitetural: **HairFastGAN não utilizado** — replaced por FLUX + IPAdapter + segmentação
- Executor genérico ComfyUI no Runtime: qualquer workflow com `comfyui.json` executa sem código adicional
- Capability routing: `background-remove` → `image/background-remove`, `haircut` → `image/haircut`, etc.
- `runtime/__init__.py` v2.0.0: `_CAPABILITY_ROUTES` + `_dispatch()` + `_execute_comfyui()` genérico
- Workflow `image/background-remove` implementado (BRIA RMBG-1.4)
- Workflow `image/image-upscale` implementado (RealESRGAN 4x)
- Manifests criados para: `face-segmentation`, `haircut`, `beard`, `makeup`, `virtual-try-on`
- `playground/` — AI Playground (FastAPI + HTML) para testar workflows sem aplicativo
- `runtime/manifest.yaml` atualizado: lista todas as capabilities com status
- `workflows/README.md` atualizado: tabela de capabilities, componentes reutilizáveis, convenções

## v0.5.0 — Sprint 5: Runtime Consolidation + IaC
- Criado módulo `runtime/` como pacote Python standalone (sem dependências de `src/`)
- `handler.py` reduzido a 10 linhas — thin entry point delegando para `Runtime`
- `runtime/bootstrap.py` — IaC completo: cria dirs do volume, symlinks ComfyUI, valida environment
- `runtime/configuration.py` — `RuntimeConfig` com todas as configs via env vars; `from_env()`
- `runtime/observability.py` — `GPUMetrics` e `ExecutionMetrics`; GPU coletada uma vez no boot via `nvidia-smi`
- `runtime/health.py` — checks de ComfyUI, GPU, ComfyUI-Manager, storage; `full_health()`
- `runtime/executor.py` — `ComfyUIExecutor`: submit + poll + parse_images
- `runtime/workflow.py` — `WorkflowManager`: load_comfyui, list_available, apply_node_overrides
- `runtime/server.py` — `ComfyUIServer`: start/wait_ready/stop via subprocess
- `runtime/upload.py` / `runtime/download.py` — base64 I/O de imagens
- `Dockerfile.runtime` — substitui `Dockerfile.comfyui`; copia `runtime/` e `workflows/` para `/handler/`
- `.github/workflows/build-runtime.yml` — substitui `build-comfyui.yml`; tags: `runtime`, `runtime-<sha>`
- `WorkflowValidator` expandido: `validate_runtime_compatibility()` com check de provider e VRAM
- Diretórios `workflows/audio/`, `workflows/video/`, `workflows/vision/`, `workflows/multimodal/` criados
- `runtime/manifest.yaml` — declaração estática do estado do runtime (providers, GPU, consumers)

## v0.4.0 — Sprint 4: AI Runtime on RunPod
- Workflow `image/identity` implementado (LoadImage → SaveImage no ComfyUI)
- `workflows/image/identity/comfyui.json` + `manifest.yaml` criados
- Handler com observability block em todas as respostas: `execution_time_ms`, `gpu_model`, `vram_*`
- Handlers inline para `echo`, `health`, `image-echo`, `image/identity`
- `scripts/start.sh` — orquestra boot: symlinks, start ComfyUI, poll `/system_stats`, exec handler
- Network Volume mapeado via symlinks: `models/`, `output/`, `input/`, `temp/` → `/runpod-volume/`

## v0.3.0 — Sprint 3: ComfyUI Provider
- `src/infrastructure/providers/comfyui/` — provider desacoplado com 8 arquivos
- `ComfyUIClient` — HTTP client com UUID por sessão; métodos: submit_prompt, get_history, get_queue, upload_image, health_check
- `ComfyUIProvider(BaseProvider)` — capabilities: image-generation, inpainting, image-to-image, upscaling
- `ComfyUIJobExecutor` — `node_overrides` para parametrização de workflows
- `ComfyUIResultParser` — extração de imagens da resposta do ComfyUI
- `ComfyUIBackend(BaseExecutionBackend)` — backend_id = "comfyui"; suporta estratégias "auto" e "comfyui"
- `ExecutionManager._PRIORITY_ORDER` atualizado: ("runpod", "comfyui", "modal", "replicate", "aws", "azure", "kubernetes")
- Exceptions tipadas: `ComfyUIError`, `ComfyUIConnectionError`, `ComfyUIWorkflowNotFoundError`, `ComfyUITimeoutError`, `ComfyUIExecutionError`
- `src/config/dependencies.py` — registra ComfyUI backend, provider, pipeline e capability

## v0.2.0 — Sprint 2: GPU Policy + Observability
- RunPod endpoint restrito a `AMPERE_48` (NVIDIA RTX A5000 24GB) via GraphQL mutation
- GPU observability coletada no boot via `nvidia-smi`; incluída em todas as respostas
- Código mantido GPU-agnostic — política de hardware é responsabilidade da infraestrutura
- `WorkflowValidator` inicial com validação de campos obrigatórios e formato semver

## v0.1.0 — Sprint 1: Fundação
- Arquitetura Clean Architecture: Domain → Application → Infrastructure → API
- API Contract v1.0.0 documentado
- RunPod Serverless configurado com GHCR como registry privado
- `ContainerRegistryAuth` configurada no RunPod (ghcr-ratecbr)
- Template e Endpoint RunPod configurados via GraphQL API
- Registries: WorkflowRegistry, PipelineRegistry, ModelRegistry, CapabilityRegistry, ProviderRegistry
