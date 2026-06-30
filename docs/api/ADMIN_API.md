# RATEC AI ENGINE — Contrato da API Administrativa

**Versão do documento:** 1.0.0  
**Data:** 2026-06-30  
**Status:** Uso Exclusivo Interno

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Padrão de Resposta](#2-padrão-de-resposta)
3. [Autenticação](#3-autenticação)
4. [Endpoints Administrativos](#4-endpoints-administrativos)
    - [GET /admin/health](#get-adminhealth)
    - [GET /admin/runtime](#get-adminruntime)
    - [GET /admin/system](#get-adminsystem)
    - [GET /admin/gpu](#get-admingpu)
    - [GET /admin/storage](#get-adminstorage)
    - [GET /admin/logs](#get-adminlogs)
    - [GET /admin/metrics](#get-adminmetrics)
    - [GET /admin/models](#get-adminmodels)
    - [GET /admin/workflows](#get-adminworkflows)

---

## 1. Visão Geral

A API Administrativa (prefixo `/admin/`) é destinada **exclusivamente** ao Console Web do RATEC AI ENGINE. Ela fornece métricas detalhadas, configurações internas, leituras de hardware local (GPU/Disco) e observabilidade profunda.

**Aviso Importante:**
Aplicativos consumidores (GoodLook, Audiover, etc.) **NUNCA** devem utilizar os endpoints `/admin/`. Para consumidores de negócios, utilize exclusivamente os endpoints definidos no `API_CONTRACT.md` (`/v1/...`).

---

## 2. Padrão de Resposta

Todos os endpoints `/admin/` encapsulam a resposta em um "envelope" padrão para facilitar a decodificação no Frontend.

### Sucesso (200 OK)
```json
{
  "success": true,
  "timestamp": "2026-06-30T16:00:00Z",
  "data": {
    "exemplo_chave": "valor"
  }
}
```

### Erro (400, 401, 403, 500)
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE_UPPERCASE",
    "message": "Descrição amigável do erro."
  }
}
```

---

## 3. Autenticação

Todos os endpoints declaram uma dependência de autenticação (`Depends(verify_admin_token)`).
Inicialmente, o sistema operará de forma flexível ou usando proteção em nível de Proxy/Frontend, mas os roteadores já possuem os "hooks" de middleware necessários para validação de JWT estrita nas próximas versões.

---

## 4. Endpoints Administrativos

### GET /admin/health
Estado geral da plataforma e disponibilidade de módulos.
* `data.status`: "ok" ou "degraded"
* `data.uptime_seconds`: Tempo de atividade do motor
* `data.version`: Versão do RATEC AI ENGINE

### GET /admin/runtime
Configurações de ambiente, bootstrap e estado interno da Engine e do ComfyUI.
* `data.is_serverless`: Boleano indicando se roda via RunPod Serverless
* `data.volume_path`: Diretório raiz do sistema
* `data.comfyui_status`: Status de conexão com o ComfyUI Manager

### GET /admin/system
Métricas e atributos do SO, carga de CPU global e uso de memória RAM.

### GET /admin/gpu
Telemetria exclusiva da placa de vídeo e alocação de VRAM.
* `data.name`: Ex: "NVIDIA A40"
* `data.vram_total_mb`: Memória total
* `data.vram_used_mb`: Memória atualmente alocada

### GET /admin/storage
Volumes de disco, espaços livres, diretórios de cache e outputs gerados localmente.

### GET /admin/logs
Leitura estruturada ou streaming de logs nativos da plataforma, abrangendo stdout, stderr e registros do ComfyUI subjacente.

### GET /admin/metrics
Performance de execução, throughput, quantidade de requisições concluídas por hora e benchmarks de aquecimento.

### GET /admin/models
Painel interno de modelos carregados na VRAM localmente, permitindo inspeção de pesos pesados.

### GET /admin/workflows
Listagem de workflows locais com todos os metadados de desenvolvedor, sem ocultar schemas e paths físicos.
