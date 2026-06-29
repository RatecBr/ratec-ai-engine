# AI Playground

Interface web para testar workflows do RATEC AI Runtime localmente.

## Requisitos

```bash
pip install -r playground/requirements.txt
```

## Como usar

1. Inicie o ComfyUI localmente:
   ```bash
   cd /caminho/do/comfyui
   python main.py --listen 127.0.0.1 --port 8188
   ```

2. Em outro terminal, inicie o playground a partir da raiz do projeto:
   ```bash
   uvicorn playground.server:app --port 7860 --reload
   ```

3. Acesse `http://localhost:7860` no browser

## Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `COMFYUI_URL` | `http://127.0.0.1:8188` | URL do ComfyUI local |
| `RUNPOD_VOLUME_PATH` | `/runpod-volume` | Volume path (pode ser local) |

## Funcionalidades

- Selecionar qualquer capability/workflow disponível
- Upload de imagem por clique ou drag & drop
- Configurar node_overrides como JSON
- Ver resultado visual + dados completos de timing
- Visualizar o JSON de resposta completo

## Princípio

Nenhum workflow deve ser integrado a um aplicativo antes de ser validado aqui.

Fluxo:
```
Workflow → Playground (validar) → Capability → API → Aplicativo
```
