#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  SignVani — unified startup script
#  Usage:
#    ./start.sh                       # faster-whisper STT (default)
#    ASR_ENGINE=vosk ./start.sh       # Vosk STT (lowest latency fallback)
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/nlp_backend"
CLIENT_DIR="$SCRIPT_DIR/client"
VENV="$BACKEND_DIR/.venv/bin/activate"
ASR_ENGINE="${ASR_ENGINE:-faster_whisper}"

# ── colour helpers ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[SignVani]${NC} $*"; }
warn()  { echo -e "${YELLOW}[SignVani]${NC} $*"; }
error() { echo -e "${RED}[SignVani]${NC} $*"; }

# ── cleanup on Ctrl-C / exit ──────────────────────────────────────────────────
cleanup() {
    echo ""
    info "Shutting down…"
    kill "$BACKEND_PID"  2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID"  2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
    info "All services stopped."
}
trap cleanup EXIT INT TERM

# ── pre-flight checks ─────────────────────────────────────────────────────────
if [ ! -f "$VENV" ]; then
    error "Virtual environment not found at $VENV"
    error "Run: python -m venv $BACKEND_DIR/.venv && source $VENV && pip install -r $BACKEND_DIR/requirements.txt"
    exit 1
fi

if ! command -v node &>/dev/null; then
    error "Node.js not found. Install it to run the React frontend."
    exit 1
fi

# ── backend ───────────────────────────────────────────────────────────────────
info "Starting backend (ASR_ENGINE=$ASR_ENGINE, port 8000)…"
(
    cd "$BACKEND_DIR"
    source "$VENV"
    ASR_ENGINE="$ASR_ENGINE" python api_server.py
) &
BACKEND_PID=$!

# wait until the API is up (up to 60 s)
info "Waiting for backend to be ready…"
READY=0
for i in $(seq 1 60); do
    if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
        READY=1
        info "Backend ready ✓"
        break
    fi
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        error "Backend process crashed. Check logs above."
        exit 1
    fi
    sleep 1
done

if [ "$READY" -eq 0 ]; then
    warn "Backend did not respond within 60 s — frontend starting anyway."
fi

# ── frontend ──────────────────────────────────────────────────────────────────
info "Starting frontend (port 3000)…"
(
    cd "$CLIENT_DIR"
    REACT_APP_API_URL=http://localhost:8000 npm start
) &
FRONTEND_PID=$!

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
info "╔══════════════════════════════════════════════╗"
info "║         SignVani is running                  ║"
info "║  Frontend : http://localhost:3000            ║"
info "║  Backend  : http://localhost:8000            ║"
info "║  ASR      : $ASR_ENGINE$(printf '%*s' $((28 - ${#ASR_ENGINE})) '')║"
info "╚══════════════════════════════════════════════╝"
echo ""
info "Press Ctrl+C to stop all services."

# keep script alive until a child dies or user interrupts
wait -n "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
