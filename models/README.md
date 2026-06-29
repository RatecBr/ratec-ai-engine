# Models

Cada subdiretório contém um `metadata.yaml` descrevendo um modelo de IA suportado pelo RATEC AI ENGINE.

## Estrutura do metadata.yaml

```yaml
id: <model-id>             # identificador único no ModelRegistry
name: <nome legível>
version: "x.y.z"
status: available | unavailable | deprecated

provider_type: <type>      # tipo de capability que este modelo serve

capabilities:
  - <capability-id>        # lista de capabilities oferecidas

requirements:
  gpu: true/false
  min_vram: "24GB"
  min_memory: "4GB"

parameters:                # parâmetros padrão e limites do modelo
  ...

metadata:
  license: <licença>
  organization: <organização>
  huggingface: <repo>      # opcional
  tags: [...]
```

## Catálogo

| ID | Capability | GPU | Status |
|----|-----------|-----|--------|
| `flux-1-dev` | image-generation | 24GB VRAM | Disponível |
| `sdxl-1.0` | image-generation | 8GB VRAM | Disponível |
| `gpt-4o` | text-generation | Não (API) | Disponível |
| `whisper-large-v3` | audio-transcription | 10GB VRAM | Disponível |

## Como registrar um modelo

Os modelos são registrados programaticamente no `ModelRegistry` em `src/config/dependencies.py`.
Os arquivos `metadata.yaml` aqui servem como fonte de verdade e documentação.
Futuramente, o `ModelRegistry` poderá carregar esses metadados automaticamente via loader YAML.
