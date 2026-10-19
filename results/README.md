# Results

All measurements come from one laptop: Intel i7-8750H, GTX 1060 Max-Q 6 GB (Vulkan backend), 32 GB RAM, Arch Linux,
llama.cpp `0.6.0-dev` build 11630. The laptop **throttles under sustained load** (CPU held at 2.4 GHz, then its 800 MHz
floor, package at 98 C). Treat speeds as indicative, and generation speed in particular as a range.

## Models

| Label in files | Model | File |
|---|---|---|
| `ornith` | Ornith-1.5-35B-A3B (MoE, ~3B active) | `Ornith-1.5-35B-A3B-IQ3_M.gguf` from `bartowski/Ornith-1.5-35B-A3B-GGUF` (17.4 GB) |
| `qwen` | Qwen3.6-35B-A3B (MoE, ~3B active) | `Qwen3.6-35B-A3B-UD-Q3_K_XL.gguf` from `unsloth/Qwen3.6-35B-A3B-GGUF` (16.8 GB) |

The two files are different quantizations from different uploaders, so speed comparisons are not perfectly like for like.

## What is in this folder

| File | Contents |
|---|---|
| `prefill_sweep.csv` | Batch-size sweep (`-b`/`-ub` 512 to 4096), Ornith, 2 fresh runs each. Same ~4.2k-token prompt shape, different content so nothing was cached. `temp_c` is the CPU temperature at the **end** of the run; `cpu_max_mhz` is a single end-of-run snapshot. |
| `tasks_thinking_off.csv` | Task results with thinking disabled: **one** attempt per task per model, `max_tokens` 3000. |
| `tasks_thinking_on.csv` | Task results with thinking enabled: three attempts per task per model, `max_tokens` 6000. |
| `outputs/thinking_off/<model>/`, `outputs/thinking_on/<model>/` | Every generated script (`A_1.py`, ...) and its `.meta.json` (seconds, tokens, finish reason). Thinking-off files are numbered `_1` because there is one attempt. |

Sampling for all task runs: temperature 0.6, top_p 0.95, top_k 20. Tasks: **A** fix `merge_intervals`, **B** CSV to a
two-sheet xlsx with a SUM formula, **C** a one-page docx memo (see `tasks/`).

## Where each number in the post comes from

| In the post | Source |
|---|---|
| Fig. 2 and the batch table (41 to 92 tok/s) | `prefill_sweep.csv` |
| Fig. 3 (generation vs CPU clock) | `prefill_sweep.csv`: `cpu_max_mhz` against `gen_tok_s` |
| Fig. 4 and the thinking-on table (6/9 vs 3/9) | `outputs/thinking_on/`, scored by `bench/score.py` |
| Thinking-off table (Ornith 2/3, Qwen 3/3) | `outputs/thinking_off/`, scored by `bench/score.py` |

## Numbers that are in the post but **not** in these files

These came from server logs and one-off tests during setup, so they cannot be re-derived from this repo:

- The **~6 minute** "before tuning" time in Fig. 1: extrapolated from a partial log (10,240 tokens in 292 s at batch 512).
- **130 s** (13,331-token Hermes prompt at batch 4096) and **3 s** (25 new tokens once cached).
- The earlier, cooler **127 tok/s** run at batch 4096 (a single run, different prompt length).
- The cache test (a repeated 3,446-token prompt re-processing 19 tokens, 81 s to 2 s) and the Hermes cold-start times (2.5 to 5.7 min).
- `--n-cpu-moe 99` (11.4 tok/s, 2.6 GB VRAM) vs `--fit` (13.4 tok/s, 5.1 GB VRAM), and the idle-sleep memory figures (17.7 GB to 0.7 GB).

## Known quirks in the data

- **`thinking_on/ornith/B_3.meta.json` records `secs: 16640`.** That is wall-clock time that includes a laptop suspend, not
  generation time (the run hit the 6,000-token cap like the others). Ignore its `secs`.
- In the thinking-on round, **all 9 failures are "hit the token cap"**, not wrong answers. Every delivered answer passed.
- Task B never finished in the thinking-on round for either model, so its correctness at larger token budgets is unknown.
- Samples per cell are small (1 and 3). This is an anecdote, not a ranking.
