# Arquitetura — RATEC AI ENGINE

## Visão geral

O RATEC AI ENGINE é a plataforma centralizada de IA da RATEC. Todos os produtos
(GOODLOOK, Audiover, Internice, Animapages, Karaokêro, Tradulino) consomem apenas
esta API, nunca integrando diretamente com modelos ou infraestrutura de IA.

## Fluxo de execução

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
  │  ExecutionManager    │  Roteia pela execution_strategy
  └──────────┬───────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
 LocalBackend   RunPodBackend   (futuro: Modal, Replicate, AWS…)
     │               │
     └───────┬───────┘
             │  ExecutionResult
             ▼
       Job.mark_completed()
```

## Camadas

| Camada | Responsabilidade | Conhece |
|--------|-----------------|---------|
| **Workflow** | Processo de negócio | Pipeline IDs |
| **Pipeline** | Orquestração técnica | Capabilities, Model IDs |
| **PipelineEngine** | Execução de steps | ExecutionManager (abstrato) |
| **ExecutionManager** | Roteamento de compute | ExecutionBackends |
| **ExecutionBackend** | Infraestrutura concreta | RunPod API, Modal API, etc. |
| **ModelRegistry** | Catálogo de modelos | AIModel metadata |
| **CapabilityRegistry** | Mapeamento capability → modelos | ModelRegistry |

## Princípios arquiteturais

- **Inversão de dependência**: camadas superiores dependem de interfaces, nunca de implementações
- **Substituibilidade de provider**: trocar RunPod por Modal = registrar novo `ExecutionBackend`
- **Substituibilidade de modelo**: trocar FLUX por SDXL = atualizar `ModelRegistry`
- **Desacoplamento de workflows**: workflows nunca conhecem modelos ou backends
- **Extensibilidade**: novos produtos da RATEC consomem a mesma API sem modificações no motor
