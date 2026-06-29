# ROADMAP — RATEC AI ENGINE

## Sprints concluídas

### Sprint 1 — Fundação (concluída)
- Clean Architecture estabelecida
- API Contract v1.0.0
- RunPod Serverless + GHCR configurados
- Registries: Workflow, Pipeline, Model, Capability, Provider

### Sprint 2 — GPU Policy + Observability (concluída)
- Endpoint RestritO a RTX A5000 (AMPERE_48)
- GPU observability em todas as respostas
- WorkflowValidator inicial

### Sprint 3 — ComfyUI Provider (concluída)
- Provider ComfyUI desacoplado (8 arquivos em `src/infrastructure/providers/comfyui/`)
- ComfyUIBackend registrado no ExecutionManager
- node_overrides para parametrização de workflows

### Sprint 4 — AI Runtime on RunPod (concluída)
- Workflow `image/identity` funcional (LoadImage → SaveImage)
- Network Volume com symlinks para todos os dirs de modelos
- `scripts/start.sh` — boot IaC do ambiente
- Observability block em todas as respostas

### Sprint 5 — Runtime Consolidation (concluída)
- Módulo `runtime/` standalone (sem dependências de `src/`)
- `handler.py` → thin entry point (10 linhas)
- `Dockerfile.runtime` substitui `Dockerfile.comfyui`
- CI/CD: `build-runtime.yml`
- WorkflowValidator expandido com VRAM e provider checks
- Estrutura de diretórios de workflows por categoria

## Próximas sprints

### Sprint 6 — Primeiro Workflow Real (a definir)
- Workflow de produção para GOODLOOK ou outro produto RATEC
- Modelos carregados via Network Volume
- Testes de ponta a ponta com imagens reais

### Sprint 7 — Integração com Produto (a definir)
- Integração com o primeiro consumidor real
- Autenticação de produto na API
- Monitoramento de jobs em produção

### Backlog
- Suporte a múltiplos workflows ComfyUI em produção
- Workflows de áudio (Audiover, Karaokêro)
- Workflows de vídeo (Animapages)
- Workflows de tradução (Tradulino)
- Dashboard de observability
- Rate limiting por produto consumidor
