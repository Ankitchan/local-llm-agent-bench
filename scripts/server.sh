#!/usr/bin/env bash
# Start/stop a llama.cpp server for benchmarking. Uses a PID file (never pkill), so it can't hit unrelated processes.
#   scripts/server.sh start /path/to/model.gguf [extra llama flags...]
#   scripts/server.sh stop | status
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
[ -f "$ROOT/config.env" ] && source "$ROOT/config.env"
LLAMA_CMD=${LLAMA_CMD:-llama-server}; PORT=${PORT:-8081}; CTX=${CTX:-65536}; FIT_TARGET=${FIT_TARGET:-900}; BATCH=${BATCH:-4096}
RUN="$ROOT/.run"; mkdir -p "$RUN"; PIDF="$RUN/server.pid"

stop() {
  if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
    kill "$(cat "$PIDF")"; for _ in $(seq 1 30); do kill -0 "$(cat "$PIDF")" 2>/dev/null || break; sleep 1; done
  fi
  rm -f "$PIDF"
}
case "${1:-}" in
  start)
    MODEL=${2:?usage: server.sh start <model.gguf> [flags...]}; shift 2
    stop
    # Do NOT add -ngl here: --fit aborts if the GPU layer count is already set.
    # $LLAMA_CMD is intentionally unquoted so "llama serve" works as two words.
    setsid nohup $LLAMA_CMD -m "$MODEL" -c "$CTX" --fit on --fit-target "$FIT_TARGET" -fa on -ctk q8_0 -ctv q8_0 \
      --parallel 1 -b "$BATCH" -ub "$BATCH" --jinja --host 127.0.0.1 --port "$PORT" "$@" > "$RUN/server.log" 2>&1 &
    echo $! > "$PIDF"
    for _ in $(seq 1 360); do
      curl -sf "http://127.0.0.1:$PORT/health" >/dev/null && { echo "server up on :$PORT (log: $RUN/server.log)"; exit 0; }
      kill -0 "$(cat "$PIDF")" 2>/dev/null || { echo "server exited early; see $RUN/server.log" >&2; exit 1; }
      sleep 1
    done
    echo "timed out waiting for the server; see $RUN/server.log" >&2; exit 1 ;;
  stop) stop; echo stopped ;;
  status) [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null && echo "running (pid $(cat "$PIDF"))" || echo "not running" ;;
  *) echo "usage: $0 start <model.gguf> [flags...] | stop | status" >&2; exit 2 ;;
esac
