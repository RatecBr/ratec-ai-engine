# Como criar um Workflow

## Conceito

Um Workflow representa um processo de negócio.
Ele **não** conhece modelos, providers ou backends de execução.
Cada step referencia apenas um `pipeline_id`.

## Passos

### 1. Criar o Pipeline (se necessário)

Em `src/config/dependencies.py`, dentro de `_build_pipeline_registry()`:

```python
registry.register(Pipeline(
    id="meu-pipeline",
    name="Meu Pipeline",
    description="Descrição técnica do que o pipeline faz",
    steps=[
        PipelineStep(
            id="step-1",
            capability="image-generation",   # capability abstrata
            action="generate",
            model_id="flux-1-dev",            # opcional — None = CapabilityRegistry decide
            execution_strategy="auto",        # auto, serverless, local
            parameters={"prompt": "$input.prompt"},
        )
    ],
))
```

### 2. Criar o Workflow

```python
registry.register(Workflow(
    id="gerar-foto-perfil",
    name="Gerar Foto de Perfil",
    description="Gera uma foto de perfil profissional a partir de um prompt",
    steps=[
        WorkflowStep(
            id="gerar-imagem",
            pipeline_id="meu-pipeline",
        )
    ],
))
```

### 3. Criar o manifest.yaml

Em `workflows/gerar-foto-perfil/manifest.yaml`:

```yaml
id: gerar-foto-perfil
version: "1.0.0"
name: Gerar Foto de Perfil
pipeline: meu-pipeline
capability: image-generation
requirements:
  gpu: true
  min_vram: "24GB"
estimated_time_seconds: 15
```

### 4. Testar

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "gerar-foto-perfil", "input": {"prompt": "foto profissional"}}'
```

## Regras

- Workflows **nunca** referenciam modelos diretamente
- Workflows **nunca** referenciam backends (`runpod`, `modal`, etc.)
- Use `capability` no PipelineStep para que o CapabilityRegistry resolva o melhor modelo
- Documente sempre com um `manifest.yaml`
