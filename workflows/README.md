# Workflows

Biblioteca de workflows de IA do RATEC AI ENGINE.
Cada workflow representa uma capability reutilizável por qualquer produto RATEC.

## Estrutura de diretórios

```
workflows/
├── image/
│   ├── identity/              ✅ active  — validação de infraestrutura (sem IA)
│   ├── background-remove/     ✅ active  — remoção de fundo (BRIA RMBG)
│   ├── image-upscale/         ✅ active  — super-resolução 4x (RealESRGAN)
│   ├── face-segmentation/     🔜 planned — segmentação facial
│   ├── haircut/               🔜 planned — troca de cabelo (FLUX + IPAdapter)
│   ├── beard/                 🔜 planned — barba (FLUX + IPAdapter)
│   ├── makeup/                🔜 planned — maquiagem (FLUX + IPAdapter)
│   └── virtual-try-on/        🔜 planned — prova virtual de roupa
├── audio/
├── video/
├── vision/
└── multimodal/
```

## Capabilities disponíveis

| Capability | Workflow | Status | VRAM | Modelos necessários |
|-----------|---------|--------|------|---------------------|
| `image-identity` | `image/identity` | ✅ Active | 0GB | nenhum |
| `background-remove` | `image/background-remove` | ✅ Active | 8GB | RMBG-1.4 |
| `image-upscale` | `image/image-upscale` | ✅ Active | 4GB | RealESRGAN_x4plus.pth |
| `face-segmentation` | `image/face-segmentation` | 🔜 Planned | 8GB | — |
| `haircut` | `image/haircut` | 🔜 Planned | 24GB | FLUX.1-dev + IPAdapter |
| `beard` | `image/beard` | 🔜 Planned | 24GB | FLUX.1-dev + IPAdapter |
| `makeup` | `image/makeup` | 🔜 Planned | 24GB | FLUX.1-dev + IPAdapter |
| `virtual-try-on` | `image/virtual-try-on` | 🔜 Planned | 24GB | FLUX.1-dev + IPAdapter |

## Como os aplicativos consomem capabilities

Os aplicativos NUNCA referenciam workflows diretamente. Solicitam apenas a capability:

```json
{
  "workflow_id": "background-remove",
  "input": {
    "image": "<base64>"
  }
}
```

O Runtime resolve automaticamente: `background-remove` → `image/background-remove/comfyui.json`

## Formato do comfyui.json

Convenções obrigatórias:
- **Node "1"** é sempre o `LoadImage` (input principal da imagem)
- Todo node deve ter `class_type`
- Inputs que referenciam outros nodes: `["node_id", output_index]`

Exemplo mínimo:
```json
{
  "1": {
    "class_type": "LoadImage",
    "inputs": {"image": "placeholder.png", "upload": "image"}
  },
  "2": {
    "class_type": "SaveImage",
    "inputs": {"images": ["1", 0], "filename_prefix": "ratec_output"}
  }
}
```

## Estrutura do manifest.yaml

```yaml
id: image/meu-workflow         # categoria/nome
version: "1.0.0"               # semver obrigatório
name: Nome Legível
provider: comfyui
status: active                 # active | planned | deprecated

requirements:
  gpu: true
  min_vram: "8GB"
  custom_nodes: [...]          # nodes do ComfyUI-Manager necessários
  models: [...]                # modelos no Network Volume

inputs:
  - name: image
    type: base64

outputs:
  - name: images
    type: object[]
```

## Workflow de referência

**`image/identity`** — pipeline de validação: LoadImage → SaveImage.
Sem modelos, sem IA. Funciona em qualquer estado do ambiente.
Use para confirmar que o Runtime e ComfyUI estão operacionais.

## Componentes reutilizáveis

```
background-remove ←──────────────────┐
face-segmentation ←──┐               │
                      ├── haircut ────┤
                      ├── beard ──────┤
                      └── makeup ─────┤
                                      │
image-upscale ←───────────────────────┘
```

## Testando com o AI Playground

Todo workflow deve ser validado no Playground antes de disponibilizado na API:

```bash
pip install -r playground/requirements.txt
uvicorn playground.server:app --port 7860
# Abra http://localhost:7860
```
