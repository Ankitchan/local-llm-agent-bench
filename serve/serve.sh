#!/usr/bin/env bash
# Launch llama.cpp's server from serve/model.env (used by the systemd unit, or run it by hand).
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$HERE/model.env"
LLAMA_CMD=${LLAMA_CMD:-llama-server}
# $LLAMA_CMD unquoted on purpose so "llama serve" works. No -ngl: --fit decides GPU placement (and aborts if -ngl is set).
exec $LLAMA_CMD -m "$MODEL_PATH" --alias "$ALIAS" \
  -c "$CTX" --fit on --fit-target "$FIT_TARGET" \
  -fa on -ctk q8_0 -ctv q8_0 --parallel 1 -b "$BATCH" -ub "$BATCH" \
  --sleep-idle-seconds "$IDLE_SLEEP" \
  --jinja --host 127.0.0.1 --port "$PORT"
