#!/bin/bash
# RATEC AI ENGINE — AI Runtime startup
# Prepara o ambiente, inicia o ComfyUI e em seguida o handler RunPod.
set -euo pipefail

VOLUME="${RUNPOD_VOLUME_PATH:-/runpod-volume}"
COMFYUI="/comfyui"
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
COMFYUI_HOST="127.0.0.1"
COMFYUI_READY_TIMEOUT="${COMFYUI_READY_TIMEOUT:-120}"

echo "[ratec] ============================================"
echo "[ratec] RATEC AI ENGINE — AI Runtime"
echo "[ratec] Volume: ${VOLUME}"
echo "[ratec] ComfyUI: ${COMFYUI_HOST}:${COMFYUI_PORT}"
echo "[ratec] ============================================"

# ── Estrutura de diretórios no volume persistente ─────────────────────────────
echo "[ratec] Preparando estrutura de diretórios..."
for dir in \
    models/checkpoints \
    models/clip \
    models/clip_vision \
    models/controlnet \
    models/ipadapter \
    models/loras \
    models/vae \
    models/upscale_models \
    models/embeddings \
    workflows \
    output \
    input \
    temp \
    logs; do
    mkdir -p "${VOLUME}/${dir}"
done
echo "[ratec] Diretórios prontos em ${VOLUME}"

# ── Symlinks ComfyUI → Volume ─────────────────────────────────────────────────
echo "[ratec] Configurando symlinks..."
ln -sfn "${VOLUME}/models"   "${COMFYUI}/models"
ln -sfn "${VOLUME}/output"   "${COMFYUI}/output"
ln -sfn "${VOLUME}/input"    "${COMFYUI}/input"
ln -sfn "${VOLUME}/temp"     "${COMFYUI}/temp"
echo "[ratec] Symlinks configurados"

# ── Iniciar ComfyUI ───────────────────────────────────────────────────────────
echo "[ratec] Iniciando ComfyUI..."
cd "${COMFYUI}"
python3 main.py \
    --listen 0.0.0.0 \
    --port "${COMFYUI_PORT}" \
    --disable-auto-launch \
    --preview-method none \
    >> "${VOLUME}/logs/comfyui.log" 2>&1 &

COMFYUI_PID=$!
echo "[ratec] ComfyUI PID: ${COMFYUI_PID}"

# ── Aguardar ComfyUI estar pronto ─────────────────────────────────────────────
echo "[ratec] Aguardando ComfyUI (timeout: ${COMFYUI_READY_TIMEOUT}s)..."
elapsed=0
interval=2
while [ "${elapsed}" -lt "${COMFYUI_READY_TIMEOUT}" ]; do
    if curl -sf "http://${COMFYUI_HOST}:${COMFYUI_PORT}/system_stats" > /dev/null 2>&1; then
        echo "[ratec] ComfyUI pronto após ${elapsed}s"
        break
    fi
    if ! kill -0 "${COMFYUI_PID}" 2>/dev/null; then
        echo "[ratec] ERRO: ComfyUI encerrou inesperadamente"
        echo "[ratec] Últimas linhas do log:"
        tail -30 "${VOLUME}/logs/comfyui.log" || true
        exit 1
    fi
    sleep "${interval}"
    elapsed=$((elapsed + interval))
done

if [ "${elapsed}" -ge "${COMFYUI_READY_TIMEOUT}" ]; then
    echo "[ratec] ERRO: ComfyUI não iniciou em ${COMFYUI_READY_TIMEOUT}s"
    tail -30 "${VOLUME}/logs/comfyui.log" || true
    exit 1
fi

# ── Iniciar handler RATEC ─────────────────────────────────────────────────────
echo "[ratec] Iniciando RATEC AI ENGINE handler..."
export COMFYUI_URL="http://${COMFYUI_HOST}:${COMFYUI_PORT}"
exec python3 -u /handler/handler.py
