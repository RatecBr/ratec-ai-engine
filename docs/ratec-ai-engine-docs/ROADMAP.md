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

## Release 1.0.1-alpha — Consolidação da Infraestrutura

> **Status:** Em andamento  
> **Foco:** Definir a infraestrutura tecnológica oficial e preparar o ambiente para testes

### Infraestrutura tecnológica definida

| Componente | Decisão |
|-----------|---------|
| Backend principal | Firebase (Auth + Firestore + Storage) |
| Execução de modelos | AI Runtime (RunPod + ComfyUI) |
| Geração de imagens | Exclusivamente local via AI Runtime |
| APIs externas | Apenas textuais: OpenAI, Claude, Gemini |
| Proibido | Replicate, Stability, Fal.ai, Segmind, HF Inference API |

### Modelos prioritários

| Modelo | Status | VRAM | Capability |
|--------|--------|------|-----------|
| BRIA RMBG-1.4 | ▶ instalar | 4GB | background-remove |
| RealESRGAN x4plus | ▶ instalar | 4GB | image-upscale |
| FLUX.1-dev | ⏸ aguarda pós-release | 24GB | haircut, beard, makeup |
| ControlNet FLUX | ⏸ aguarda pós-release | 24GB | haircut, makeup |
| IPAdapter FLUX | ⏸ aguarda pós-release | 24GB | haircut, beard, makeup |
| Whisper large-v3 | ⏸ aguarda pós-release | 10GB | audio-transcription |
| PaddleOCR | ⏸ aguarda pós-release | — | ocr |

### Model Installation Manager

```
python scripts/install_models.py
# com HuggingFace token (necessário para BRIA RMBG):
HF_TOKEN=hf_xxx python scripts/install_models.py
```

- [ ] Executar `install_models.py` no RunPod
- [ ] BRIA RMBG-1.4 instalado e health check OK
- [ ] RealESRGAN x4plus instalado e health check OK
- [ ] Relatório de instalação gerado sem erros
- [ ] ComfyUI reconhece ambos os modelos

---

## Release 1.0.0-alpha — Fase de Validação da Plataforma

> **Status:** Em andamento  
> **Congelamento:** Nenhuma nova funcionalidade até aprovação completa

### Estado atual da plataforma (auditado em 2026-06-29)

| Componente | Status |
|-----------|--------|
| runtime/__init__.py v2.0.0 | ✅ Estável |
| runtime/bootstrap.py | ✅ Funcional |
| runtime/lab/ (SQLite + cache) | ✅ Completo |
| runtime/models/catalog/ (6 manifests) | ✅ Definidos |
| workflows com comfyui.json | ✅ 3 (identity, background-remove, image-upscale) |
| workflows planejados (sem comfyui.json) | ⏸️ 6 (beard, haircut, face-seg, makeup, try-on, image-gen) |
| playground/server.py v2.0.0 (5 abas) | ✅ Funcional |
| scripts/start.sh | ✅ Funcional |
| Dockerfile.runtime + CI/CD | ✅ Funcional |

### Etapa 1 — Validar Infraestrutura

- [ ] AI Runtime inicia corretamente no RunPod
- [ ] ComfyUI inicia automaticamente via `scripts/start.sh`
- [ ] Provider conecta ao ComfyUI local (`localhost:8188`)
- [ ] WorkflowManager encontra os workflows (`image/identity`, `image/background-remove`, `image/image-upscale`)
- [ ] Network Volume (`/runpod-volume/`) está montado e acessível
- [ ] Upload de imagem para ComfyUI funciona
- [ ] Download de resultado funciona
- [ ] GPU é detectada (`nvidia-smi`)
- [ ] Diretórios de modelos estão nos caminhos corretos

### Etapa 2 — Validar Modelos

Instalar apenas os modelos necessários para esta release:

| Modelo | Local no Volume | Capability |
|--------|----------------|------------|
| BRIA RMBG-1.4 | `/runpod-volume/models/...` | background-remove |
| RealESRGAN x4plus | `/runpod-volume/models/upscale_models/` | image-upscale |

- [ ] BRIA RMBG-1.4: download, instalação, carregamento, execução
- [ ] RealESRGAN x4plus: download, instalação, carregamento, execução
- [ ] VRAM documentada para cada modelo
- [ ] Tempo de processamento documentado para cada modelo

### Etapa 3 — Validar Capabilities

Executar exaustivamente as três capabilities:

- [ ] `image-identity`: passagem de imagem, resultado correto, sem erros
- [ ] `background-remove`: remoção de fundo, qualidade do resultado, múltiplas imagens
- [ ] `image-upscale`: upscale 4x, qualidade, tempo de processamento

### Etapa 4 — AI Playground

- [ ] Execute: executa qualquer das 3 capabilities sem erro
- [ ] History: todas as execuções gravadas, imagens salvas
- [ ] Benchmark: métricas agregadas corretas
- [ ] Compare: comparação side-by-side funciona
- [ ] Catalog: lista modelos e capabilities corretamente

### Critérios de Aprovação

A plataforma será considerada aprovada quando:

- [ ] `image-identity` funcionar de forma consistente
- [ ] `background-remove` funcionar corretamente
- [ ] `image-upscale` funcionar corretamente
- [ ] AI Playground executar qualquer Capability sem erros
- [ ] AI Runtime permanecer estável durante múltiplas execuções
- [ ] Não existirem falhas conhecidas na infraestrutura

---

## Pós-Release 1.0.0-alpha: Integração com GoodLook

Somente após a aprovação completa acima. O GoodLook consome exclusivamente via API pública — nunca conhece modelos, workflows, ComfyUI ou Runtime.

---

## Pós-Integração: Evolução da Plataforma

### Prioridade 1 — `face-segmentation`
- Definir nó ComfyUI para segmentação facial
- Implementar `comfyui.json`
- Validar como pré-requisito para haircut/beard/makeup

### Prioridade 2 — `haircut`, `beard`, `makeup`
- Instalar FLUX.1-dev + IPAdapter no Network Volume
- Implementar comfyui.json para cada capability
- Benchmarkar e comparar versões no AI Lab

### Prioridade 3 — `virtual-try-on`
- Dependência: background-remove + FLUX
- Implementar workflow
- Validar

### Backlog
- Capabilities de áudio: `audio-transcription` (Audiover, Karaokêro)
- Capabilities de tradução: Tradulino
- Dashboard de observability em produção
- Rate limiting por produto consumidor
- Autenticação de produto na API pública

---

## Métricas de qualidade da plataforma

Antes de integrar qualquer aplicativo, monitorar:

| Métrica | Meta |
|---------|------|
| Capabilities aprovadas | ≥ 3 |
| Taxa de sucesso por workflow | ≥ 95% |
| Tempo médio de execução | < 30s (imagem) |
| Consumo médio de VRAM | documentado por capability |
| Score médio de qualidade | ≥ 4/5 |
| Custo estimado por execução | definido antes da integração |
