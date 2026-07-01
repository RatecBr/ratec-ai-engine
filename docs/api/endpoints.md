# API Reference — RATEC AI ENGINE

> **Arquitetura atual:** RunPod Serverless. Todas as requisições chegam via proxy Vercel (`engine.ra.tec.br`) e são encapsuladas em chamadas `runsync` para o handler. Não há servidor HTTP local — o roteamento é feito dentro do `handler.py`.

---

## Transporte

```
Console Web → Vercel BFF (/api/[...path]) → RunPod runsync → handler.py → resposta
```

O campo `http_path` no payload do RunPod determina qual rota é servida.

---

## Rotas Públicas `/v1/*`

Consumidas pelo Console Web e (futuramente) pelos aplicativos RATEC.  
Retornam dados diretos — **sem** o envelope `{success, data}`.

### `GET /v1/health`
```json
{ "status": "ok", "version": "1.1.0-alpha", "uptime_seconds": 3600, "availability": "online" }
```

### `GET /v1/capabilities`
```json
{ "status": "ok", "capabilities": ["background-remove", "beard", "face-segmentation", "haircut", "identity", "image-identity", "image-upscale", "makeup", "virtual-try-on"], "total": 9 }
```

### `GET /v1/workflows`
```json
{
  "status": "ok",
  "workflows": [
    { "id": "image/background-remove", "name": "Background Remove", "version": "1.0", "description": "Workflow de IA: image/background-remove" },
    { "id": "image/identity",          "name": "Identity",          "version": "1.0", "description": "Workflow de IA: image/identity" },
    { "id": "image/image-upscale",     "name": "Image Upscale",     "version": "1.0", "description": "Workflow de IA: image/image-upscale" }
  ],
  "total": 3
}
```

### `GET /v1/models`
```json
{ "status": "ok", "models": [{ "id": "sdxl_base.safetensors", "name": "sdxl_base.safetensors", "workflow": "image/identity", "status": "available" }], "total": 1 }
```

### `GET /v1/jobs` (GET)
```json
{ "status": "ok", "jobs": [], "total": 0 }
```
> Sem tracking de jobs no modo serverless — cada `runsync` é autocontido.

### `POST /v1/jobs`
```json
// Request body
{ "workflow_id": "background-remove", "input": { "image": "<base64>" } }

// Response (síncrono — resultado imediato)
{ "id": "a1b2c3d4", "status": "completed", "workflow_id": "background-remove", "progress": 100, "output": { ... } }
```

### `GET /v1/jobs/{id}`
```json
{ "id": "{id}", "status": "not_found", "error": "Rastreamento de jobs não disponível no modo serverless." }
```

---

## Rotas Administrativas `/admin/*`

Exclusivas do Console Web (`engine.ra.tec.br`).  
Retornam o envelope `{ "success": true, "data": { ... } }`.

| Rota | Descrição |
|---|---|
| `GET /admin/version` | Metadados de build: versão, commit, branch, docker tag, GPU, boot time |
| `GET /admin/health` | Saúde da plataforma e uptime |
| `GET /admin/gpu` | Telemetria da GPU: nome, VRAM total/usada/livre, modelos ativos |
| `GET /admin/system` | Estado consolidado: GPU + runtime + storage + ComfyUI status |
| `GET /admin/runtime` | Configuração do runtime: modo serverless, volume path, capabilities carregadas |
| `GET /admin/storage` | Volumes de disco, espaço livre, breakdown models vs cache |
| `GET /admin/logs` | Logs estruturados do stdout do worker |
| `GET /admin/metrics` | Métricas de throughput e execução |
| `GET /admin/models` | Modelos instalados no volume |
| `GET /admin/workflows` | Workflows registrados com metadados de desenvolvedor |
