# Como criar um Workflow

## Dois tipos de workflow

### Workflow ComfyUI (produção atual)

Workflows ComfyUI rodam diretamente no Runtime via `runtime/workflow.py`. São mais simples e diretos.

### Workflow via Clean Architecture (modo API)

Workflows registrados no `WorkflowRegistry` e roteados pelo `ExecutionManager`. Para casos que precisam de orquestração complexa.

---

## Criando um Workflow ComfyUI

### 1. Criar o diretório

```
workflows/
└── image/                    # categoria: image, audio, video, vision, multimodal
    └── meu-workflow/
        ├── comfyui.json      # workflow no formato API do ComfyUI
        └── manifest.yaml     # metadados
```

### 2. Criar o `comfyui.json`

Exporte o workflow do ComfyUI em formato API (não o formato UI):

```json
{
  "1": {
    "class_type": "LoadImage",
    "_meta": {"title": "Load Image"},
    "inputs": {
      "image": "placeholder.png",
      "upload": "image"
    }
  },
  "2": {
    "class_type": "CheckpointLoaderSimple",
    "_meta": {"title": "Load Checkpoint"},
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly.ckpt"
    }
  },
  "3": {
    "class_type": "SaveImage",
    "_meta": {"title": "Save Image"},
    "inputs": {
      "images": ["1", 0],
      "filename_prefix": "ratec_output"
    }
  }
}
```

**Regras obrigatórias:**
- Todo node deve ter `class_type` (o `WorkflowValidator` rejeita nodes sem ele)
- Inputs que referenciam outros nodes usam `["node_id", output_index]`

### 3. Criar o `manifest.yaml`

```yaml
id: image/meu-workflow
version: "1.0.0"
name: Meu Workflow de Imagem
provider: comfyui
pipeline: comfyui-image-pipeline

requirements:
  gpu: true
  min_vram: "24GB"

inputs:
  - name: image
    type: base64
    description: Imagem de entrada

outputs:
  - name: images
    type: base64[]
  - name: elapsed_ms
    type: int

estimated_time_seconds: 15
```

### 4. Usar `node_overrides` para parametrização

Para passar inputs do job para nodes específicos do workflow, use `node_overrides`:

```python
node_overrides = {
    "1": {"image": "uploaded_filename.png"},  # node_id: {input_key: value}
}
workflow = WorkflowManager.apply_node_overrides(base_workflow, node_overrides)
```

O `ComfyUIJobExecutor` aceita `node_overrides` como parâmetro de execução.

### 5. Validar antes de usar

O `WorkflowValidator` é executado automaticamente no registro. Para validar manualmente:

```python
from src.infrastructure.validators.workflow_validator import WorkflowValidator
from pathlib import Path

validator = WorkflowValidator(workflows_root=Path("workflows"))
result = validator.validate(manifest)
print(result)  # [OK] image/meu-workflow ou [FALHOU] com erros
```

---

## Criando um Workflow via Clean Architecture

### 1. Criar o Pipeline (se necessário)

Em `src/config/dependencies.py`, dentro de `_build_pipeline_registry()`:

```python
registry.register(Pipeline(
    id="meu-pipeline",
    name="Meu Pipeline",
    steps=[
        PipelineStep(
            id="step-1",
            capability="image-generation",
            action="generate",
            model_id=None,              # None = CapabilityRegistry decide
            execution_strategy="auto",
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
    steps=[
        WorkflowStep(
            id="gerar-imagem",
            pipeline_id="meu-pipeline",
        )
    ],
))
```

### 3. Criar o `manifest.yaml`

Em `workflows/image/gerar-foto-perfil/manifest.yaml`:

```yaml
id: image/gerar-foto-perfil
version: "1.0.0"
name: Gerar Foto de Perfil
pipeline: meu-pipeline
provider: comfyui
requirements:
  gpu: true
  min_vram: "24GB"
```

### 4. Testar

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "image/gerar-foto-perfil", "input": {"prompt": "foto profissional"}}'
```

---

## Regras

- Workflows **nunca** referenciam modelos diretamente
- Workflows **nunca** referenciam backends (`runpod`, `modal`, etc.)
- Todo workflow deve ter `manifest.yaml` com versão no formato `x.y.z` (semver)
- Workflows ComfyUI devem ter `provider: comfyui` no manifest
- Todo `comfyui.json` deve ter `class_type` em todos os nodes
- Organize por categoria: `image/`, `audio/`, `video/`, `vision/`, `multimodal/`

## Workflow de referência

O workflow `image/identity` é o workflow de validação de infraestrutura:
- Path: `workflows/image/identity/`
- Função: recebe imagem → LoadImage → SaveImage → retorna mesma imagem
- Propósito: validar que o Runtime e o ComfyUI estão funcionais sem depender de modelos
