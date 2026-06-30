#!/bin/bash
# RATEC AI ENGINE — AI Runtime startup
# Prepara o ambiente, inicia o ComfyUI e em seguida o handler RunPod.
set -euo pipefail

VOLUME="${RUNPOD_VOLUME_PATH:-/runpod-volume}"
COMFYUI="/comfyui"
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
COMFYUI_HOST="127.0.0.1"
COMFYUI_READY_TIMEOUT="${COMFYUI_READY_TIMEOUT:-120}"
HANDLER_DIR="/handler"

echo "[ratec] ============================================"
echo "[ratec] RATEC AI ENGINE — AI Runtime"
echo "[ratec] Volume: ${VOLUME}"
echo "[ratec] ComfyUI: ${COMFYUI_HOST}:${COMFYUI_PORT}"
echo "[ratec] ============================================"

# ── Estrutura de diretórios no volume persistente ─────────────────────────────
echo "[ratec] Preparando estrutura de diretórios..."
for dir in \
    models/BRIA \
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

# ── Instalar/verificar modelos e custom nodes ─────────────────────────────────
# Sempre executa no cold start: downloads são pulados se modelos já existem no
# volume; custom nodes (efêmeros no container) são re-instalados se ausentes.
echo "[ratec] Executando install_models.py..."
INSTALL_EXIT=0
RUNPOD_VOLUME_PATH="${VOLUME}" \
COMFYUI_PATH="${COMFYUI}" \
timeout 300 python3 "${HANDLER_DIR}/scripts/install_models.py" \
    >> "${VOLUME}/logs/install_models.log" 2>&1 || INSTALL_EXIT=$?
if [ "${INSTALL_EXIT}" -eq 0 ]; then
    echo "[ratec] install_models.py concluído com sucesso"
else
    echo "[ratec] AVISO: install_models.py terminou com código ${INSTALL_EXIT}"
    echo "[ratec] Log disponível em: ${VOLUME}/logs/install_models.log"
    echo "[ratec] Continuando — usando comfyui.json padrão como fallback"
fi

# ── Iniciar ComfyUI ───────────────────────────────────────────────────────────
echo "[ratec] Iniciando ComfyUI..."
cd "${COMFYUI}"
python3 main.py \
    --listen "${COMFYUI_HOST}" \
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
