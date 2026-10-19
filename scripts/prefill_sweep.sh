#!/usr/bin/env bash
# Sweep batch size (-b/-ub) and record prefill/generation speed, temperature and CPU clock for each run.
#   scripts/prefill_sweep.sh /path/to/model.gguf [batch sizes...]      (default: 512 1024 2048 4096)
# Env: RUNS=2  OUT=results/local/prefill_sweep.csv  MAX_START_TEMP=68 (optional: wait for the CPU to cool first)
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
[ -f "$ROOT/config.env" ] && source "$ROOT/config.env"
PORT=${PORT:-8081}; export LLM_URL=${LLM_URL:-http://127.0.0.1:$PORT}
MODEL=${1:?usage: prefill_sweep.sh <model.gguf> [batches...]}; shift || true
BATCHES=${*:-512 1024 2048 4096}; RUNS=${RUNS:-2}
OUT=${OUT:-$ROOT/results/local/prefill_sweep.csv}; mkdir -p "$(dirname "$OUT")"
trap '"$ROOT/scripts/server.sh" stop' EXIT
echo "batch,run,prompt_tokens,cached_tokens,prefill_tok_s,gen_tok_s,wall_s,temp_c,cpu_max_mhz,vram_mib" > "$OUT"
cool() {  # wait until the CPU is below MAX_START_TEMP; silently skip if temperature can't be read
  [ -n "${MAX_START_TEMP:-}" ] || return 0
  for _ in $(seq 1 60); do
    t=$(python3 -c "import sys; sys.path.insert(0,'$ROOT/bench'); import common; print(common.cpu_temp_c() or '')")
    [ -z "$t" ] && return 0; [ "$t" -le "$MAX_START_TEMP" ] && return 0; sleep 10
  done
}
for b in $BATCHES; do
  cool; BATCH=$b "$ROOT/scripts/server.sh" start "$MODEL"
  python3 "$ROOT/bench/prefill.py" --seed "WARM$b" --records 30 >/dev/null   # untimed warm-up
  for r in $(seq 1 "$RUNS"); do
    line=$(python3 "$ROOT/bench/prefill.py" --seed "S${b}r${r}")
    vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 || true)
    echo "$b,$r,${line#*,},$vram" | tee -a "$OUT"
  done
done
echo "wrote $OUT"
