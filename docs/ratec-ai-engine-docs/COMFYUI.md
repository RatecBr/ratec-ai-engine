# ComfyUI — Provider e Runtime

O ComfyUI é o motor de execução de workflows de imagem da plataforma RATEC AI ENGINE.
É integrado em dois níveis: como **Provider** na Clean Architecture e como **servidor local** no Runtime.

## Arquitetura

### Provider (Clean Architecture)

Localizado em `src/infrastructure/providers/comfyui/`, o ComfyUI Provider é completamente desacoplado do Runtime.

```
src/infrastructure/providers/comfyui/
├── __init__.py           # exports públicos
├── client.py             # ComfyUIClient — HTTP client
├── exceptions.py         # exceções tipadas
├── job_executor.py       # ComfyUIJobExecutor
├── models.py             # ComfyUIPromptResponse, ComfyUIOutputImage, ComfyUIJobResult
├── provider.py           # ComfyUIProvider(BaseProvider)
├── result_parser.py      # ComfyUIResultParser
└── workflow_loader.py    # ComfyUIWorkflowLoader
```

**Exceções:**
- `ComfyUIError` — base
- `ComfyUIConnectionError` — falha de conectividade
- `ComfyUIWorkflowNotFoundError` — arquivo comfyui.json não encontrado
- `ComfyUITimeoutError` — polling excedeu timeout
- `ComfyUIExecutionError` — node_errors na execução

**ComfyUIClient:**
- UUID único por sessão (`_client_id = str(uuid.uuid4())`)
- Métodos: `submit_prompt`, `get_history`, `get_queue`, `upload_image`, `health_check`

**ComfyUIProvider:**
- `ProviderType.COMFYUI`
- Capabilities: `image-generation`, `inpainting`, `image-to-image`, `upscaling`

**ComfyUIJobExecutor:**
- `node_overrides: dict` — sobrescreve inputs de nodes específicos do workflow
- Exemplo: `{"1": {"image": "minha_foto.png"}}` → atualiza o node `1`

### ExecutionBackend

`ComfyUIBackend(BaseExecutionBackend)` registrado no `ExecutionManager`:
- `backend_id = "comfyui"`
- `supports_strategy("auto", "comfyui")`
- Prioridade na ordem: `("runpod", "comfyui", "modal", "replicate", "aws", "azure", "kubernetes")`

### Runtime (módulo standalone)

O módulo `runtime/` no container RunPod usa ComfyUI como servidor local:

```
runtime/
├── executor.py     # ComfyUIExecutor: submit + poll + parse_images
├── server.py       # ComfyUIServer: start/wait_ready/stop
├── workflow.py     # WorkflowManager: load/list/apply_overrides
├── upload.py       # upload de imagem base64 → ComfyUI
└── download.py     # download de imagem ComfyUI → base64
```

**ComfyUIExecutor:**
1. `submit(client, workflow)` → `POST /prompt` → retorna `prompt_id`; levanta erro se `node_errors`
2. `poll(client, prompt_id, timeout)` → `GET /history/{id}` com `asyncio.sleep(poll_interval)`
3. `parse_images(history_entry)` → extrai `filename, subfolder, type, node_id`

## Formato do Workflow (API Format)

O ComfyUI usa um formato JSON de grafo de nodes:

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
    "class_type": "SaveImage",
    "_meta": {"title": "Save Image"},
    "inputs": {
      "images": ["1", 0],
      "filename_prefix": "ratec_output"
    }
  }
}
```

**Regras:**
- Cada key é o ID do node (string numérica)
- `class_type` é obrigatório em todos os nodes (validado pelo `WorkflowValidator`)
- Inputs que referenciam outros nodes usam `["node_id", output_index]`

## Convenção de arquivos

Cada workflow ComfyUI segue a estrutura:

```
workflows/
└── image/
    └── meu-workflow/
        ├── comfyui.json    # workflow no formato API do ComfyUI
        └── manifest.yaml   # metadados do workflow
```

O `manifest.yaml` deve declarar `provider: comfyui`.

## Workflow identity

O workflow de validação de infraestrutura `image/identity`:
- **Função:** recebe uma imagem, passa pelo ComfyUI (LoadImage → SaveImage), retorna a mesma imagem
- **Propósito:** validar que ComfyUI está funcional sem depender de modelos
- **Path:** `workflows/image/identity/`

## Comunicação HTTP

| Operação | Endpoint | Método |
|----------|----------|--------|
| Submeter workflow | `/prompt` | POST |
| Consultar resultado | `/history/{prompt_id}` | GET |
| Status da fila | `/queue` | GET |
| Status do sistema | `/system_stats` | GET |
| Upload de imagem | `/upload/image` | POST |
| Download de imagem | `/view?filename=...` | GET |

## Configuração

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `COMFYUI_URL` | `http://127.0.0.1:8188` | URL base do ComfyUI |
| `COMFYUI_PORT` | `8188` | Porta |
| `COMFYUI_STARTUP_TIMEOUT` | `120` | Segundos para aguardar startup |
| `COMFYUI_PATH` | `/comfyui` | Dir de instalação |
