"""
RATEC AI Playground
===================
Interface de testes para workflows do AI Runtime.
Roda localmente apontando para um ComfyUI local ou endpoint RunPod.

Uso local (ComfyUI rodando em localhost:8188):
    cd /caminho/do/projeto
    uvicorn playground.server:app --port 7860 --reload

Variáveis de ambiente:
    COMFYUI_URL         URL do ComfyUI (default: http://127.0.0.1:8188)
    RUNPOD_API_KEY      Para testar via RunPod (opcional)
    RUNPOD_ENDPOINT_ID  ID do endpoint RunPod (opcional)
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

# Adiciona a raiz do projeto ao path para importar runtime/
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from runtime import Runtime, _CAPABILITY_ROUTES
from runtime.configuration import RuntimeConfig

app = FastAPI(title="RATEC AI Playground", version="1.0.0")

_runtime: Runtime | None = None


def _get_runtime() -> Runtime:
    global _runtime
    if _runtime is None:
        _runtime = Runtime.initialize()
    return _runtime


# ── HTML UI ───────────────────────────────────────────────────────────────────

_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RATEC AI Playground</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #0f0f0f; color: #e0e0e0; min-height: 100vh; }
  header { background: #1a1a2e; padding: 16px 24px; border-bottom: 1px solid #333; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 18px; font-weight: 600; color: #fff; }
  header span { font-size: 12px; color: #666; }
  .container { max-width: 1100px; margin: 0 auto; padding: 24px; }
  .grid { display: grid; grid-template-columns: 340px 1fr; gap: 20px; }
  .panel { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 20px; }
  .panel h2 { font-size: 14px; font-weight: 600; margin-bottom: 16px; color: #aaa; text-transform: uppercase; letter-spacing: 0.5px; }
  label { display: block; font-size: 13px; color: #aaa; margin-bottom: 6px; margin-top: 14px; }
  label:first-child { margin-top: 0; }
  select, textarea { width: 100%; padding: 9px 12px; background: #111; border: 1px solid #333; border-radius: 6px; color: #e0e0e0; font-size: 13px; outline: none; }
  select:focus, textarea:focus { border-color: #555; }
  textarea { resize: vertical; font-family: monospace; }
  .upload-area { border: 2px dashed #333; border-radius: 6px; padding: 20px; text-align: center; cursor: pointer; transition: border-color 0.2s; }
  .upload-area:hover, .upload-area.drag { border-color: #555; }
  .upload-area input { display: none; }
  .upload-area img { max-width: 100%; max-height: 200px; border-radius: 4px; margin-top: 10px; }
  .upload-area p { font-size: 13px; color: #666; }
  button { width: 100%; padding: 11px; background: #2563eb; border: none; border-radius: 6px; color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 16px; transition: background 0.2s; }
  button:hover { background: #1d4ed8; }
  button:disabled { background: #333; color: #666; cursor: not-allowed; }
  .result-img { max-width: 100%; border-radius: 6px; }
  .timing { font-size: 12px; color: #666; margin-top: 10px; }
  .timing span { color: #888; margin-right: 12px; }
  .error { background: #2a1010; border: 1px solid #5a2020; border-radius: 6px; padding: 12px; color: #ff8080; font-size: 13px; margin-top: 12px; }
  .json-out { background: #111; border: 1px solid #2a2a2a; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 12px; color: #aaa; overflow-x: auto; white-space: pre; margin-top: 12px; max-height: 300px; overflow-y: auto; }
  .status { font-size: 12px; color: #666; margin-top: 8px; min-height: 18px; }
  .capabilities { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
  .cap-badge { background: #1e3a5f; color: #60a5fa; border-radius: 4px; padding: 3px 8px; font-size: 12px; }
  .cap-badge.active { background: #063d20; color: #4ade80; }
  .placeholder { color: #444; font-size: 13px; text-align: center; padding: 40px 20px; }
</style>
</head>
<body>
<header>
  <h1>🎨 RATEC AI Playground</h1>
  <span>Testador de workflows do AI Runtime</span>
</header>
<div class="container">
  <div class="grid">
    <div class="panel">
      <h2>Configuração</h2>
      <label>Capability / Workflow</label>
      <select id="workflow">
        <option value="">Carregando...</option>
      </select>
      <label>Imagem de entrada</label>
      <div class="upload-area" id="dropzone">
        <input type="file" id="fileInput" accept="image/*">
        <p id="dropText">Clique ou arraste uma imagem aqui</p>
        <img id="preview" style="display:none">
      </div>
      <label>Node overrides (JSON, opcional)</label>
      <textarea id="overrides" rows="4" placeholder='{"2": {"model_name": "outro_modelo.pth"}}'></textarea>
      <button id="runBtn" onclick="runWorkflow()" disabled>▶ Executar</button>
      <div class="status" id="status"></div>
    </div>
    <div class="panel">
      <h2>Resultado</h2>
      <div id="resultArea">
        <div class="placeholder">Execute um workflow para ver o resultado aqui.</div>
      </div>
    </div>
  </div>
</div>
<script>
let imageB64 = null;

async function loadCapabilities() {
  try {
    const r = await fetch('/capabilities');
    const data = await r.json();
    const sel = document.getElementById('workflow');
    sel.innerHTML = '';
    (data.capabilities || []).forEach(cap => {
      const opt = document.createElement('option');
      opt.value = cap;
      opt.textContent = cap;
      sel.appendChild(opt);
    });
    document.getElementById('runBtn').disabled = false;
  } catch(e) {
    document.getElementById('status').textContent = 'Erro ao carregar capabilities: ' + e.message;
  }
}

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const dropText = document.getElementById('dropText');

dropzone.onclick = () => fileInput.click();
fileInput.onchange = e => loadFile(e.target.files[0]);
dropzone.ondragover = e => { e.preventDefault(); dropzone.classList.add('drag'); };
dropzone.ondragleave = () => dropzone.classList.remove('drag');
dropzone.ondrop = e => { e.preventDefault(); dropzone.classList.remove('drag'); loadFile(e.dataTransfer.files[0]); };

function loadFile(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    imageB64 = e.target.result.split(',')[1];
    preview.src = e.target.result;
    preview.style.display = 'block';
    dropText.style.display = 'none';
  };
  reader.readAsDataURL(file);
}

async function runWorkflow() {
  const workflowId = document.getElementById('workflow').value;
  const overridesRaw = document.getElementById('overrides').value.trim();
  const btn = document.getElementById('runBtn');
  const status = document.getElementById('status');

  if (!imageB64) { status.textContent = 'Selecione uma imagem primeiro.'; return; }

  let nodeOverrides = {};
  if (overridesRaw) {
    try { nodeOverrides = JSON.parse(overridesRaw); } catch { status.textContent = 'Node overrides: JSON inválido.'; return; }
  }

  btn.disabled = true;
  status.textContent = 'Executando...';
  document.getElementById('resultArea').innerHTML = '<div class="placeholder">Aguardando...</div>';

  const body = new FormData();
  body.append('workflow_id', workflowId);
  body.append('image_b64', imageB64);
  body.append('node_overrides', JSON.stringify(nodeOverrides));

  const t0 = Date.now();
  try {
    const r = await fetch('/run', { method: 'POST', body });
    const data = await r.json();
    const elapsed = Date.now() - t0;
    renderResult(data, elapsed);
  } catch(e) {
    document.getElementById('resultArea').innerHTML = '<div class="error">Erro de rede: ' + e.message + '</div>';
  }

  btn.disabled = false;
  status.textContent = '';
}

function renderResult(data, elapsed) {
  const area = document.getElementById('resultArea');
  if (data.status === 'failed') {
    area.innerHTML = '<div class="error">Falhou: ' + (data.error || JSON.stringify(data)) + '</div>';
    return;
  }
  const result = data.result || {};
  const images = result.images || [];
  const timing = result.timing || {};

  let html = '';
  images.forEach((img, i) => {
    if (img.image_b64) {
      html += `<img class="result-img" src="data:image/png;base64,${img.image_b64}" title="Node ${img.node_id}">`;
    }
  });

  if (!html) html = '<div class="placeholder">Workflow completou mas sem imagens na saída.</div>';

  html += `<div class="timing">
    <span>Total: ${elapsed}ms</span>
    <span>Upload: ${timing.upload_ms || 0}ms</span>
    <span>Execução: ${timing.execution_ms || 0}ms</span>
    <span>Download: ${timing.download_ms || 0}ms</span>
  </div>`;

  html += '<div class="json-out">' + JSON.stringify(data, (k,v) => k === 'image_b64' ? '&lt;base64&gt;' : v, 2) + '</div>';
  area.innerHTML = html;
}

loadCapabilities();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML


@app.get("/capabilities")
async def get_capabilities():
    rt = _get_runtime()
    available_comfyui = rt._wm.list_available()
    all_caps = sorted(
        [cap for cap in _CAPABILITY_ROUTES if
         _CAPABILITY_ROUTES[cap].replace("\\", "/") in [p.replace("\\", "/") for p in available_comfyui]]
        + ["echo", "health", "image-echo"]
    )
    return {"capabilities": all_caps, "workflows_available": available_comfyui}


@app.post("/run")
async def run_workflow(
    workflow_id: str = Form(...),
    image_b64: str = Form(...),
    node_overrides: str = Form("{}"),
):
    rt = _get_runtime()
    try:
        overrides = json.loads(node_overrides)
    except json.JSONDecodeError:
        overrides = {}

    job = {
        "input": {
            "workflow_id": workflow_id,
            "input": {
                "image": image_b64,
                "node_overrides": overrides,
            },
        }
    }
    result = await rt.handle(job)
    return JSONResponse(result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("playground.server:app", host="0.0.0.0", port=7860, reload=True)
