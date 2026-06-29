# START HERE

## Objetivo

Construir o RATEC AI ENGINE antes de integrá-lo ao GOODLOOK.

## Estado atual (Sprint 5 concluída)

As fases abaixo foram concluídas:

1. ~~Revisar a arquitetura~~ — Clean Architecture implementada
2. ~~Criar a estrutura do projeto~~ — Domain / Application / Infrastructure / API
3. ~~Criar a API~~ — `/v1/jobs`, `/v1/health`, `/v1/providers`, `/v1/workflows`
4. ~~Criar o Workflow Engine~~ — WorkflowRegistry + WorkflowEngine
5. ~~Criar a camada de Providers~~ — ComfyUI Provider completo (`src/infrastructure/providers/comfyui/`)
6. ~~Preparar execução no RunPod Serverless~~ — handler + Runtime + boot IaC
7. ~~Criar Docker~~ — `Dockerfile.runtime` + CI/CD `build-runtime.yml`
8. ~~Documentar a arquitetura~~ — `docs/` atualizado

## Próximos passos

1. Definir o primeiro workflow de produção (GOODLOOK ou outro produto)
2. Carregar modelos no Network Volume
3. Executar o workflow end-to-end em produção
4. Integrar o primeiro produto consumidor

## Regras permanentes

- Não implementar regras de negócio dos aplicativos no motor.
- O motor deve ser reutilizável por todos os sistemas da RATEC.
- Aplicar Clean Architecture, SOLID e baixo acoplamento.
- Workflows nunca referenciam modelos ou backends diretamente.
- Modelos nunca ficam na imagem Docker.

## Onde começar

| Documento | Conteúdo |
|-----------|---------|
| `docs/00-VISION.md` | Visão e princípios da plataforma |
| `docs/architecture/overview.md` | Arquitetura completa + diagramas |
| `docs/ratec-ai-engine-docs/COMFYUI.md` | Provider ComfyUI e Runtime |
| `docs/ratec-ai-engine-docs/RUNPOD.md` | Infraestrutura RunPod |
| `docs/ratec-ai-engine-docs/DECISIONS.md` | Decisões arquiteturais e motivações |
| `docs/workflows/creating-workflows.md` | Como criar novos workflows |
| `docs/ratec-ai-engine-docs/CHANGELOG.md` | Histórico de sprints |
