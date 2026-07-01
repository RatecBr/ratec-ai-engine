# RATEC AI ENGINE — Contrato Público da API

**Versão do documento:** 1.1.0  
**Data:** 2026-07-01  
**Status:** Estável

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [URL Base](#2-url-base)
3. [Versionamento](#3-versionamento)
4. [Autenticação](#4-autenticação)
5. [Headers Padrão](#5-headers-padrão)
6. [Rate Limiting](#6-rate-limiting)
7. [Idempotência](#7-idempotência)
8. [Formato de Erros](#8-formato-de-erros)
9. [Códigos HTTP](#9-códigos-http)
10. [Status dos Jobs](#10-status-dos-jobs)
11. [Endpoints](#11-endpoints)
    - [GET /v1/health](#get-v1health)
    - [GET /v1/workflows](#get-v1workflows)
    - [GET /v1/workflows/{id}](#get-v1workflowsid)
    - [GET /v1/capabilities](#get-v1capabilities)
    - [GET /v1/models](#get-v1models)
    - [GET /v1/models/{id}](#get-v1modelsid)
    - [POST /v1/jobs](#post-v1jobs)
    - [GET /v1/jobs](#get-v1jobs)
    - [GET /v1/jobs/{id}](#get-v1jobsid)
    - [POST /v1/jobs/{id}/cancel](#post-v1jobsidcancel)
    - [GET /v1/providers](#get-v1providers)
    - [GET /v1/providers/{id}](#get-v1providersid)
12. [Polling e Webhooks](#12-polling-e-webhooks)
13. [Changelog](#13-changelog)

---

## 1. Visão Geral

O **RATEC AI ENGINE** é a plataforma centralizada de Inteligência Artificial da RATEC.

Toda comunicação com o RATEC AI ENGINE ocorre **exclusivamente via REST API**. Nenhum aplicativo consumidor deve importar código interno, entidades ou bibliotecas do RATEC AI ENGINE. A API é o único contrato entre os projetos.

**Consumidores previstos:**

| Aplicativo | Status |
|---|---|
| GOODLOOK | Primeiro consumidor |
| Audiover | Planejado |
| Internice | Planejado |
| Animapages | Planejado |
| Karaokêro | Planejado |
| Terceiros | Via API pública |

---

## 2. URL Base

| Ambiente | URL |
|---|---|
| Produção (RunPod) | `https://api.runpod.ai/v2/{endpoint_id}/runsync` |
| API REST direta | `https://api.ratec.ai/v1` |
| Desenvolvimento local | `http://localhost:8000/v1` |

Todos os exemplos neste documento usam o prefixo `/v1`.

---

## 3. Versionamento

Todos os endpoints são prefixados com `/v1/`.

Versões futuras (`/v2/`, `/v3/`) serão adicionadas **sem remover versões anteriores**. Versões deprecated serão anunciadas com antecedência mínima de **90 dias** e sinalizadas no header de resposta:

```
Deprecation: Tue, 01 Jan 2027 00:00:00 GMT
Sunset: Wed, 01 Apr 2027 00:00:00 GMT
```

---

## 4. Autenticação

Toda requisição deve incluir a chave de API no header `Authorization`:

```
Authorization: Bearer {api_key}
```

- A chave é emitida por consumidor — uma chave por aplicativo
- Chaves são revogáveis imediatamente em caso de comprometimento
- Chave ausente ou inválida → `401 Unauthorized`
- Chave válida sem escopo suficiente → `403 Forbidden`

> **Nota de implementação:** A autenticação via Bearer token será implementada em fase posterior. Em ambiente de desenvolvimento, endpoints aceitam requisições sem autenticação.

---

## 5. Headers Padrão

### Requisição

| Header | Obrigatório | Descrição |
|---|---|---|
| `Authorization` | Sim | `Bearer {api_key}` |
| `Content-Type` | Sim (POST) | `application/json` |
| `Idempotency-Key` | Recomendado (POST /jobs) | UUID v4 para idempotência |
| `X-App-ID` | Recomendado | Identificador do aplicativo consumidor (ex: `goodlook`, `audiover`) |

### Resposta

| Header | Descrição |
|---|---|
| `Content-Type` | `application/json` |
| `X-Request-ID` | UUID único para rastreamento da requisição |
| `X-RateLimit-Limit` | Limite total de requisições na janela |
| `X-RateLimit-Remaining` | Requisições restantes na janela atual |
| `X-RateLimit-Reset` | Timestamp Unix de reset da janela |

---

## 6. Rate Limiting

Limites aplicados por `api_key`:

| Recurso | Limite |
|---|---|
| Requisições por minuto | 60 |
| Jobs simultâneos em execução | 10 |
| Jobs submetidos por hora | 500 |

Ao exceder o limite, o servidor retorna `429 Too Many Requests`:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Limite de requisições atingido. Aguarde antes de tentar novamente.",
    "details": {
      "retry_after_seconds": 30,
      "limit": 60,
      "window": "1m"
    }
  }
}
```

O header `Retry-After` indica em quantos segundos o cliente pode tentar novamente.

> **Nota de implementação:** Rate limiting será adicionado via middleware em fase posterior.

---

## 7. Idempotência

`POST /v1/jobs` suporta o header `Idempotency-Key`:

```
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

Se a mesma chave for enviada em múltiplas requisições, o servidor **retorna a resposta original sem criar um novo job**. Chaves são retidas por 24 horas.

A chave deve ser um UUID v4 gerado pelo cliente antes da requisição. O cliente é responsável por gerar uma chave nova para cada job distinto.

Todos os demais endpoints são idempotentes por natureza (GET retorna o mesmo recurso, cancelar um job já cancelado retorna 409).

---

## 8. Formato de Erros

**Todos** os endpoints retornam erros no mesmo envelope:

```json
{
  "error": {
    "code": "UPPER_SNAKE_CASE",
    "message": "Descrição legível por humanos.",
    "details": {}
  }
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `code` | string | Código de erro em `UPPER_SNAKE_CASE` |
| `message` | string | Mensagem para log ou exibição ao usuário |
| `details` | object | Informações adicionais específicas do erro (pode ser vazio) |

### Catálogo de códigos de erro

| Código | HTTP | Quando ocorre |
|---|---|---|
| `UNAUTHORIZED` | 401 | Chave de API ausente ou inválida |
| `FORBIDDEN` | 403 | Chave válida, mas sem permissão para o recurso |
| `WORKFLOW_NOT_FOUND` | 404 | Workflow não existe no registro |
| `JOB_NOT_FOUND` | 404 | Job não encontrado |
| `MODEL_NOT_FOUND` | 404 | Modelo não registrado |
| `CAPABILITY_NOT_FOUND` | 404 | Capability não registrada |
| `PROVIDER_NOT_FOUND` | 404 | Provider não registrado |
| `JOB_NOT_CANCELLABLE` | 409 | Job em estado terminal; cancelamento inválido |
| `VALIDATION_ERROR` | 422 | Payload inválido ou campo obrigatório ausente |
| `RATE_LIMIT_EXCEEDED` | 429 | Limite de requisições atingido |
| `INTERNAL_ERROR` | 500 | Erro interno inesperado |
| `SERVICE_UNAVAILABLE` | 503 | Serviço temporariamente indisponível |

---

## 9. Códigos HTTP

| Código | Significado | Uso |
|---|---|---|
| `200 OK` | Sucesso | GET, cancelamento bem-sucedido |
| `202 Accepted` | Aceito para processamento | POST /v1/jobs (assíncrono) |
| `400 Bad Request` | Requisição malformada | JSON inválido, header ausente |
| `401 Unauthorized` | Não autenticado | Chave ausente ou inválida |
| `403 Forbidden` | Não autorizado | Chave válida sem permissão |
| `404 Not Found` | Recurso não encontrado | Workflow, job, modelo inexistente |
| `409 Conflict` | Conflito de estado | Cancelar job já finalizado |
| `422 Unprocessable Entity` | Payload inválido | Campo obrigatório ausente ou tipo errado |
| `429 Too Many Requests` | Rate limit | Requisições em excesso |
| `500 Internal Server Error` | Erro interno | Falha inesperada no servidor |
| `503 Service Unavailable` | Serviço indisponível | Manutenção ou sobrecarga |

---

## 10. Status dos Jobs

| Status | Descrição |
|---|---|
| `queued` | Job aceito e aguardando worker disponível |
| `running` | Job em execução ativa |
| `completed` | Job concluído com sucesso; `output` disponível |
| `failed` | Job falhou; `error` contém a causa |
| `cancelled` | Job cancelado pelo cliente |
| `timeout` | Job excedeu o tempo máximo de execução |

**Estados terminais** (imutáveis): `completed`, `failed`, `cancelled`, `timeout`.

### Diagrama de transições

```
         ┌──────────┐
         │  queued  │
         └────┬─────┘
              │ worker disponível
              ▼
         ┌──────────┐
         │ running  │
         └────┬─────┘
     ┌────────┼────────┬──────────┐
     ▼        ▼        ▼          ▼
┌─────────┐ ┌──────┐ ┌──────────┐ ┌─────────┐
│completed│ │failed│ │cancelled │ │ timeout │
└─────────┘ └──────┘ └──────────┘ └─────────┘

queued → cancelled  (cancelamento antecipado)
```

---

## 11. Endpoints

---

### GET /v1/health

Verifica a saúde do serviço e de seus componentes.

**Autenticação:** Não requerida.

**Request:**
```http
GET /v1/health
```

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.1.0-alpha",
  "uptime_seconds": 3600,
  "availability": "online"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | string | `"ok"` ou `"degraded"` |
| `version` | string | Versão do engine |
| `uptime_seconds` | integer | Segundos desde o boot do worker |
| `availability` | string | `"online"` ou `"offline"` |

> **Nota (modo Serverless):** No RunPod Serverless cada invocação pode atingir um worker diferente. `uptime_seconds` reflete o tempo de vida da instância atual, não do endpoint.

---

### GET /v1/workflows

Lista todos os workflows disponíveis para execução.

**Request:**
```http
GET /v1/workflows
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "workflows": [
    {
      "id": "haircut",
      "name": "Haircut Simulation",
      "description": "Simulação de corte de cabelo com IA generativa",
      "version": "1.0.0",
      "capabilities": ["image-generation"],
      "estimated_time_seconds": 15,
      "input_schema": {
        "photo": { "type": "string", "format": "base64", "required": true },
        "style": { "type": "string", "required": true }
      },
      "output_schema": {
        "image": { "type": "string", "format": "base64" }
      }
    },
    {
      "id": "echo",
      "name": "Echo",
      "description": "Retorna a entrada como saída. Usado para testes de infraestrutura.",
      "version": "1.0.0",
      "capabilities": ["echo"],
      "estimated_time_seconds": 1,
      "input_schema": {},
      "output_schema": {}
    }
  ]
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string | Identificador único do workflow |
| `name` | string | Nome legível |
| `description` | string | O que o workflow faz |
| `version` | string | Versão semântica |
| `capabilities` | array[string] | Capabilities utilizadas |
| `estimated_time_seconds` | integer\|null | Tempo estimado de execução |
| `input_schema` | object | Schema JSON do input esperado |
| `output_schema` | object | Schema JSON do output retornado |

---

### GET /v1/workflows/{id}

Retorna os detalhes de um workflow específico.

**Request:**
```http
GET /v1/workflows/haircut
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "id": "haircut",
  "name": "Haircut Simulation",
  "description": "Simulação de corte de cabelo com IA generativa",
  "version": "1.0.0",
  "capabilities": ["image-generation"],
  "estimated_time_seconds": 15,
  "input_schema": {
    "photo": { "type": "string", "format": "base64", "required": true },
    "style": { "type": "string", "required": true }
  },
  "output_schema": {
    "image": { "type": "string", "format": "base64" }
  }
}
```

**Response 404:**
```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow 'haircut' não encontrado.",
    "details": {}
  }
}
```

---

### GET /v1/capabilities

Lista todas as capabilities disponíveis no sistema.

Uma **capability** representa uma operação de IA abstrata (`image-generation`, `text-generation`, `audio-transcription`). Workflows são compostos de capabilities; modelos implementam capabilities.

**Request:**
```http
GET /v1/capabilities
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "status": "ok",
  "capabilities": [
    "background-remove",
    "beard",
    "face-segmentation",
    "haircut",
    "identity",
    "image-identity",
    "image-upscale",
    "makeup",
    "virtual-try-on"
  ],
  "total": 9
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | string | `"ok"` |
| `capabilities` | array[string] | IDs das capabilities disponíveis, em ordem alfabética |
| `total` | integer | Total de capabilities registradas |

> **Nota:** As capabilities listadas correspondem às chaves do `_CAPABILITY_ROUTES` no `runtime/__init__.py`. Cada capability mapeia para um workflow ComfyUI específico no volume.

---

### GET /v1/models

Lista os modelos de IA registrados no sistema.

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `capability` | string | Não | Filtra modelos que suportam a capability |
| `status` | string | Não | Filtra por status (`available`, `unavailable`, `deprecated`) |

**Request:**
```http
GET /v1/models?capability=image-generation
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "models": [
    {
      "id": "flux-1-dev",
      "name": "FLUX.1 Dev",
      "provider": "runpod",
      "capabilities": ["image-generation"],
      "status": "available",
      "version": "1.0.0",
      "requirements": {
        "gpu": true,
        "min_vram": "16GB"
      }
    },
    {
      "id": "sdxl-1.0",
      "name": "Stable Diffusion XL 1.0",
      "provider": "runpod",
      "capabilities": ["image-generation"],
      "status": "available",
      "version": "1.0",
      "requirements": {
        "gpu": true,
        "min_vram": "8GB"
      }
    }
  ]
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string | Identificador único |
| `name` | string | Nome legível |
| `provider` | string | Provider que executa o modelo |
| `capabilities` | array[string] | Capabilities suportadas |
| `status` | string | `available`, `unavailable`, `deprecated` |
| `version` | string | Versão do modelo |
| `requirements` | object | Requisitos de hardware |

---

### GET /v1/models/{id}

Retorna detalhes de um modelo específico.

**Request:**
```http
GET /v1/models/flux-1-dev
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "id": "flux-1-dev",
  "name": "FLUX.1 Dev",
  "provider": "runpod",
  "capabilities": ["image-generation"],
  "status": "available",
  "version": "1.0.0",
  "requirements": {
    "gpu": true,
    "min_vram": "16GB"
  }
}
```

**Response 404:**
```json
{
  "error": {
    "code": "MODEL_NOT_FOUND",
    "message": "Modelo 'flux-1-dev' não encontrado.",
    "details": {}
  }
}
```

---

### POST /v1/jobs

Cria e enfileira um novo job de processamento de IA.

Operação **síncrona no modo Serverless**: no RunPod Serverless a chamada `runsync` bloqueia até o job completar. O resultado é retornado diretamente com `status: "completed"`. Não é necessário polling — `output` já estará populado na resposta.

> **Nota de compatibilidade:** A interface mantém os campos `id`, `status` e `progress` para compatibilidade com o Console Web, mas o fluxo assíncrono real (polling) não se aplica ao modo Serverless.

**Request:**
```http
POST /v1/jobs
Authorization: Bearer {api_key}
Content-Type: application/json
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

```json
{
  "workflow_id": "haircut",
  "input": {
    "photo": "<base64_da_imagem>",
    "style": "undercut"
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `workflow_id` | string | Sim | ID do workflow a executar |
| `input` | object | Não | Dados de entrada (schema definido pelo workflow) |

**Response 202:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "haircut",
  "status": "queued",
  "progress": 0,
  "input": {
    "photo": "<base64>",
    "style": "undercut"
  },
  "output": null,
  "error": null,
  "created_at": "2026-06-29T18:00:00Z",
  "updated_at": "2026-06-29T18:00:00Z",
  "completed_at": null
}
```

**Response 404 — workflow não existe:**
```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow 'haircut' não encontrado.",
    "details": {}
  }
}
```

**Response 422 — payload inválido:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Campo obrigatório ausente: workflow_id.",
    "details": {
      "field": "workflow_id"
    }
  }
}
```

---

### GET /v1/jobs

Lista jobs com filtros e paginação.

**Query Parameters:**

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `status` | string | null | Filtra por status do job |
| `workflow_id` | string | null | Filtra por workflow |
| `limit` | integer | 50 | Máximo de itens por página (1–200) |
| `offset` | integer | 0 | Deslocamento para paginação |

**Request:**
```http
GET /v1/jobs?status=completed&workflow_id=haircut&limit=20&offset=0
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "workflow_id": "haircut",
      "status": "completed",
      "progress": 100,
      "input": { "style": "undercut" },
      "output": { "image": "<base64>" },
      "error": null,
      "created_at": "2026-06-29T18:00:00Z",
      "updated_at": "2026-06-29T18:00:15Z",
      "completed_at": "2026-06-29T18:00:15Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### GET /v1/jobs/{id}

Retorna o estado atual de um job específico.

**Request:**
```http
GET /v1/jobs/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {api_key}
```

**Response 200 — queued:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "haircut",
  "status": "queued",
  "progress": 0,
  "input": { "photo": "<base64>", "style": "undercut" },
  "output": null,
  "error": null,
  "created_at": "2026-06-29T18:00:00Z",
  "updated_at": "2026-06-29T18:00:00Z",
  "completed_at": null
}
```

**Response 200 — running:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "haircut",
  "status": "running",
  "progress": 45,
  "input": { "photo": "<base64>", "style": "undercut" },
  "output": null,
  "error": null,
  "created_at": "2026-06-29T18:00:00Z",
  "updated_at": "2026-06-29T18:00:05Z",
  "completed_at": null
}
```

**Response 200 — completed:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "haircut",
  "status": "completed",
  "progress": 100,
  "input": { "photo": "<base64>", "style": "undercut" },
  "output": {
    "image": "<base64_da_imagem_resultante>"
  },
  "error": null,
  "created_at": "2026-06-29T18:00:00Z",
  "updated_at": "2026-06-29T18:00:15Z",
  "completed_at": "2026-06-29T18:00:15Z"
}
```

**Response 200 — failed:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "haircut",
  "status": "failed",
  "progress": 30,
  "input": { "photo": "<base64>", "style": "undercut" },
  "output": null,
  "error": "Modelo indisponível no provider.",
  "created_at": "2026-06-29T18:00:00Z",
  "updated_at": "2026-06-29T18:00:08Z",
  "completed_at": "2026-06-29T18:00:08Z"
}
```

**Response 200 — timeout:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "haircut",
  "status": "timeout",
  "progress": 60,
  "input": { "photo": "<base64>", "style": "undercut" },
  "output": null,
  "error": "Job excedeu o tempo máximo de execução de 300 segundos.",
  "created_at": "2026-06-29T18:00:00Z",
  "updated_at": "2026-06-29T18:05:00Z",
  "completed_at": "2026-06-29T18:05:00Z"
}
```

**Campos da resposta:**

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string (UUID) | Identificador único do job |
| `workflow_id` | string | Workflow executado |
| `status` | string | Status atual (ver seção 10) |
| `progress` | integer | Progresso de 0 a 100 |
| `input` | object | Input fornecido na criação |
| `output` | object\|null | Resultado quando `completed` |
| `error` | string\|null | Causa do erro quando `failed` ou `timeout` |
| `created_at` | string (ISO 8601 UTC) | Momento de criação |
| `updated_at` | string (ISO 8601 UTC) | Última atualização de estado |
| `completed_at` | string\|null (ISO 8601 UTC) | Momento de conclusão (estados terminais) |

**Response 404:**
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job '550e8400-e29b-41d4-a716-446655440000' não encontrado.",
    "details": {}
  }
}
```

---

### POST /v1/jobs/{id}/cancel

Cancela um job que ainda não completou.

Apenas jobs nos estados `queued` ou `running` podem ser cancelados. Jobs em estado terminal retornam `409 Conflict`.

**Request:**
```http
POST /v1/jobs/550e8400-e29b-41d4-a716-446655440000/cancel
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "haircut",
  "status": "cancelled",
  "progress": 30,
  "input": { "style": "undercut" },
  "output": null,
  "error": null,
  "created_at": "2026-06-29T18:00:00Z",
  "updated_at": "2026-06-29T18:00:10Z",
  "completed_at": "2026-06-29T18:00:10Z"
}
```

**Response 409 — job em estado terminal:**
```json
{
  "error": {
    "code": "JOB_NOT_CANCELLABLE",
    "message": "Job '550e8400-...' está em estado 'completed' e não pode ser cancelado.",
    "details": {
      "current_status": "completed"
    }
  }
}
```

**Response 404:**
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job '550e8400-...' não encontrado.",
    "details": {}
  }
}
```

---

### GET /v1/providers

Lista todos os providers de execução registrados.

**Request:**
```http
GET /v1/providers
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "providers": [
    {
      "id": "runpod",
      "name": "RunPod Serverless",
      "type": "runpod",
      "status": "active",
      "capabilities": ["image-generation", "text-generation", "audio-transcription"]
    },
    {
      "id": "local",
      "name": "Local Backend",
      "type": "local",
      "status": "active",
      "capabilities": ["echo"]
    }
  ]
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string | Identificador único |
| `name` | string | Nome legível |
| `type` | string | `runpod`, `comfyui`, `openai`, `local` |
| `status` | string | `active`, `inactive`, `degraded` |
| `capabilities` | array[string] | Capabilities que este provider suporta |

---

### GET /v1/providers/{id}

Retorna detalhes de um provider específico.

**Request:**
```http
GET /v1/providers/runpod
Authorization: Bearer {api_key}
```

**Response 200:**
```json
{
  "id": "runpod",
  "name": "RunPod Serverless",
  "type": "runpod",
  "status": "active",
  "capabilities": ["image-generation", "text-generation", "audio-transcription"]
}
```

**Response 404:**
```json
{
  "error": {
    "code": "PROVIDER_NOT_FOUND",
    "message": "Provider 'runpod' não encontrado.",
    "details": {}
  }
}
```

---

## 12. Polling e Webhooks

### Polling (implementado)

O cliente consulta `GET /v1/jobs/{id}` periodicamente até atingir um estado terminal.

**Estratégia recomendada — backoff exponencial:**

```
t=0s   POST /v1/jobs          → 202, status: queued
t=2s   GET  /v1/jobs/{id}     → status: queued
t=4s   GET  /v1/jobs/{id}     → status: running
t=8s   GET  /v1/jobs/{id}     → status: running
t=16s  GET  /v1/jobs/{id}     → status: completed  ✓
```

Intervalo inicial: **2 segundos**. Dobrar a cada consulta sem mudança de estado. Limite máximo: **30 segundos**.

### Webhook (planejado — v1.1)

O cliente registra uma URL de callback ao criar o job. O RATEC AI ENGINE fará um `POST` nessa URL quando o job atingir um estado terminal.

**Request de criação com webhook:**
```json
{
  "workflow_id": "haircut",
  "input": { "photo": "<base64>", "style": "undercut" },
  "webhook_url": "https://app.goodlook.com.br/webhooks/ratec"
}
```

**Payload enviado ao webhook:**
```json
{
  "event": "job.completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "timestamp": "2026-06-29T18:00:15Z"
}
```

O cliente deve responder com `200 OK` em até 5 segundos. O RATEC AI ENGINE tentará reenviar até 3 vezes com backoff exponencial em caso de falha.

---

## 13. Implementação — Status por Endpoint

Referência rápida do estado atual da implementação no handler serverless (`handler.py`):

| Endpoint | Implementado | Observações |
|---|---|---|
| GET /v1/health | ✅ | Retorna status, versão, uptime |
| GET /v1/capabilities | ✅ | Lista de 9 capabilities do `_CAPABILITY_ROUTES` |
| GET /v1/workflows | ✅ | Workflows disponíveis via `WorkflowManager` |
| GET /v1/models | ✅ | Modelos ativos do `active_models.json` |
| GET /v1/workflows/{id} | 🔲 | Rota única não implementada |
| GET /v1/models/{id} | 🔲 | Rota única não implementada |
| POST /v1/jobs | ✅ | Execução síncrona via `_runtime.handle()` |
| GET /v1/jobs | ✅ | Retorna lista vazia (sem tracking serverless) |
| GET /v1/jobs/{id} | ⚠️ | Retorna `not_found` — sem persistência entre invocações |
| POST /v1/jobs/{id}/cancel | 🔲 | Não aplicável no modo serverless |
| GET /v1/providers | 🔲 | Fase posterior |
| GET /v1/providers/{id} | 🔲 | Fase posterior |
| Autenticação Bearer | 🔲 | Fase posterior |
| Rate limiting | 🔲 | Fase posterior |
| Idempotency-Key | 🔲 | Fase posterior |
| Webhooks | 🔲 | v1.1 |

---

## 14. Changelog

| Versão | Data | Descrição |
|---|---|---|
| 1.1.0 | 2026-07-01 | Rotas /v1/* implementadas no handler serverless; response de /v1/health e /v1/capabilities atualizados; nota sobre execução síncrona em serverless |
| 1.0.0 | 2026-06-29 | Contrato público inicial |
