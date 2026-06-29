# Workflows

Cada subdiretório contém um `manifest.yaml` descrevendo um Workflow registrado no RATEC AI ENGINE.

## Estrutura do Manifest

```yaml
id: <workflow-id>          # identificador único, usado na API (/v1/jobs)
version: "1.0.0"
name: <nome legível>
description: <descrição>

pipeline: <pipeline-id>    # pipeline que executa este workflow
model: <model-id>          # modelo preferencial (null = resolvido via Capability Registry)
provider: <provider-id>    # provider preferencial (null = resolvido via ExecutionManager)
capability: <capability>   # capacidade solicitada (alternativa ao model direto)

requirements:
  gpu: true/false
  min_vram: "24GB"
  min_memory: "4GB"

estimated_time_seconds: <int>

metadata:
  category: <categoria>
  tags: [...]
  stable: true/false
```

## Princípio de desacoplamento

Um Workflow **nunca** referencia diretamente um modelo ou backend de execução.
Ele declara uma **capacidade** e o motor resolve qual modelo/backend usar em runtime.

## Workflows disponíveis

| ID | Pipeline | Capability | Status |
|----|----------|-----------|--------|
| `echo` | `echo-pipeline` | `echo` | Estável |
| `image-generation` | `image-generation-pipeline` | `image-generation` | Em desenvolvimento |
