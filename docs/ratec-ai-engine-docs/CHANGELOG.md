# CHANGELOG

## Unreleased — Hotfix + Console Web (2026-07-01)

> **Objetivo:** Corrigir bugs críticos que impediam o worker de inicializar e conectar o Console Web ao Engine em produção.

### Correções críticas

**`handler.py` — docstring não fechada (bug de silêncio total)**
- A docstring de módulo estava aberta na linha 1 sem fechamento — todo o arquivo (imports, `_runtime`, `handler`, `runpod.serverless.start`) era interpretado como string literal; o worker iniciava e encerrava silenciosamente com exit code 1
- Corrigido: docstring fechada após a linha 3; todo o código passa a ser executado

**`Dockerfile.serverless` — COPY statements ausentes**
- Apenas `handler.py` e `build_info.json*` eram copiados para a imagem
- `runtime/`, `src/` e `workflows/` estavam ausentes → `ModuleNotFoundError: No module named 'runtime'` ao iniciar
- Corrigido: adicionados os três COPY statements faltantes

**`runtime/__init__.py` — violação de isolamento standalone**
- `_print_startup()` importava `from src.application.admin.version_provider import version_provider`, quebrando a regra de que `runtime/` é um módulo independente de `src/`
- Removido o import e o banner duplicado `===`; o banner agora é responsabilidade exclusiva do `handler.py`

### Novas funcionalidades

**`handler.py` — rotas públicas `/v1/*` para o Console Web**
- `GET /v1/health` — saúde do worker (status, versão, uptime)
- `GET /v1/capabilities` — lista de capabilities do `_CAPABILITY_ROUTES` (9 itens em produção)
- `GET /v1/workflows` — workflows disponíveis via `WorkflowManager.list_available()`
- `GET /v1/models` — modelos ativos lidos do `active_models.json` do volume
- `GET /v1/jobs` — retorna lista vazia (sem tracking de jobs no modelo serverless)
- `POST /v1/jobs` — executa job de forma síncrona via `_runtime.handle()`, retorna resultado imediato
- `GET /v1/jobs/{id}` — responde `not_found` (sem persistência entre invocações serverless)
- Rotas `/v1/*` retornam dados diretos sem o envelope `{success, data}` (diferente das rotas `/admin/`)

**`handler.py` — endpoint `/admin/version`** *(adicionado na sessão anterior)*
- Retorna `build_info.json` gerado pelo CI/CD: versão, commit, branch, data de build, docker tag, GPU model, `worker_started_at`

### Manutenção

- `lab_data/` removido do histórico git (`git rm -r --cached`) e adicionado ao `.gitignore`
- Scripts de diagnóstico na raiz (`/test_*.py`) adicionados ao `.gitignore`
- `develop` sincronizado com `main` via merge

---

## Unreleased — Release 1.0.2-alpha: Política Oficial de Gerenciamento de Modelos

> **Objetivo:** Tornar a plataforma resiliente — nenhuma Capability depende de um modelo específico.

**Política de modelos:**
- Cada Capability possui lista ordenada de modelos compatíveis com `fallback_priority`
- O instalador tenta o modelo preferencial; se falhar (auth, erro de rede), instala a próxima alternativa
- O Runtime lê `active_models.json` do Network Volume no boot e seleciona o workflow correto
- Modelos com `requires_hf_token: true` são opcionais — não bloqueiam a plataforma

**Novos modelos no catálogo:**
- `birefnet` — fallback open source (MIT) para `background-remove`; prioridade 2; sem autenticação; instalado via custom node `ComfyUI_birefnet_ll`

**Campos adicionados aos manifests:**
- `preferred`, `fallback_priority`, `requires_hf_token`, `requires_license_acceptance`, `license_type`, `download_strategy`
- `workflow_variants` — lista de arquivos `comfyui.{model_id}.json` disponíveis

**Novo arquivo de workflow:**
- `workflows/image/background-remove/comfyui.birefnet.json` — workflow BiRefNet para background-remove

**Runtime:**
- `RuntimeConfig.active_models_path` — path para `active_models.json` no volume
- `RuntimeConfig.load_active_models()` — lê o arquivo, retorna `{}` se não encontrado
- `Runtime._active_models` — mapa `workflow_id → model_id` carregado no boot
- `Runtime._execute_comfyui()` — usa `load_comfyui(workflow_id, model_id=active_model)`
- `Runtime._health()` — expõe `active_models` na resposta de health check

**WorkflowManager:**
- `load_comfyui(workflow_id, model_id=None)` — carrega `comfyui.{model_id}.json` se existir, senão `comfyui.json`
- `list_model_variants(workflow_id)` — lista model IDs com workflow dedicado

**Model Installation Manager v2.0 (`scripts/install_models.py`):**
- `CAPABILITY_PRIORITIES` — modelos por capability em ordem de preferência
- Tenta instalar modelos em prioridade; pula se requer auth sem token; tenta próximo
- Escreve `active_models.json` no volume com o modelo instalado por capability
- Relatório mostra todos os modelos tentados, motivo do skip, qual ficou ativo

**AI Playground:**
- `/api/catalog/capabilities` — endpoint com política de modelos por capability
- `/api/capabilities` — agora inclui `active_models`
- Aba Catalog: modelos com badges `preferencial`/`fallback #N`/`HF_TOKEN`
- Aba Capabilities: coluna "Modelo ativo" + lista de alternativas com prioridade e auth

**Diretriz #13:** Nenhuma Capability depende de um único modelo — toda nova Capability deve ter ao menos uma alternativa open source sem autenticação

---

## Unreleased — Release 1.0.1-alpha: Consolidação da Infraestrutura

> **Objetivo:** Definir oficialmente a infraestrutura tecnológica da plataforma e preparar o ambiente para os testes funcionais no AI Playground.

**Decisões de infraestrutura:**
- Firebase permanece como backend principal (Authentication, Firestore, Storage) — sem migração
- AI Runtime responsável exclusivamente pela execução de modelos — nunca acessa Firebase diretamente
- Modelos locais como estratégia padrão; APIs externas de geração de imagens proibidas nesta fase
- APIs externas permitidas apenas para tarefas textuais: OpenAI, Claude, Gemini
- Modelos prioritários da plataforma: BRIA RMBG, RealESRGAN, FLUX, ControlNet, IPAdapter, Whisper, PaddleOCR

**Model Installation Manager:**
- `scripts/install_models.py` — instala BRIA RMBG-1.4 e RealESRGAN x4plus no Network Volume
- Verifica montagem do volume, faz download, instala custom nodes, executa health check
- Gera relatório JSON com status de cada modelo e resultado dos health checks
- Salva relatório em `/runpod-volume/logs/install_report_{ts}.json`

**Correções:**
- `runtime/bootstrap.py` — adicionado `models/BRIA` aos diretórios do Network Volume
- `runtime/models/catalog/bria-rmbg/manifest.yaml` — URL de download corrigida para arquivo direto (`resolve/main/model.pth`); adicionado `requires_hf_token: true`

**Nova diretriz permanente:**
- Diretriz #12 — Avaliação de Novas Dependências Tecnológicas: 5 perguntas antes de incorporar qualquer nova dependência

---

## Unreleased — Release 1.0.0-alpha: Fase de Validação da Plataforma

> **Objetivo:** Validar o funcionamento de ponta a ponta antes da integração com o GoodLook.  
> **Congelamento:** Nenhuma nova funcionalidade, abstração ou reorganização arquitetural.

**Estado da plataforma (auditado 2026-06-29):**
- 3 capabilities com `comfyui.json` prontas para validação: `image-identity`, `background-remove`, `image-upscale`
- 6 capabilities planejadas com apenas `manifest.yaml` (aguardam próxima fase): beard, haircut, face-segmentation, makeup, virtual-try-on, image-generation
- Todos os demais componentes (Runtime, Lab, Playground, IaC) estruturalmente completos

**Critérios de aprovação:**
- `image-identity` funciona de forma consistente
- `background-remove` funciona corretamente (BRIA RMBG-1.4 instalado)
- `image-upscale` funciona corretamente (RealESRGAN x4plus instalado)
- AI Playground executa qualquer capability sem erros
- AI Runtime estável durante múltiplas execuções
- Infraestrutura sem falhas conhecidas

---

## v2.0.0 — Epic 3: AI Lab
- **Arquitetura congelada** — nenhuma alteração estrutural sem ADR aprovada
- `runtime/lab/database.py` — SQLite (stdlib): tabelas `executions` e `cache_entries`; índices por capability e data
- `runtime/lab/cache.py` — `compute_key()`: SHA-256 de `(workflow_id + input_hash + node_overrides)`
- `runtime/lab/__init__.py` — `Lab` facade: `record()`, `save_input/output_images()`, `cache_get/set()`
- `runtime/models/catalog/` — 6 manifests YAML: bria-rmbg, realesrgan, flux, controlnet, ipadapter, whisper
  - Campos: id, versão, vendor, licença, VRAM, capabilities, nodes ComfyUI, URL de origem
- `playground/catalog.py` — leitor YAML do catálogo via `pyyaml`
- `playground/server.py` v2.0 — 5 abas:
  - **Execute**: capability + imagem + overrides + cache experimental → grava em histórico
  - **History**: tabela filtrável por capability/sucesso, expansão com imagens, avaliação manual ★ (1–5)
  - **Compare**: side-by-side de dois registros do histórico por ID
  - **Benchmark**: métricas agregadas por capability e workflow (success rate, avg ms, avg VRAM, avg score)
  - **Catalog**: modelos (status, VRAM, licença, capabilities), capabilities (active/planned), cache (hits + limpar)
- `playground/requirements.txt` — adicionado `pyyaml` e `aiofiles`
- Fluxo obrigatório validado: Workflow → Playground → Benchmark → Aprovar → API → Aplicativo

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
