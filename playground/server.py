"""
RATEC AI Engine — Control Panel
================================
Interface web oficial para desenvolvimento, validação e administração da plataforma.

Abas:
  Dashboard — status completo em tempo real (ComfyUI, GPU, Volume, modelos)
  Execute   — executa qualquer capability com imagem e parâmetros
  History   — histórico completo de execuções com imagens e métricas
  Compare   — comparação lado a lado de duas execuções
  Benchmark — métricas agregadas por capability e workflow
  Logs      — visualização de logs do sistema (ComfyUI, instalação de modelos)
  Catalog   — catálogo de modelos e capabilities

Uso:
    pip install -r playground/requirements.txt
    uvicorn playground.server:app --port 7860 --reload

Variáveis de ambiente:
    COMFYUI_URL         URL do ComfyUI (default: http://127.0.0.1:8188)
    RUNPOD_VOLUME_PATH  Caminho do Network Volume (default: /runpod-volume)
    LAB_DATA_PATH       Diretório dos dados do Lab (default: ./lab_data)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
load_dotenv()

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from runtime import Runtime, _BOOT_TIME, _CAPABILITY_ROUTES
from runtime.health import full_health
from runtime.lab import Lab
from playground.catalog import list_capability_models, list_models

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RATEC AI Engine — Control Panel", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite o Vercel fazer requisições para a máquina local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Inicialização ─────────────────────────────────────────────────────────────

_runtime: Runtime | None = None
_lab: Lab | None = None
_lab_dir = Path(os.environ.get("LAB_DATA_PATH", "./lab_data"))

_LOG_ALLOWLIST = {"comfyui.log", "install_models.log"}


@app.on_event("startup")
async def startup():
    global _runtime, _lab, _remote_mode, _runpod_key, _runpod_endpoint
    _runpod_key = os.environ.get("RUNPOD_API_KEY")
    _runpod_endpoint = os.environ.get("RUNPOD_ENDPOINT_ID")
    _remote_mode = bool(_runpod_key and _runpod_endpoint)

    if not _remote_mode:
        _runtime = Runtime.initialize()
    else:
        print(f"[playground] Modo NUVEM ativado. Conectando ao RunPod: {_runpod_endpoint}", flush=True)

    _lab = Lab(_lab_dir)
    images_dir = _lab_dir / "images"
    (images_dir / "input").mkdir(parents=True, exist_ok=True)
    (images_dir / "output").mkdir(parents=True, exist_ok=True)
    app.mount("/lab/images", StaticFiles(directory=str(images_dir)), name="lab_images")
    print(f"[playground] AI Lab iniciado -> {_lab_dir.resolve()}", flush=True)

import httpx

async def _remote_runsync(workflow_id: str, input_data: dict = {}, timeout_s: float = 300.0) -> dict:
    if _runpod_endpoint.startswith("pod:"):
        pod_id = _runpod_endpoint.split("pod:")[1]
        url = f"https://{pod_id}-8000.proxy.runpod.net/runsync"
    else:
        url = f"https://api.runpod.ai/v2/{_runpod_endpoint}/runsync"
        
    headers = {
        "Authorization": f"Bearer {_runpod_key}",
        "Content-Type": "application/json"
    }
    payload = {"input": {"workflow_id": workflow_id, "input": input_data}}
    
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "COMPLETED":
            return data.get("output", {})
        raise RuntimeError(f"RunPod pendente/falhou: {data}")



def _rt() -> Runtime:
    assert _runtime is not None
    return _runtime


def _lb() -> Lab:
    assert _lab is not None
    return _lab


# ── HTML ─────────────────────────────────────────────────────────────────────

_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RATEC AI Engine</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0a0a0a;color:#d4d4d4;min-height:100vh}
a{color:#60a5fa;text-decoration:none}

/* Header */
header{background:#111;border-bottom:1px solid #222;padding:10px 20px;display:flex;align-items:center;gap:12px}
header h1{font-size:15px;font-weight:700;color:#fff;letter-spacing:-.3px}
header .version{font-size:11px;color:#555;padding:2px 6px;background:#1a1a1a;border-radius:3px}
header .env-badge{font-size:11px;padding:2px 8px;border-radius:3px;font-weight:600}
header .env-production{background:#052e16;color:#4ade80}
header .env-development{background:#1c1500;color:#fbbf24}
#hdr-refresh{margin-left:auto;font-size:11px;color:#444;cursor:pointer;padding:4px 10px;background:#161616;border:1px solid #222;border-radius:4px}
#hdr-refresh:hover{color:#888}
#hdr-online{width:8px;height:8px;border-radius:50%;background:#555;margin-right:4px;display:inline-block}
#hdr-online.ok{background:#4ade80;box-shadow:0 0 6px #4ade8066}
#hdr-online.warn{background:#fbbf24}
#hdr-online.fail{background:#f87171}

/* Nav */
nav{background:#111;border-bottom:1px solid #1f1f1f;padding:0 20px;display:flex;gap:2px;overflow-x:auto}
nav button{background:none;border:none;color:#666;padding:10px 14px;font-size:13px;cursor:pointer;border-bottom:2px solid transparent;transition:color .15s;white-space:nowrap}
nav button:hover{color:#aaa}
nav button.active{color:#fff;border-bottom-color:#4ade80}

/* Layout */
.container{max-width:1400px;margin:0 auto;padding:20px}
.tab{display:none}.tab.active{display:block}

/* Panels */
.panel{background:#111;border:1px solid #1f1f1f;border-radius:8px;padding:18px;margin-bottom:16px}
.panel-title{font-size:11px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:.8px;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid-3{display:grid;grid-template-columns:320px 1fr 1fr;gap:16px}
.grid-sidebar{display:grid;grid-template-columns:300px 1fr;gap:16px}

/* Dashboard status cards */
.dash-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
@media(max-width:900px){.dash-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:500px){.dash-grid{grid-template-columns:1fr}}
.status-card{background:#111;border:1px solid #1f1f1f;border-radius:8px;padding:16px;position:relative;overflow:hidden}
.status-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.status-card.ok::before{background:#22c55e}
.status-card.warn::before{background:#f59e0b}
.status-card.fail::before{background:#ef4444}
.status-card.loading::before{background:#3b82f6;animation:pulse .8s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}
.sc-label{font-size:10px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px}
.sc-value{font-size:18px;font-weight:700;color:#d4d4d4;line-height:1.2}
.sc-sub{font-size:11px;color:#555;margin-top:4px}
.sc-icon{font-size:22px;position:absolute;right:14px;top:14px;opacity:.2}

/* VRAM bar */
.vram-bar-wrap{margin-top:8px}
.vram-bar-bg{background:#1a1a1a;border-radius:3px;height:5px;overflow:hidden}
.vram-bar-fill{height:5px;border-radius:3px;background:#4ade80;transition:width .5s}
.vram-bar-fill.mid{background:#f59e0b}
.vram-bar-fill.high{background:#ef4444}
.vram-bar-label{font-size:10px;color:#555;margin-top:3px}

/* Dash sections */
.dash-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:700px){.dash-row{grid-template-columns:1fr}}
.model-row{display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid #161616}
.model-row:last-child{border:0}
.model-name{font-size:13px;color:#d4d4d4}
.model-id{font-size:11px;color:#4ade80;font-family:monospace}
.cap-pill{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;background:#0d1a0d;border:1px solid #1a3a1a;border-radius:20px;font-size:12px;color:#4ade80;margin:3px}
.cap-pill.sys{background:#0a1a2a;border-color:#1a3050;color:#60a5fa}
.cap-pill.plan{background:#1a1a0a;border-color:#3a3010;color:#fbbf24}
.quick-actions{display:flex;gap:10px;flex-wrap:wrap}

/* Quick action result */
.action-result{margin-top:12px;background:#0d0d0d;border:1px solid #1f1f1f;border-radius:6px;padding:12px;font-family:monospace;font-size:11px;color:#888;overflow:auto;max-height:200px;white-space:pre;display:none}

/* Refresh bar */
.refresh-bar{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.refresh-bar .countdown{font-size:11px;color:#444}
.refresh-bar button{font-size:11px;padding:4px 10px;background:#161616;border:1px solid #222;border-radius:4px;color:#666;cursor:pointer}
.refresh-bar button:hover{color:#aaa}
.last-updated{font-size:11px;color:#444;margin-left:auto}

/* Form */
label{display:block;font-size:12px;color:#777;margin:12px 0 5px}
label:first-child{margin-top:0}
select,input[type=text],input[type=number],textarea{width:100%;padding:8px 10px;background:#0d0d0d;border:1px solid #2a2a2a;border-radius:5px;color:#d4d4d4;font-size:13px;outline:none}
select:focus,input:focus,textarea:focus{border-color:#404040}
textarea{resize:vertical;font-family:monospace;font-size:12px}

/* Upload */
.drop{border:2px dashed #222;border-radius:6px;padding:24px;text-align:center;cursor:pointer;transition:border-color .15s;position:relative}
.drop:hover,.drop.drag{border-color:#444}
.drop input{display:none}
.drop-text{font-size:12px;color:#555}
.drop img{max-width:100%;max-height:180px;border-radius:4px;margin-top:8px;object-fit:contain}

/* Buttons */
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;transition:background .15s}
.btn-primary{background:#166534;color:#4ade80}.btn-primary:hover{background:#15803d}
.btn-primary:disabled{background:#1a2e1a;color:#3d5c3d;cursor:not-allowed}
.btn-sm{padding:5px 10px;font-size:12px}
.btn-ghost{background:#1a1a1a;color:#aaa;border:1px solid #2a2a2a}.btn-ghost:hover{background:#222}
.btn-danger{background:#2a0a0a;color:#f87171;border:1px solid #3a1a1a}.btn-danger:hover{background:#3a1010}
.btn-full{width:100%;justify-content:center;margin-top:12px}
.btn-blue{background:#0c1a3a;color:#60a5fa;border:1px solid #1a3060}.btn-blue:hover{background:#0d2050}

/* Status */
.status{font-size:12px;color:#666;min-height:18px;margin-top:8px}
.badge{padding:2px 7px;border-radius:3px;font-size:11px;font-weight:600}
.badge-green{background:#052e16;color:#4ade80}
.badge-red{background:#2a0a0a;color:#f87171}
.badge-blue{background:#0c1a3a;color:#60a5fa}
.badge-yellow{background:#1c1500;color:#fbbf24}
.badge-gray{background:#1a1a1a;color:#777}

/* Results */
.result-img{max-width:100%;border-radius:6px;display:block}
.timing{display:flex;gap:12px;margin-top:10px;flex-wrap:wrap}
.timing span{font-size:12px;color:#555}
.timing strong{color:#888}
.error-box{background:#1a0808;border:1px solid #3a1a1a;border-radius:6px;padding:12px;color:#f87171;font-size:13px;margin-top:10px}
.json-box{background:#0d0d0d;border:1px solid #1f1f1f;border-radius:6px;padding:12px;font-family:monospace;font-size:11px;color:#888;overflow:auto;max-height:220px;white-space:pre;margin-top:10px}
.placeholder{color:#333;font-size:13px;text-align:center;padding:48px 20px}

/* History table */
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:8px 12px;font-size:11px;font-weight:600;color:#555;border-bottom:1px solid #1f1f1f;text-transform:uppercase;letter-spacing:.5px}
td{padding:9px 12px;border-bottom:1px solid #161616;vertical-align:middle}
tr:hover td{background:#111}
tr.selected td{background:#0d1a0d}
.thumb{width:40px;height:40px;object-fit:cover;border-radius:3px;cursor:pointer}
.score-stars{color:#fbbf24;font-size:14px}

/* Evaluation form */
.eval-form{background:#0d0d0d;border:1px solid #1f1f1f;border-radius:6px;padding:16px;margin-top:12px}
.eval-form h4{font-size:12px;color:#555;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px}
.stars-input{display:flex;gap:4px;margin-bottom:10px}
.stars-input span{font-size:22px;cursor:pointer;color:#333;transition:color .1s}
.stars-input span.on{color:#fbbf24}

/* Benchmark */
.metric-card{background:#0d0d0d;border:1px solid #1f1f1f;border-radius:6px;padding:14px}
.metric-label{font-size:11px;color:#555;margin-bottom:4px}
.metric-value{font-size:22px;font-weight:700;color:#d4d4d4}
.metric-sub{font-size:11px;color:#555;margin-top:2px}
.metrics-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:16px}

/* Catalog */
.model-card{background:#0d0d0d;border:1px solid #1f1f1f;border-radius:6px;padding:14px;margin-bottom:10px}
.model-card h3{font-size:14px;color:#d4d4d4;margin-bottom:4px}
.model-card p{font-size:12px;color:#666;margin-bottom:8px;line-height:1.5}
.model-meta{display:flex;gap:8px;flex-wrap:wrap}

/* Compare */
.compare-col{display:flex;flex-direction:column;gap:12px}
.compare-img-wrap{background:#0d0d0d;border:1px solid #1f1f1f;border-radius:6px;padding:8px;min-height:200px;display:flex;align-items:center;justify-content:center}
.compare-img-wrap img{max-width:100%;max-height:360px;border-radius:4px}

/* Logs */
.log-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.log-controls select{width:auto;min-width:160px}
.log-viewer{background:#060606;border:1px solid #1a1a1a;border-radius:6px;padding:14px;font-family:'Courier New',monospace;font-size:11px;color:#5a8f5a;overflow:auto;height:520px;white-space:pre-wrap;word-break:break-all;line-height:1.6}
.log-viewer .log-err{color:#f87171}
.log-viewer .log-warn{color:#fbbf24}
.log-meta{font-size:11px;color:#444;margin-top:8px}
.log-empty{color:#333;font-size:13px;text-align:center;padding:80px 0}
.auto-badge{font-size:10px;padding:2px 6px;border-radius:3px;font-weight:700;background:#052e16;color:#4ade80}
.auto-badge.off{background:#1a1a1a;color:#555}

/* Scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:#0d0d0d}
::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:3px}
</style>
</head>
<body>
<header>
  <h1>⚗ RATEC AI Engine</h1>
  <span class="version" id="hdr-version">v2.0</span>
  <span id="hdr-env" class="env-badge env-development" style="display:none"></span>
  <span style="margin-left:8px;font-size:12px;color:#555" id="hdr-hostname"></span>
  <span id="hdr-refresh" onclick="refreshDashboard()" title="Atualizar status">
    <span id="hdr-online"></span>atualizar
  </span>
</header>
<nav>
  <button onclick="showTab('dashboard')" id="tab-btn-dashboard" class="active">🖥 Dashboard</button>
  <button onclick="showTab('execute')" id="tab-btn-execute">▶ Execute</button>
  <button onclick="showTab('history')" id="tab-btn-history">📋 History</button>
  <button onclick="showTab('compare')" id="tab-btn-compare">⚖ Compare</button>
  <button onclick="showTab('benchmark')" id="tab-btn-benchmark">📊 Benchmark</button>
  <button onclick="showTab('logs')" id="tab-btn-logs">📄 Logs</button>
  <button onclick="showTab('catalog')" id="tab-btn-catalog">🗂 Catalog</button>
</nav>

<!-- ═══════════════ TAB: DASHBOARD ═══════════════ -->
<div id="tab-dashboard" class="tab active">
<div class="container">

  <!-- Refresh bar -->
  <div class="refresh-bar">
    <button onclick="refreshDashboard()">🔄 Atualizar agora</button>
    <span class="countdown" id="dash-countdown"></span>
    <span class="last-updated" id="dash-updated"></span>
  </div>

  <!-- Status cards row -->
  <div class="dash-grid" id="dash-cards">
    <div class="status-card loading" id="sc-runtime">
      <div class="sc-label">Runtime</div>
      <div class="sc-value" id="sc-runtime-val">—</div>
      <div class="sc-sub" id="sc-runtime-sub">Carregando...</div>
      <span class="sc-icon">⚙</span>
    </div>
    <div class="status-card loading" id="sc-comfyui">
      <div class="sc-label">ComfyUI</div>
      <div class="sc-value" id="sc-comfyui-val">—</div>
      <div class="sc-sub" id="sc-comfyui-sub">Verificando...</div>
      <span class="sc-icon">🧠</span>
    </div>
    <div class="status-card loading" id="sc-gpu">
      <div class="sc-label">GPU</div>
      <div class="sc-value" id="sc-gpu-val">—</div>
      <div class="sc-sub" id="sc-gpu-sub">Detectando...</div>
      <div class="vram-bar-wrap" id="sc-vram-wrap" style="display:none">
        <div class="vram-bar-bg"><div class="vram-bar-fill" id="vram-fill" style="width:0%"></div></div>
        <div class="vram-bar-label" id="vram-label"></div>
      </div>
      <span class="sc-icon">🎮</span>
    </div>
    <div class="status-card loading" id="sc-volume">
      <div class="sc-label">Network Volume</div>
      <div class="sc-value" id="sc-volume-val">—</div>
      <div class="sc-sub" id="sc-volume-sub">Verificando...</div>
      <span class="sc-icon">💾</span>
    </div>
  </div>

  <!-- Main content row -->
  <div class="dash-row">

    <!-- Left: models + capabilities -->
    <div>
      <div class="panel">
        <div class="panel-title">Modelos Ativos</div>
        <div id="dash-models"><div class="placeholder" style="padding:20px 0">Carregando...</div></div>
      </div>
      <div class="panel">
        <div class="panel-title">Capabilities</div>
        <div id="dash-caps" style="display:flex;flex-wrap:wrap;gap:4px"></div>
      </div>
    </div>

    <!-- Right: comfyui details + quick actions -->
    <div>
      <div class="panel">
        <div class="panel-title">ComfyUI — Detalhes</div>
        <div id="dash-comfyui-detail"><div class="placeholder" style="padding:20px 0">Aguardando dados...</div></div>
      </div>
      <div class="panel">
        <div class="panel-title">Ações Rápidas</div>
        <div class="quick-actions">
          <button class="btn btn-ghost btn-sm" onclick="runSystemJob('health')">🔄 Health Check</button>
          <button class="btn btn-ghost btn-sm" onclick="runSystemJob('echo')">📤 Echo Test</button>
          <button class="btn btn-blue btn-sm" onclick="showTab('execute')">▶ Executar Capability</button>
          <button class="btn btn-blue btn-sm" onclick="showTab('logs')">📄 Ver Logs</button>
        </div>
        <div class="action-result" id="dash-action-result"></div>
        <div class="status" id="dash-action-status"></div>
      </div>
    </div>

  </div>
</div>
</div>

<!-- ═══════════════ TAB: EXECUTE ═══════════════ -->
<div id="tab-execute" class="tab">
<div class="container">
<div class="grid-3">
  <div>
    <div class="panel">
      <div class="panel-title">Configuração</div>
      <label>Capability</label>
      <select id="cap-select"><option value="">Carregando...</option></select>
      <label>Imagem de entrada</label>
      <div class="drop" id="dropzone" ondragover="event.preventDefault();this.classList.add('drag')" ondragleave="this.classList.remove('drag')" ondrop="onDrop(event)" onclick="document.getElementById('fileInput').click()">
        <input type="file" id="fileInput" accept="image/*" onchange="onFile(this.files[0])">
        <div class="drop-text" id="drop-text">Clique ou arraste uma imagem</div>
        <img id="input-preview" style="display:none">
      </div>
      <label>Node overrides (JSON opcional)</label>
      <textarea id="overrides" rows="3" placeholder='{"2":{"model_name":"outro.pth"}}'></textarea>
      <label>Usar cache experimental</label>
      <select id="use-cache"><option value="1">Sim — reutilizar resultado se idêntico</option><option value="0">Não — executar sempre</option></select>
      <button class="btn btn-primary btn-full" id="run-btn" onclick="runWorkflow()" disabled>▶ Executar</button>
      <div class="status" id="run-status"></div>
    </div>
  </div>
  <div>
    <div class="panel" style="height:100%">
      <div class="panel-title">Resultado</div>
      <div id="exec-result"><div class="placeholder">Execute um workflow para ver o resultado.</div></div>
    </div>
  </div>
  <div>
    <div class="panel" style="height:100%">
      <div class="panel-title">Avaliação</div>
      <div id="eval-area"><div class="placeholder">Disponível após execução.</div></div>
    </div>
  </div>
</div>
</div>
</div>

<!-- ═══════════════ TAB: HISTORY ═══════════════ -->
<div id="tab-history" class="tab">
<div class="container">
  <div class="panel">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
      <div class="panel-title" style="margin:0">Histórico de Execuções</div>
      <select id="hist-filter-cap" onchange="loadHistory()" style="width:auto;flex:1;max-width:200px"><option value="">Todas as capabilities</option></select>
      <select id="hist-filter-ok" onchange="loadHistory()" style="width:auto">
        <option value="">Todas</option><option value="1">Sucesso</option><option value="0">Falha</option>
      </select>
      <button class="btn btn-ghost btn-sm" onclick="loadHistory()">↻ Atualizar</button>
    </div>
    <div id="hist-table-wrap"><div class="placeholder">Carregando...</div></div>
  </div>
  <div id="hist-detail" style="display:none;margin-top:16px">
    <div class="grid-2">
      <div class="panel">
        <div class="panel-title">Entrada</div>
        <div id="hist-input-img" style="text-align:center"><div class="placeholder">Sem imagem</div></div>
        <div id="hist-params" class="json-box" style="margin-top:10px"></div>
      </div>
      <div class="panel">
        <div class="panel-title">Saída</div>
        <div id="hist-output-imgs"></div>
        <div id="hist-metrics" class="metrics-grid" style="margin-top:12px"></div>
        <div id="hist-eval-form"></div>
      </div>
    </div>
  </div>
</div>
</div>

<!-- ═══════════════ TAB: COMPARE ═══════════════ -->
<div id="tab-compare" class="tab">
<div class="container">
  <div class="panel" style="margin-bottom:16px">
    <div class="panel-title">Comparação lado a lado</div>
    <div style="display:flex;gap:10px;align-items:flex-end">
      <div style="flex:1"><label style="margin-top:0">Execução A (ID)</label><input type="number" id="cmp-a" placeholder="ex: 1" min="1"></div>
      <div style="flex:1"><label style="margin-top:0">Execução B (ID)</label><input type="number" id="cmp-b" placeholder="ex: 2" min="1"></div>
      <button class="btn btn-primary" onclick="loadCompare()">Comparar</button>
    </div>
  </div>
  <div class="grid-2" id="compare-area">
    <div class="compare-col">
      <div class="panel"><div class="panel-title">Execução A</div><div id="cmp-panel-a" class="placeholder">Informe o ID acima.</div></div>
    </div>
    <div class="compare-col">
      <div class="panel"><div class="panel-title">Execução B</div><div id="cmp-panel-b" class="placeholder">Informe o ID acima.</div></div>
    </div>
  </div>
</div>
</div>

<!-- ═══════════════ TAB: BENCHMARK ═══════════════ -->
<div id="tab-benchmark" class="tab">
<div class="container">
  <div style="display:flex;gap:10px;align-items:center;margin-bottom:14px">
    <div style="font-size:13px;color:#555">Métricas agregadas de todas as execuções registradas no AI Lab.</div>
    <button class="btn btn-ghost btn-sm" style="margin-left:auto" onclick="loadBenchmark()">↻ Atualizar</button>
  </div>
  <div class="panel" style="margin-bottom:16px">
    <div class="panel-title">Por Capability</div>
    <div id="bench-cap-wrap"><div class="placeholder">Carregando...</div></div>
  </div>
  <div class="panel">
    <div class="panel-title">Por Workflow</div>
    <div id="bench-wf-wrap"><div class="placeholder">Carregando...</div></div>
  </div>
</div>
</div>

<!-- ═══════════════ TAB: LOGS ═══════════════ -->
<div id="tab-logs" class="tab">
<div class="container">
  <div class="panel">
    <div class="panel-title">
      Logs do Sistema
      <span class="auto-badge off" id="log-auto-badge">AUTO OFF</span>
    </div>
    <div class="log-controls">
      <select id="log-file-select" onchange="fetchLogContent()" style="min-width:200px">
        <option value="">Selecionar arquivo de log...</option>
      </select>
      <select id="log-lines-select" onchange="fetchLogContent()" style="width:120px">
        <option value="100">100 linhas</option>
        <option value="200" selected>200 linhas</option>
        <option value="500">500 linhas</option>
        <option value="1000">1000 linhas</option>
      </select>
      <button class="btn btn-ghost btn-sm" onclick="fetchLogContent()">↻ Atualizar</button>
      <button class="btn btn-ghost btn-sm" id="log-auto-btn" onclick="toggleLogAuto()">▶ Auto-refresh (5s)</button>
      <button class="btn btn-ghost btn-sm" onclick="scrollLogToBottom()">⬇ Ir ao final</button>
    </div>
    <div class="log-viewer" id="log-viewer">
      <div class="log-empty">Selecione um arquivo de log acima.</div>
    </div>
    <div class="log-meta" id="log-meta"></div>
  </div>
</div>
</div>

<!-- ═══════════════ TAB: CATALOG ═══════════════ -->
<div id="tab-catalog" class="tab">
<div class="container">
  <div style="display:flex;gap:8px;margin-bottom:14px">
    <button class="btn btn-ghost btn-sm" onclick="showCatalogTab('models')" id="cat-btn-models">Modelos</button>
    <button class="btn btn-ghost btn-sm" onclick="showCatalogTab('capabilities')" id="cat-btn-capabilities">Capabilities</button>
    <button class="btn btn-ghost btn-sm" onclick="showCatalogTab('cache')" id="cat-btn-cache">Cache</button>
  </div>
  <div id="cat-models"><div class="placeholder">Carregando...</div></div>
  <div id="cat-capabilities" style="display:none"><div class="placeholder">Carregando...</div></div>
  <div id="cat-cache" style="display:none"><div class="placeholder">Carregando...</div></div>
</div>
</div>

<script>
// ── Global state ──────────────────────────────────────────────────────────────
let imageB64 = null, imageHash = null, lastExecId = null, currentRating = 0;
let _dashTimer = null, _dashInterval = 30;
let _logTimer = null, _logAutoOn = false;

// ── Tab navigation ────────────────────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.getElementById('tab-btn-' + name).classList.add('active');
  if (name === 'dashboard') loadDashboard();
  if (name === 'history')   loadHistory();
  if (name === 'benchmark') loadBenchmark();
  if (name === 'logs')      loadLogs();
  if (name === 'catalog')   loadCatalog('models');
}

function showCatalogTab(name) {
  ['models','capabilities','cache'].forEach(n => {
    document.getElementById('cat-' + n).style.display = n===name?'':'none';
    document.getElementById('cat-btn-' + n).classList.toggle('btn-primary', n===name);
    document.getElementById('cat-btn-' + n).classList.toggle('btn-ghost', n!==name);
  });
  loadCatalog(name);
}

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  // Load capabilities for Execute tab
  const r = await fetch('/api/capabilities').then(x=>x.json()).catch(()=>({}));
  const caps = r.capabilities || [];
  const sel = document.getElementById('cap-select');
  sel.innerHTML = caps.map(c=>`<option value="${c}">${c}</option>`).join('');
  document.getElementById('run-btn').disabled = false;

  const hf = document.getElementById('hist-filter-cap');
  hf.innerHTML = '<option value="">Todas as capabilities</option>' +
    caps.filter(c=>!['echo','health','image-echo'].includes(c))
        .map(c=>`<option value="${c}">${c}</option>`).join('');

  // Load dashboard on start
  await loadDashboard();

  // Auto-refresh dashboard every 30s
  startDashCountdown();
}
init();

// ── DASHBOARD ─────────────────────────────────────────────────────────────────
function setCard(id, status, val, sub) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `status-card ${status}`;
  if (val !== undefined) document.getElementById(id+'-val').textContent = val;
  if (sub !== undefined) document.getElementById(id+'-sub').textContent = sub;
}

async function loadDashboard() {
  const data = await fetch('/api/status').then(x=>x.json()).catch(e => ({_error: String(e)}));
  if (data._error || data.error) {
    setCard('sc-runtime','warn','Aguardando RunPod...', data._error || data.error);
    setCard('sc-comfyui','warn','● Inicializando', 'Nuvem acordando');
    setCard('sc-gpu','warn','● Aguardando', '-');
    setCard('sc-volume','warn','● Aguardando', '-');
    document.getElementById('hdr-online').className = 'warn';
    return;
  }
  renderDashboard(data);
}

function refreshDashboard() {
  if (_dashTimer) clearTimeout(_dashTimer);
  loadDashboard();
  startDashCountdown();
}

function startDashCountdown() {
  if (_dashTimer) clearTimeout(_dashTimer);
  let remaining = _dashInterval;
  const el = document.getElementById('dash-countdown');
  const tick = () => {
    if (remaining <= 0) {
      loadDashboard();
      remaining = _dashInterval;
    }
    el.textContent = `próxima atualização em ${remaining}s`;
    remaining--;
    _dashTimer = setTimeout(tick, 1000);
  };
  tick();
}

function renderDashboard(d) {
  const now = new Date().toLocaleTimeString('pt-BR');
  document.getElementById('dash-updated').textContent = `atualizado às ${now}`;

  // Header
  const hv = document.getElementById('hdr-version');
  if (hv) hv.textContent = 'v' + (d.runtime_version || '?');
  const hh = document.getElementById('hdr-hostname');
  if (hh) hh.textContent = d.hostname || '';
  const he = document.getElementById('hdr-env');
  if (he && d.environment) {
    he.textContent = d.environment;
    he.style.display = 'inline-block';
    he.className = 'env-badge ' + (d.environment === 'production' ? 'env-production' : 'env-development');
  }

  // Runtime card
  const uptime = d.uptime_seconds != null
    ? (d.uptime_seconds < 60 ? d.uptime_seconds + 's' : Math.round(d.uptime_seconds/60) + 'min')
    : '?';
  setCard('sc-runtime', 'ok', 'v' + (d.runtime_version||'?'), `Python ${d.python_version||'?'} · uptime ${uptime}`);

  // ComfyUI card
  const cu = d.comfyui || {};
  if (cu.available) {
    setCard('sc-comfyui', 'ok', '● Online', `latência ${cu.latency_ms}ms · fila ${cu.queue_pending||0}`);
    document.getElementById('hdr-online').className = 'ok';
  } else {
    setCard('sc-comfyui', 'fail', '● Offline', 'ComfyUI não responde');
    document.getElementById('hdr-online').className = 'fail';
  }

  // GPU card
  const gpu = d.gpu || {};
  if (gpu.model) {
    const vramUsed = gpu.vram_used_mb, vramTotal = gpu.vram_total_mb;
    const vramFree = gpu.vram_free_mb;
    const pct = vramTotal ? Math.round(vramUsed * 100 / vramTotal) : 0;
    setCard('sc-gpu', 'ok', gpu.model.replace('NVIDIA ',''), `Driver ${gpu.driver_version||'?'}`);
    const vramWrap = document.getElementById('sc-vram-wrap');
    const fill = document.getElementById('vram-fill');
    const lbl  = document.getElementById('vram-label');
    if (vramWrap && vramTotal) {
      vramWrap.style.display = 'block';
      fill.style.width = pct + '%';
      fill.className = 'vram-bar-fill' + (pct>80?' high':pct>60?' mid':'');
      lbl.textContent = `${vramUsed}MB / ${vramTotal}MB usado (${pct}%)`;
    }
  } else {
    setCard('sc-gpu', 'warn', 'Não detectada', 'nvidia-smi indisponível');
    document.getElementById('hdr-online').className = document.getElementById('hdr-online').className || 'warn';
  }

  // Volume card
  const st = d.storage || {};
  if (st.volume_available) {
    const free  = st.volume_free_gb  != null ? st.volume_free_gb.toFixed(0)  + 'GB livres' : '';
    const total = st.volume_total_gb != null ? '/ ' + st.volume_total_gb.toFixed(0) + 'GB' : '';
    setCard('sc-volume', 'ok', 'Montado', `${free} ${total}`.trim() || 'disponível');
  } else {
    setCard('sc-volume', 'warn', 'Não montado', 'RUNPOD_VOLUME_PATH não encontrado');
  }

  // Active models
  const modelsEl = document.getElementById('dash-models');
  const am = d.active_models || {};
  if (Object.keys(am).length) {
    modelsEl.innerHTML = Object.entries(am).map(([wf,m]) =>
      `<div class="model-row">
        <span class="model-name">${wf}</span>
        <span class="model-id">${m}</span>
      </div>`
    ).join('');
  } else {
    modelsEl.innerHTML = '<div style="font-size:12px;color:#555;padding:8px 0">Nenhum modelo ativo — execute install_models.py</div>';
  }

  // Capabilities pills
  const capsEl = document.getElementById('dash-caps');
  const caps = d.capabilities || [];
  const wfs  = (d.workflows_available || []).map(w => w.replace(/\\/g,'/'));
  capsEl.innerHTML = caps.map(c => {
    const isSys = ['echo','health','image-echo'].includes(c);
    const route = _CAPABILITY_ROUTES_JS[c] || c;
    const hasWf = wfs.some(w => w === route);
    const cls = isSys ? 'cap-pill sys' : (hasWf ? 'cap-pill' : 'cap-pill plan');
    const dot = isSys ? '●' : (hasWf ? '●' : '○');
    return `<span class="${cls}">${dot} ${c}</span>`;
  }).join('');

  // ComfyUI detail
  const detail = document.getElementById('dash-comfyui-detail');
  const mgr = d.comfyui_manager || {};
  detail.innerHTML = `
    <div class="model-row">
      <span style="font-size:12px;color:#777">Status</span>
      <span>${cu.available ? '<span class="badge badge-green">Online</span>' : '<span class="badge badge-red">Offline</span>'}</span>
    </div>
    ${cu.version ? `<div class="model-row"><span style="font-size:12px;color:#777">Versão</span><span class="model-id">${cu.version}</span></div>` : ''}
    ${cu.torch_version ? `<div class="model-row"><span style="font-size:12px;color:#777">PyTorch</span><span class="model-id">${cu.torch_version}</span></div>` : ''}
    ${cu.latency_ms != null ? `<div class="model-row"><span style="font-size:12px;color:#777">Latência</span><span class="model-id">${cu.latency_ms}ms</span></div>` : ''}
    <div class="model-row">
      <span style="font-size:12px;color:#777">Fila</span>
      <span class="model-id">${cu.queue_running||0} rodando · ${cu.queue_pending||0} pendentes</span>
    </div>
    <div class="model-row">
      <span style="font-size:12px;color:#777">Manager</span>
      <span>${mgr.installed ? '<span class="badge badge-green">instalado</span>' : '<span class="badge badge-gray">não instalado</span>'}${mgr.version?' v'+mgr.version:''}</span>
    </div>
    <div class="model-row">
      <span style="font-size:12px;color:#777">Workflows</span>
      <span class="model-id">${(d.workflows_available||[]).length} disponíveis</span>
    </div>`;
}

// ── Quick actions ─────────────────────────────────────────────────────────────
async function runSystemJob(wfId) {
  const el = document.getElementById('dash-action-result');
  const st = document.getElementById('dash-action-status');
  el.style.display = 'none';
  st.textContent = `⏳ Executando ${wfId}...`;
  const r = await fetch('/api/system/' + wfId, {method:'POST'}).then(x=>x.json()).catch(e=>({error:String(e)}));
  el.style.display = 'block';
  el.textContent = JSON.stringify(r, null, 2);
  st.textContent = r.status === 'completed' ? '✓ Concluído com sucesso' : (r.error ? '✗ ' + r.error : '');
}

// Populated from /api/capabilities
let _CAPABILITY_ROUTES_JS = {};

// ── IMAGE UPLOAD ──────────────────────────────────────────────────────────────
function onDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('drag');
  onFile(e.dataTransfer.files[0]);
}
function onFile(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    imageB64 = e.target.result.split(',')[1];
    imageHash = null;
    const img = document.getElementById('input-preview');
    img.src = e.target.result; img.style.display='block';
    document.getElementById('drop-text').style.display='none';
  };
  reader.readAsDataURL(file);
}

// ── EXECUTE ───────────────────────────────────────────────────────────────────
async function runWorkflow() {
  if (!imageB64) { document.getElementById('run-status').textContent='Selecione uma imagem primeiro.'; return; }
  const cap = document.getElementById('cap-select').value;
  const ovRaw = document.getElementById('overrides').value.trim();
  const useCache = document.getElementById('use-cache').value === '1';
  let nodeOverrides = {};
  if (ovRaw) { try { nodeOverrides = JSON.parse(ovRaw); } catch { document.getElementById('run-status').textContent='Node overrides: JSON inválido.'; return; } }

  document.getElementById('run-btn').disabled = true;
  document.getElementById('run-status').textContent = '⏳ Executando...';
  document.getElementById('exec-result').innerHTML = '<div class="placeholder">Aguardando ComfyUI...</div>';
  document.getElementById('eval-area').innerHTML = '<div class="placeholder">Disponível após execução.</div>';
  lastExecId = null;

  const body = new FormData();
  body.append('capability', cap);
  body.append('image_b64', imageB64);
  body.append('node_overrides', JSON.stringify(nodeOverrides));
  body.append('use_cache', useCache ? '1' : '0');

  const t0 = Date.now();
  const res = await fetch('/api/run', { method:'POST', body }).then(x=>x.json()).catch(e=>({status:'failed',error:String(e)}));
  const elapsed = Date.now() - t0;

  document.getElementById('run-btn').disabled = false;
  document.getElementById('run-status').textContent = '';

  if (res.exec_id) lastExecId = res.exec_id;
  renderExecResult(res, elapsed);
  if (lastExecId) renderEvalForm(lastExecId);
}

function renderExecResult(res, elapsed) {
  const area = document.getElementById('exec-result');
  if (res.status === 'failed') {
    area.innerHTML = `<div class="error-box">❌ ${res.error||JSON.stringify(res)}</div>`;
    return;
  }
  const r = res.result || {};
  const imgs = r.images || [];
  const timing = r.timing || {};
  const obs = res.observability || {};
  const cached = res.cached ? '<span class="badge badge-yellow">⚡ cache</span>' : '';

  let html = cached;
  imgs.forEach(img => {
    if (img.image_b64) html += `<img class="result-img" src="data:image/png;base64,${img.image_b64}" style="margin-bottom:8px">`;
  });
  if (!imgs.length) html += '<div class="placeholder">Workflow completou sem imagens de saída.</div>';
  html += `<div class="timing">
    <span>Total: <strong>${elapsed}ms</strong></span>
    <span>Upload: <strong>${timing.upload_ms||0}ms</strong></span>
    <span>Exec: <strong>${timing.execution_ms||0}ms</strong></span>
    <span>Download: <strong>${timing.download_ms||0}ms</strong></span>
    <span>GPU: <strong>${obs.gpu_model||'?'}</strong></span>
    <span>VRAM: <strong>${obs.vram_used_mb||'?'}/${obs.vram_total_mb||'?'} MB</strong></span>
  </div>`;
  if (res.exec_id) html += `<div class="status" style="margin-top:8px">💾 Registrado #${res.exec_id}</div>`;
  html += `<div class="json-box">${JSON.stringify(res, (k,v)=>k==='image_b64'?'<base64>':v, 2)}</div>`;
  area.innerHTML = html;
}

// ── EVALUATION ────────────────────────────────────────────────────────────────
function renderEvalForm(execId) {
  currentRating = 0;
  document.getElementById('eval-area').innerHTML = `
    <div class="eval-form">
      <h4>Avaliação Manual</h4>
      <div class="stars-input" id="stars">
        ${[1,2,3,4,5].map(i=>`<span onclick="setRating(${i})" id="star-${i}">★</span>`).join('')}
      </div>
      <label style="margin-top:6px">Notas</label>
      <textarea id="eval-notes" rows="2" placeholder="Observações gerais..."></textarea>
      <label>Pontos positivos</label>
      <textarea id="eval-pros" rows="2" placeholder="O que funcionou bem?"></textarea>
      <label>Pontos negativos</label>
      <textarea id="eval-cons" rows="2" placeholder="O que pode melhorar?"></textarea>
      <button class="btn btn-primary btn-full btn-sm" style="margin-top:10px" onclick="submitEval(${execId})">Salvar Avaliação</button>
      <div class="status" id="eval-status"></div>
    </div>`;
}

function setRating(n) {
  currentRating = n;
  for (let i=1;i<=5;i++) document.getElementById('star-'+i).classList.toggle('on', i<=n);
}

async function submitEval(execId) {
  const body = new FormData();
  body.append('score', currentRating);
  body.append('notes', document.getElementById('eval-notes').value);
  body.append('pros', document.getElementById('eval-pros').value);
  body.append('cons', document.getElementById('eval-cons').value);
  await fetch(`/api/history/${execId}/evaluate`, {method:'POST',body});
  document.getElementById('eval-status').textContent = '✓ Avaliação salva';
}

// ── HISTORY ───────────────────────────────────────────────────────────────────
async function loadHistory() {
  const cap = document.getElementById('hist-filter-cap').value;
  const ok  = document.getElementById('hist-filter-ok').value;
  const params = new URLSearchParams();
  if (cap) params.set('capability', cap);
  if (ok !== '') params.set('success', ok);
  document.getElementById('hist-detail').style.display = 'none';

  const rows = await fetch('/api/history?' + params).then(x=>x.json()).catch(()=>[]);
  if (!rows.length) {
    document.getElementById('hist-table-wrap').innerHTML = '<div class="placeholder">Nenhuma execução registrada ainda.</div>';
    return;
  }
  const tbl = `<table>
    <thead><tr><th>ID</th><th>Data</th><th>Capability</th><th>Workflow</th><th>Status</th>
    <th>Exec ms</th><th>VRAM</th><th>Score</th><th>Output</th></tr></thead>
    <tbody>` +
    rows.map(r => `<tr onclick="showHistDetail(${r.id})" style="cursor:pointer">
      <td>#${r.id}</td>
      <td style="font-size:11px;color:#555">${r.created_at}</td>
      <td><strong>${r.capability}</strong></td>
      <td style="font-size:11px;color:#666">${r.workflow_id}</td>
      <td>${r.success ? '<span class="badge badge-green">OK</span>' : '<span class="badge badge-red">FAIL</span>'}</td>
      <td>${r.execution_ms||'-'}</td>
      <td style="font-size:11px">${r.vram_used_mb ? r.vram_used_mb+'MB' : '-'}</td>
      <td>${r.eval_score ? '★'.repeat(r.eval_score) : '-'}</td>
      <td style="font-size:11px">${r.output_count||0} img</td>
    </tr>`).join('') +
    '</tbody></table>';
  document.getElementById('hist-table-wrap').innerHTML = tbl;
}

async function showHistDetail(id) {
  const rec = await fetch(`/api/history/${id}`).then(x=>x.json());
  document.getElementById('hist-detail').style.display = 'block';
  document.getElementById('hist-detail').scrollIntoView({behavior:'smooth'});

  const inputArea = document.getElementById('hist-input-img');
  if (rec.input_hash) {
    inputArea.innerHTML = `<img src="/lab/images/input/${rec.input_hash}.png" style="max-width:100%;max-height:200px;border-radius:4px">`;
  } else {
    inputArea.innerHTML = '<div class="placeholder">Sem imagem de entrada registrada</div>';
  }
  document.getElementById('hist-params').textContent =
    'Params: ' + (rec.input_params||'{}') + '\nOverrides: ' + (rec.node_overrides||'{}');

  const outHtml = Array.from({length: rec.output_count||0}, (_,i) =>
    `<img src="/lab/images/output/${id}/${i}.png" class="result-img" style="margin-bottom:6px">`
  ).join('') || '<div class="placeholder">Sem imagens de saída</div>';
  document.getElementById('hist-output-imgs').innerHTML = outHtml;

  document.getElementById('hist-metrics').innerHTML = [
    {l:'Exec', v:rec.execution_ms+'ms'},
    {l:'Upload', v:rec.upload_ms+'ms'},
    {l:'Download', v:rec.download_ms+'ms'},
    {l:'Total', v:rec.total_ms+'ms'},
    {l:'VRAM usado', v:(rec.vram_used_mb||'-')+'MB'},
    {l:'GPU', v:rec.gpu_model||'-'},
  ].map(m=>`<div class="metric-card"><div class="metric-label">${m.l}</div><div class="metric-value" style="font-size:16px">${m.v}</div></div>`).join('');

  document.getElementById('hist-eval-form').innerHTML = `
    <div class="eval-form">
      <h4>Avaliação #${id}${rec.eval_score ? ' — atual: '+'★'.repeat(rec.eval_score) : ''}</h4>
      <div class="stars-input" id="h-stars">
        ${[1,2,3,4,5].map(i=>`<span onclick="setHistRating(${i},${id})" id="hs-${i}" class="${rec.eval_score>=i?'on':''}"}>★</span>`).join('')}
      </div>
      <label>Notas</label><textarea id="h-notes" rows="2">${rec.eval_notes||''}</textarea>
      <label>Positivos</label><textarea id="h-pros" rows="2">${rec.eval_pros||''}</textarea>
      <label>Negativos</label><textarea id="h-cons" rows="2">${rec.eval_cons||''}</textarea>
      <button class="btn btn-primary btn-sm" style="margin-top:8px" onclick="submitHistEval(${id})">Salvar</button>
    </div>`;
  window._histRating = rec.eval_score || 0;
}

function setHistRating(n, id) {
  window._histRating = n;
  for (let i=1;i<=5;i++) document.getElementById('hs-'+i).classList.toggle('on', i<=n);
}
async function submitHistEval(id) {
  const body = new FormData();
  body.append('score', window._histRating||0);
  body.append('notes', document.getElementById('h-notes').value);
  body.append('pros', document.getElementById('h-pros').value);
  body.append('cons', document.getElementById('h-cons').value);
  await fetch(`/api/history/${id}/evaluate`, {method:'POST',body});
  loadHistory();
}

// ── COMPARE ───────────────────────────────────────────────────────────────────
async function loadCompare() {
  const a = document.getElementById('cmp-a').value;
  const b = document.getElementById('cmp-b').value;
  if (!a || !b) return;
  const [ra, rb] = await Promise.all([
    fetch(`/api/history/${a}`).then(x=>x.json()),
    fetch(`/api/history/${b}`).then(x=>x.json()),
  ]);
  renderComparePanel('a', ra);
  renderComparePanel('b', rb);
}

function renderComparePanel(side, rec) {
  const el = document.getElementById('cmp-panel-' + side);
  if (rec.error) { el.innerHTML = `<div class="error-box">${rec.error}</div>`; return; }
  const imgs = Array.from({length:rec.output_count||0},(_,i)=>
    `<img src="/lab/images/output/${rec.id}/${i}.png" style="max-width:100%;border-radius:4px;margin-bottom:6px">`
  ).join('') || '<div class="placeholder">Sem imagens</div>';
  el.innerHTML = `
    <div style="margin-bottom:10px">
      <strong>#${rec.id}</strong>
      <span class="badge badge-blue" style="margin-left:8px">${rec.capability}</span>
      ${rec.success ? '<span class="badge badge-green" style="margin-left:4px">OK</span>' : '<span class="badge badge-red" style="margin-left:4px">FAIL</span>'}
    </div>
    ${imgs}
    <div class="timing" style="margin-top:8px">
      <span>Exec: <strong>${rec.execution_ms||'-'}ms</strong></span>
      <span>Total: <strong>${rec.total_ms||'-'}ms</strong></span>
      <span>VRAM: <strong>${rec.vram_used_mb||'-'}MB</strong></span>
      ${rec.eval_score ? `<span>Score: <strong>${'★'.repeat(rec.eval_score)}</strong></span>` : ''}
    </div>
    ${rec.eval_notes ? `<p style="margin-top:8px;font-size:12px;color:#666">${rec.eval_notes}</p>` : ''}`;
}

// ── BENCHMARK ─────────────────────────────────────────────────────────────────
async function loadBenchmark() {
  const data = await fetch('/api/benchmark').then(x=>x.json()).catch(()=>({}));
  renderBenchTable('bench-cap-wrap', data.by_capability||[], ['capability','total','successes','success_rate','avg_exec_ms','avg_total_ms','avg_vram_mb','avg_score','last_run']);
  renderBenchTable('bench-wf-wrap', data.by_workflow||[], ['workflow_id','capability','total','success_rate','avg_exec_ms','avg_vram_mb','last_run']);
}

function renderBenchTable(id, rows, cols) {
  if (!rows.length) { document.getElementById(id).innerHTML = '<div class="placeholder">Nenhum dado ainda. Execute workflows no AI Lab.</div>'; return; }
  const fmt = {success_rate: v=>v+'%', avg_exec_ms: v=>v+'ms', avg_total_ms: v=>v+'ms', avg_vram_mb: v=>v+'MB', last_run: v=>(v||'').substring(0,16)};
  const head = cols.map(c=>`<th>${c.replace(/_/g,' ')}</th>`).join('');
  const body = rows.map(r=>`<tr>${cols.map(c=>{
    const v = r[c];
    const disp = fmt[c] ? (v!=null?fmt[c](v):'-') : (v!=null?v:'-');
    return `<td>${disp}</td>`;
  }).join('')}</tr>`).join('');
  document.getElementById(id).innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

// ── LOGS ──────────────────────────────────────────────────────────────────────
async function loadLogs() {
  const data = await fetch('/api/logs').then(x=>x.json()).catch(()=>({files:[],available:false}));
  const sel = document.getElementById('log-file-select');
  const current = sel.value;
  if (!data.available || !data.files.length) {
    sel.innerHTML = '<option value="">Nenhum log disponível</option>';
    document.getElementById('log-viewer').innerHTML = '<div class="log-empty">Volume não montado ou nenhum log encontrado.<br><small style="color:#333">Configure RUNPOD_VOLUME_PATH para acessar os logs.</small></div>';
    document.getElementById('log-meta').textContent = data.log_dir ? `Diretório: ${data.log_dir}` : '';
    return;
  }
  sel.innerHTML = '<option value="">Selecionar arquivo de log...</option>' +
    data.files.map(f => `<option value="${f}"${f===current?' selected':''}>${f}</option>`).join('');
  if (current && data.files.includes(current)) fetchLogContent();
  else if (data.files.length) {
    sel.value = data.files[data.files.length - 1]; // default: most recent
    fetchLogContent();
  }
}

async function fetchLogContent() {
  const name = document.getElementById('log-file-select').value;
  const lines = document.getElementById('log-lines-select').value;
  const viewer = document.getElementById('log-viewer');
  const meta = document.getElementById('log-meta');

  if (!name) {
    viewer.innerHTML = '<div class="log-empty">Selecione um arquivo de log acima.</div>';
    return;
  }

  const data = await fetch(`/api/logs/${name}?lines=${lines}`).then(x=>x.json()).catch(e=>({content:'Erro: '+e,available:false}));

  if (!data.available && !data.content) {
    viewer.innerHTML = `<div class="log-empty">Arquivo não encontrado: ${name}</div>`;
    return;
  }

  // Colorize log lines
  const html = (data.content || '').split('\n').map(line => {
    if (/error|erro|exception|traceback|critical/i.test(line)) return `<span class="log-err">${esc(line)}</span>`;
    if (/warn|aviso/i.test(line)) return `<span class="log-warn">${esc(line)}</span>`;
    return esc(line);
  }).join('\n');

  viewer.innerHTML = html || '<div class="log-empty">Arquivo vazio.</div>';
  meta.textContent = `${data.line_count||0} linhas totais · exibindo últimas ${data.showing||0}`;

  if (_logAutoOn) scrollLogToBottom();
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function scrollLogToBottom() {
  const v = document.getElementById('log-viewer');
  v.scrollTop = v.scrollHeight;
}

function toggleLogAuto() {
  _logAutoOn = !_logAutoOn;
  const badge = document.getElementById('log-auto-badge');
  const btn   = document.getElementById('log-auto-btn');
  if (_logAutoOn) {
    badge.textContent = 'AUTO ON'; badge.className = 'auto-badge';
    btn.textContent = '⏸ Parar auto-refresh';
    _logTimer = setInterval(fetchLogContent, 5000);
    fetchLogContent();
  } else {
    badge.textContent = 'AUTO OFF'; badge.className = 'auto-badge off';
    btn.textContent = '▶ Auto-refresh (5s)';
    if (_logTimer) clearInterval(_logTimer);
  }
}

// ── CATALOG ───────────────────────────────────────────────────────────────────
let _catalogLoaded = {};
async function loadCatalog(which) {
  if (_catalogLoaded[which]) return;
  _catalogLoaded[which] = true;
  if (which === 'models') {
    const models = await fetch('/api/catalog/models').then(x=>x.json()).catch(()=>[]);
    const cat = document.getElementById('cat-models');
    if (!models.length) { cat.innerHTML = '<div class="placeholder">Nenhum modelo no catálogo.</div>'; return; }
    cat.innerHTML = models.map(m => {
      const caps = (m.capabilities||[]).map(c=>`<span class="badge badge-blue">${c}</span>`).join(' ');
      const status = m.status === 'active' ? '<span class="badge badge-green">active</span>' :
                     m.status === 'planned' ? '<span class="badge badge-yellow">planned</span>' :
                     `<span class="badge badge-gray">${m.status||'?'}</span>`;
      const authBadge = m.requires_hf_token ? '<span class="badge badge-red">HF_TOKEN</span>' : '';
      const licenseBadge = m.license_type ? `<span class="badge badge-gray">${m.license_type}</span>` : (m.license ? `<span class="badge badge-gray">${m.license}</span>` : '');
      const preferredBadge = m.preferred ? '<span class="badge badge-green">preferencial</span>' : (m.fallback_priority ? `<span class="badge badge-yellow">fallback #${m.fallback_priority}</span>` : '');
      return `<div class="model-card">
        <h3>${m.name||m.id} <span style="font-size:11px;color:#555">v${m.version||'?'}</span></h3>
        <p>${m.description||''}</p>
        <div class="model-meta">
          ${status}${preferredBadge}${authBadge}
          <span class="badge badge-gray">${m.vendor||'?'}</span>
          ${licenseBadge}
          <span class="badge badge-gray">${m.category||'?'}</span>
          ${m.requirements?.min_vram ? `<span class="badge badge-gray">min ${m.requirements.min_vram}</span>` : ''}
          ${m.metrics?.model_size_mb ? `<span class="badge badge-gray">${m.metrics.model_size_mb}MB</span>` : ''}
          ${caps}
        </div>
        ${m.installation?.path ? `<div style="font-size:11px;color:#444;margin-top:8px">📁 ${m.installation.path}</div>` : ''}
      </div>`;
    }).join('');
  }
  if (which === 'capabilities') {
    const [capData, modelData] = await Promise.all([
      fetch('/api/capabilities').then(x=>x.json()).catch(()=>({})),
      fetch('/api/catalog/capabilities').then(x=>x.json()).catch(()=>[]),
    ]);
    const modelMap = {};
    modelData.forEach(c => { modelMap[c.capability] = c; });
    const caps = capData.capabilities || [];
    const wfs  = capData.workflows_available || [];
    const cat = document.getElementById('cat-capabilities');
    const rows = caps.filter(c => !['echo','health','image-echo'].includes(c)).map(c => {
      const route = capData.routes?.[c] || c;
      const hasWf  = wfs.some(w => w.replace(/\\/g,'/') === route.replace(/\\/g,'/'));
      const wfStatus = hasWf ? '<span class="badge badge-green">OK</span>' : '<span class="badge badge-yellow">planejado</span>';
      const capInfo = modelMap[c];
      const activeModel = capInfo?.active_model || '—';
      const modelsHtml = (capInfo?.models || []).map(m => {
        const activeBadge = m.is_active ? '<span class="badge badge-green">ativo</span>' : '';
        const authBadge = m.requires_hf_token ? '<span class="badge badge-red" title="Necessita HF_TOKEN">auth</span>' : '';
        const pref = m.preferred ? '⭐' : `#${m.fallback_priority||'?'}`;
        return `<span style="font-size:11px;margin-right:6px">${pref} ${m.name} ${activeBadge}${authBadge}</span>`;
      }).join('');
      return `<tr>
        <td><strong>${c}</strong></td>
        <td style="font-size:12px;color:#555">${route}</td>
        <td>${wfStatus}</td>
        <td style="font-size:12px">${activeModel}</td>
        <td>${modelsHtml || '<span style="color:#555;font-size:11px">—</span>'}</td>
      </tr>`;
    }).join('');
    cat.innerHTML = `<table><thead><tr><th>Capability</th><th>Workflow</th><th>Workflow</th><th>Modelo ativo</th><th>Modelos disponíveis</th></tr></thead><tbody>${rows}</tbody></table>`;
  }
  if (which === 'cache') {
    const entries = await fetch('/api/cache').then(x=>x.json()).catch(()=>[]);
    const cat = document.getElementById('cat-cache');
    if (!entries.length) { cat.innerHTML = '<div class="placeholder">Cache vazio.</div>'; return; }
    const rows = entries.map(e=>`<tr>
      <td style="font-size:11px;font-family:monospace;color:#555">${e.cache_key}</td>
      <td>${e.capability}</td>
      <td>${e.hit_count}</td>
      <td style="font-size:11px;color:#555">${e.created_at}</td>
      <td><button class="btn btn-danger btn-sm" onclick="clearCache('${e.cache_key}')">✕</button></td>
    </tr>`).join('');
    cat.innerHTML = `
      <div style="text-align:right;margin-bottom:10px">
        <button class="btn btn-danger btn-sm" onclick="clearCache(null)">Limpar tudo</button>
      </div>
      <table><thead><tr><th>Key</th><th>Capability</th><th>Hits</th><th>Criado</th><th></th></tr></thead><tbody>${rows}</tbody></table>`;
  }
}

async function clearCache(key) {
  const url = key ? `/api/cache/${key}` : '/api/cache';
  await fetch(url, {method:'DELETE'});
  _catalogLoaded.cache = false;
  loadCatalog('cache');
}

// Populate routes map from API for dashboard pills
fetch('/api/capabilities').then(x=>x.json()).then(d => {
  _CAPABILITY_ROUTES_JS = d.routes || {};
}).catch(()=>{});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML


# ── API: Status (Dashboard) ───────────────────────────────────────────────────

@app.get("/api/status")
async def api_status():
    if _remote_mode:
        try:
            # Check with a fast timeout so UI doesn't hang on cold boot
            res = await _remote_runsync("health", timeout_s=10.0)
            if "error" in res:
                return {"error": res["error"], "worker_ready": False}
            return {
                **res.get("result", {}),
                "environment": "cloud",
                "runpod_endpoint": _runpod_endpoint
            }
        except Exception as e:
            return {"error": "Servidor RunPod está inicializando (Cold Start) ou demorando para responder...", "worker_ready": False}

    rt = _rt()
    health = await full_health(rt._config)
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    uptime = int((now - _BOOT_TIME).total_seconds())
    return {
        **health,
        "runtime_version": rt._config.version,
        "environment": rt._config.environment,
        "boot_time": _BOOT_TIME.isoformat(),
        "uptime_seconds": uptime,
        "workflows_available": [str(p).replace("\\", "/") for p in rt._wm.list_available()],
        "capabilities": sorted(_CAPABILITY_ROUTES.keys()),
        "active_models": rt._active_models,
    }


# ── API: System workflows (Dashboard quick actions) ───────────────────────────

@app.post("/api/system/{workflow_id}")
async def api_system_run(workflow_id: str):
    if workflow_id not in ("echo", "health", "image-echo"):
        raise HTTPException(400, f"Workflow de sistema inválido: '{workflow_id}'")
    if _remote_mode:
        try:
            return await _remote_runsync(workflow_id, {})
        except Exception as e:
            return JSONResponse(status_code=400, content={"error": f"Erro na Nuvem: {str(e)}"})

    rt = _rt()
    return await rt.handle({"input": {"workflow_id": workflow_id, "input": {}}})


# ── API: Logs ─────────────────────────────────────────────────────────────────

@app.get("/api/logs")
def api_logs_list():
    rt = _rt()
    log_dir = rt._config.logs_dir
    if not log_dir.exists():
        return {"files": [], "log_dir": str(log_dir), "available": False}
    files = sorted(f.name for f in log_dir.iterdir() if f.is_file() and f.suffix == ".log")
    return {"files": files, "log_dir": str(log_dir), "available": True}


@app.get("/api/logs/{name}")
def api_logs_content(name: str, lines: int = 200):
    if not name.endswith(".log") or "/" in name or "\\" in name or ".." in name:
        raise HTTPException(400, "Nome de arquivo inválido")
    if lines < 1 or lines > 5000:
        lines = 200
    rt = _rt()
    log_path = rt._config.logs_dir / name
    if not log_path.exists():
        return {"name": name, "content": "", "available": False, "line_count": 0, "showing": 0}
    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
        all_lines = content.splitlines()
        last_lines = all_lines[-lines:]
        return {
            "name": name,
            "content": "\n".join(last_lines),
            "available": True,
            "line_count": len(all_lines),
            "showing": len(last_lines),
        }
    except Exception as exc:
        return {"name": name, "content": f"Erro ao ler: {exc}", "available": True, "line_count": 0, "showing": 0}


# ── API: Capabilities ─────────────────────────────────────────────────────────

@app.get("/api/capabilities")
async def api_capabilities():
    all_caps = sorted(list(_CAPABILITY_ROUTES.keys()) + ["echo", "health", "image-echo"])
    if _remote_mode:
        return {
            "capabilities": all_caps,
            "workflows_available": [],
            "routes": {},
            "active_models": {}
        }

    rt = _rt()
    available = rt._wm.list_available()
    return {
        "capabilities": all_caps,
        "workflows_available": [str(p).replace("\\", "/") for p in available],
        "routes": {k: v.replace("\\", "/") for k, v in _CAPABILITY_ROUTES.items()},
        "active_models": rt._active_models,
    }


# ── API: Run ──────────────────────────────────────────────────────────────────

@app.post("/api/run")
async def api_run(
    capability: str = Form(...),
    image_b64: str = Form(...),
    node_overrides: str = Form("{}"),
    use_cache: str = Form("1"),
):
    lb = _lb()
    try:
        overrides = json.loads(node_overrides)
    except json.JSONDecodeError:
        overrides = {}

    resolved = _CAPABILITY_ROUTES.get(capability, capability) if not _remote_mode else capability

    input_hash = lb.save_input_image(image_b64) if image_b64 else None
    if use_cache == "1":
        key = lb.cache_key(resolved, input_hash, overrides)
        cached_json = lb.cache_get(key)
        if cached_json:
            cached_result = json.loads(cached_json)
            cached_result["cached"] = True
            cached_result["exec_id"] = None
            return JSONResponse(cached_result)

    if _remote_mode:
        try:
            result = await _remote_runsync(capability, {"image": image_b64, "node_overrides": overrides})
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"error": f"Erro na Nuvem (Servidor pode estar dormindo): {str(e)}"}
            )
    else:
        rt = _rt()
        job = {"input": {"workflow_id": capability, "input": {"image": image_b64, "node_overrides": overrides}}}
        result = await rt.handle(job)

    exec_id = lb.record(
        capability=capability,
        workflow_id=resolved,
        job_result=result,
        input_hash=input_hash,
        input_params={},
        node_overrides=overrides,
    )
    result["exec_id"] = exec_id
    result["cached"] = False

    if use_cache == "1" and result.get("status") == "completed":
        key = lb.cache_key(resolved, input_hash, overrides)
        lb.cache_set(key, capability, json.dumps(result))

    return JSONResponse(result)


# ── API: History ──────────────────────────────────────────────────────────────

@app.get("/api/history")
def api_history(capability: str = "", success: str = ""):
    from runtime.lab import database as db
    filters: dict = {}
    if capability:
        filters["capability"] = capability
    if success != "":
        filters["success"] = success == "1"
    return db.list_executions(**filters)


@app.get("/api/history/{exec_id}")
def api_history_item(exec_id: int):
    from runtime.lab import database as db
    rec = db.get_execution(exec_id)
    if not rec:
        raise HTTPException(404, "Execução não encontrada")
    return rec


@app.post("/api/history/{exec_id}/evaluate")
def api_evaluate(exec_id: int, score: int = Form(0), notes: str = Form(""), pros: str = Form(""), cons: str = Form("")):
    from runtime.lab import database as db
    db.add_evaluation(exec_id, score, notes, pros, cons)
    return {"ok": True}


# ── API: Benchmark ────────────────────────────────────────────────────────────

@app.get("/api/benchmark")
def api_benchmark():
    from runtime.lab import database as db
    return {
        "by_capability": db.get_benchmark_by_capability(),
        "by_workflow": db.get_benchmark_by_workflow(),
    }


# ── API: Catalog ──────────────────────────────────────────────────────────────

@app.get("/api/catalog/models")
def api_catalog_models():
    return list_models()


@app.get("/api/catalog/capabilities")
def api_catalog_capabilities():
    volume_path = str(_runtime._config.volume_path) if _runtime else None
    return list_capability_models(volume_path)


# ── API: Cache ────────────────────────────────────────────────────────────────

@app.get("/api/cache")
def api_cache_list():
    from runtime.lab import database as db
    return db.cache_list()


@app.delete("/api/cache")
def api_cache_clear_all():
    from runtime.lab import database as db
    count = db.cache_clear()
    return {"cleared": count}


@app.delete("/api/cache/{key}")
def api_cache_clear_key(key: str):
    from runtime.lab import database as db
    db.cache_clear(key)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("playground.server:app", host="0.0.0.0", port=7860, reload=True)
