# API Reference — RATEC AI ENGINE v1

Base URL: `http://host:8000/v1`  
Documentação interativa: `http://host:8000/docs`

---

## Health

### `GET /v1/health`
Status da plataforma e de cada provider e backend.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "providers": { "local": "ok", "runpod": "ok" },
  "backends":  { "local": "ok", "runpod": "ok" }
}
```

---

## Jobs

### `POST /v1/jobs`
Submete um job para execução assíncrona.

**Body:**
```json
{ "workflow_id": "echo", "input": { "key": "value" } }
```

**Response 202:**
```json
{
  "id": "uuid",
  "workflow_id": "echo",
  "status": "completed",
  "output": { ... },
  "created_at": "2026-01-01T00:00:00Z"
}
```

### `GET /v1/jobs`
Lista jobs com filtros opcionais: `?status=pending&workflow_id=echo&limit=50&offset=0`

### `GET /v1/jobs/{job_id}`
Busca um job pelo ID.

### `POST /v1/jobs/{job_id}/cancel`
Cancela um job pendente ou em execução.

---

## Workflows

### `GET /v1/workflows`
Lista todos os workflows registrados.

### `GET /v1/workflows/{workflow_id}`
Detalha um workflow específico incluindo seus steps e o pipeline_id referenciado.

---

## Pipelines

### `GET /v1/pipelines`
Lista todos os pipelines registrados.

### `GET /v1/pipelines/{pipeline_id}`
Detalha um pipeline incluindo capability, action, model_id e execution_strategy de cada step.

---

## Models

### `GET /v1/models`
Lista todos os modelos registrados. Filtro opcional: `?capability=image-generation`

### `GET /v1/models/{model_id}`
Detalha um modelo: capabilities, requirements, status.

---

## Providers

### `GET /v1/providers`
Lista providers registrados no catálogo de capabilities.

### `GET /v1/providers/{provider_id}`
Detalha um provider.
