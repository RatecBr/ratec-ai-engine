# ROADMAP — RATEC AI ENGINE

## Épicos e Sprints concluídos

### Epic 1 — Fundação da Plataforma

#### Sprint 1 — Fundação (concluída)
- Clean Architecture estabelecida (Domain → Application → Infrastructure → API)
- API Contract v1.0.0
- RunPod Serverless + GHCR configurados
- Registries: Workflow, Pipeline, Model, Capability, Provider

#### Sprint 2 — GPU Policy + Observability (concluída)
- Endpoint restrito a RTX A5000 (AMPERE_48)
- GPU observability em todas as respostas
- WorkflowValidator inicial

#### Sprint 3 — ComfyUI Provider (concluída)
- Provider ComfyUI desacoplado (`src/infrastructure/providers/comfyui/`)
- ComfyUIBackend registrado no ExecutionManager
- node_overrides para parametrização de workflows

#### Sprint 4 — AI Runtime on RunPod (concluída)
- Workflow `image/identity` funcional
- Network Volume com symlinks para modelos
- Boot sequence via `scripts/start.sh`

#### Sprint 5 — Runtime Consolidation (concluída)
- Módulo `runtime/` standalone + `handler.py` thin entry point
- `Dockerfile.runtime` + CI/CD `build-runtime.yml`
- WorkflowValidator com checks de VRAM e provider
- Estrutura de workflows por categoria

---

### Epic 2 — Biblioteca de Workflows de IA (concluído)
- Mudança estratégica: plataforma de todos os produtos RATEC (não só GOODLOOK)
- HairFastGAN descartado — substituído por FLUX + IPAdapter + segmentação
- Executor genérico ComfyUI: novos workflows sem alteração de código
- Capability routing: `background-remove` → `image/background-remove`, etc.
- Workflows implementados: `image/background-remove` (BRIA RMBG), `image/image-upscale` (RealESRGAN)
- Manifests planejados: `face-segmentation`, `haircut`, `beard`, `makeup`, `virtual-try-on`
- AI Playground v1: FastAPI + HTML para testar workflows localmente

---

### Epic 3 — AI Lab (concluído)
- **Arquitetura congelada** — nenhuma alteração estrutural sem ADR
- `runtime/lab/` — SQLite para histórico, benchmark, avaliações, cache experimental
- `runtime/models/catalog/` — 6 manifests: BRIA RMBG, RealESRGAN, FLUX, ControlNet, IPAdapter, Whisper
- AI Playground v2 — 5 abas: Execute, History, Compare, Benchmark, Catalog
- Fluxo obrigatório: Workflow → Playground → Benchmark → Aprovar → API → Aplicativo

---

## Próximo foco: Capabilities em produção

### Prioridade 1 — `background-remove` (próximo)
- Instalar modelo BRIA RMBG-1.4 no Network Volume
- Testar e benchmarkar no AI Playground
- Aprovar + publicar como capability estável

### Prioridade 2 — `image-upscale`
- Instalar modelo RealESRGAN x4plus no Network Volume
- Testar e benchmarkar
- Aprovar + publicar

### Prioridade 3 — `face-segmentation`
- Definir nó ComfyUI para segmentação facial
- Implementar `comfyui.json`
- Validar como pré-requisito para haircut/beard/makeup

### Prioridade 4 — `haircut`, `beard`, `makeup`
- Instalar FLUX.1-dev + IPAdapter no Network Volume
- Implementar comfyui.json para cada capability
- Benchmarkar e comparar versões no AI Lab

### Prioridade 5 — `virtual-try-on`
- Dependência: background-remove + FLUX
- Implementar workflow
- Validar

### Backlog
- Integração com o primeiro produto consumidor (GOODLOOK)
- Capabilities de áudio: `audio-transcription` (Audiover, Karaokêro)
- Capabilities de tradução: Tradulino
- Dashboard de observability em produção
- Rate limiting por produto consumidor
- Autenticação de produto na API pública

---

## Métricas de qualidade da plataforma (pós-Epic 3)

Antes de integrar qualquer aplicativo, monitorar:

| Métrica | Meta |
|---------|------|
| Capabilities aprovadas | ≥ 3 |
| Taxa de sucesso por workflow | ≥ 95% |
| Tempo médio de execução | < 30s (imagem) |
| Consumo médio de VRAM | documentado por capability |
| Score médio de qualidade | ≥ 4/5 |
| Custo estimado por execução | definido antes da integração |
