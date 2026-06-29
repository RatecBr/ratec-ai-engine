# START HERE

## Objetivo

Construir o RATEC AI ENGINE — plataforma oficial de IA de todos os produtos RATEC.

## Estado atual (Epic 3 concluído)

### ✅ Epic 1 — Fundação (Sprints 1–5)
1. ~~Revisar a arquitetura~~ — Clean Architecture implementada
2. ~~Criar a estrutura do projeto~~ — Domain / Application / Infrastructure / API
3. ~~Criar a API~~ — `/v1/jobs`, `/v1/health`, `/v1/providers`, `/v1/workflows`
4. ~~Criar o Workflow Engine~~ — WorkflowRegistry + WorkflowEngine
5. ~~Criar a camada de Providers~~ — ComfyUI Provider (`src/infrastructure/providers/comfyui/`)
6. ~~Preparar execução no RunPod Serverless~~ — handler + Runtime + IaC
7. ~~Criar Docker~~ — `Dockerfile.runtime` + CI/CD `build-runtime.yml`

### ✅ Epic 2 — Biblioteca de Workflows
- ~~Capability routing~~ — `background-remove`, `image-upscale`, `haircut`, etc.
- ~~Executor genérico ComfyUI~~ — novos workflows sem código adicional
- ~~AI Playground v1~~ — interface de testes local

### ✅ Epic 3 — AI Lab
- ~~Congelar arquitetura~~ — nenhuma mudança estrutural sem ADR
- ~~Histórico de execuções~~ — SQLite com imagens, métricas, avaliações
- ~~Benchmark~~ — métricas agregadas por capability e workflow
- ~~Cache experimental~~ — SHA-256 de inputs para reutilização em pesquisa
- ~~Catálogo de modelos~~ — 6 manifests YAML (BRIA RMBG, RealESRGAN, FLUX, ControlNet, IPAdapter, Whisper)
- ~~AI Playground v2~~ — 5 abas: Execute, History, Compare, Benchmark, Catalog

## Próximos passos

**Foco: colocar capabilities em produção, uma por vez.**

1. **Instalar BRIA RMBG-1.4** no Network Volume → testar `background-remove` no Playground → benchmarkar → aprovar
2. **Instalar RealESRGAN x4plus** → validar `image-upscale` → aprovar
3. **Implementar `face-segmentation`** com o nó ComfyUI correto → validar
4. **Instalar FLUX.1-dev + IPAdapter** → implementar `haircut` → benchmarkar → aprovar

Nenhuma capability vai para o aplicativo sem aprovação no AI Lab.

## Regras permanentes

- Arquitetura **congelada** — novidades apenas em capabilities, nunca na estrutura
- Workflows **nunca** referenciam modelos ou backends diretamente
- Apps **nunca** conhecem modelos, providers ou workflows
- Modelos **nunca** ficam na imagem Docker

## Referência rápida

| Documento | Conteúdo |
|-----------|---------|
| `docs/00-VISION.md` | Visão e princípios |
| `docs/architecture/overview.md` | Arquitetura completa + estrutura de diretórios |
| `docs/ratec-ai-engine-docs/DECISIONS.md` | Todas as decisões arquiteturais |
| `docs/ratec-ai-engine-docs/ROADMAP.md` | Épicos, sprints e próximas prioridades |
| `docs/ratec-ai-engine-docs/RUNPOD.md` | Infraestrutura RunPod |
| `docs/ratec-ai-engine-docs/COMFYUI.md` | Provider ComfyUI e Runtime |
| `docs/workflows/creating-workflows.md` | Como criar novos workflows |
| `playground/README.md` | Como usar o AI Lab Playground |
| `docs/ratec-ai-engine-docs/CHANGELOG.md` | Histórico completo |
