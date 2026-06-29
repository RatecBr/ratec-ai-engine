# START HERE

## Objetivo

Construir o RATEC AI ENGINE antes de integrá-lo ao GOODLOOK.

## Ordem obrigatória

1. Revisar a arquitetura.
2. Criar a estrutura do projeto.
3. Criar a API (/v1/jobs, /v1/health, /v1/providers, /v1/workflows).
4. Criar o Workflow Engine.
5. Criar a camada de Providers.
6. Preparar execução no RunPod Serverless.
7. Criar Docker.
8. Documentar toda a arquitetura.

## Regras

- Não integrar o GOODLOOK nesta fase.
- Não implementar regras de negócio dos aplicativos.
- O motor deve ser reutilizável por todos os sistemas da RATEC.
- Aplicar Clean Architecture, SOLID e baixo acoplamento.
- O primeiro consumidor será o GOODLOOK apenas após a conclusão da plataforma.
