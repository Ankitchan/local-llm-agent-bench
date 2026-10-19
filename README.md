# local-llm-agent-bench

Tools and data behind the blog post **"Your local AI agent is slow because of prefill, not tokens per second"**:
running a 35B Mixture-of-Experts model on a 6 GB laptop GPU with llama.cpp and an agent (Hermes Agent).

It contains:

- **`bench/`**: a prompt-processing (prefill) benchmark, three scored agent-style tasks, and the scorers.
- **`serve/`**: the on-demand setup (systemd socket activation) that loads the model only when something calls it.
- **`results/`**: the raw measurements and every model output behind the post. See [`results/README.md`](results/README.md).
- **`figures/`**: the charts, regenerated from `results/` by `figures/make_figs.py`.

## Requirements

- A recent **llama.cpp** server. The scripts use `--fit`, `--sleep-idle-seconds`, `--jinja`, and `-fa on`, which older builds lack.
  Results here come from llama.cpp `0.6.0-dev` (build 11630, Vulkan backend). The binary is `llama-server` upstream; if your
  build has the `llama serve` wrapper, set `LLAMA_CMD="llama serve"` in `config.env`.
- Python 3.12 or newer (tested on 3.14) and `pip install -r requirements.txt` (versions are pinned: model-written scripts
  can pass or fail depending on the pandas version).
- Optional: `nvidia-smi` (VRAM column in the sweep), `curl`, and systemd for `serve/`.
- Nothing is Intel- or NVIDIA-specific. CPU temperature and clock readings are skipped if your system doesn't expose them.

## Quick start

```bash
git clone <this repo> && cd local-llm-agent-bench
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
cp config.env.example config.env          # edit LLAMA_CMD, PORT, CTX if needed

python bench/selftest.py                  # 1. check the scorers (no model needed)

# 2. prefill benchmark: sweep batch size, 2 fresh runs each, CSV out
MAX_START_TEMP=68 scripts/prefill_sweep.sh /path/to/model.gguf

# 3. the three agent tasks (start a server first, then score)
scripts/server.sh start /path/to/model.gguf
python bench/run_tasks.py --out results/local/mymodel --samples 3 --thinking on
scripts/server.sh stop
python bench/score.py results/local/mymodel --samples 3
```

`results/local/` is git-ignored, so your runs never overwrite the published data.

### ⚠ Security: `score.py` runs code written by an LLM

`bench/score.py` **executes the Python that the model generated**, with your user's permissions. The temporary directory
and timeout are not a sandbox. Run it in a container or VM unless you are sure of what the model produced.

## Reproduce the published numbers

```bash
python bench/selftest.py
python bench/score.py results/outputs/thinking_off/ornith results/outputs/thinking_off/qwen --samples 1   # Ornith 2/3, Qwen 3/3
python bench/score.py results/outputs/thinking_on/ornith  results/outputs/thinking_on/qwen  --samples 3   # Ornith 6/9, Qwen 3/9
python figures/make_figs.py                                                                                # rebuild the charts
```

Scoring is deterministic, so you should get the same pass/fail and reasons. What you can't reproduce without the same
hardware is speed: see the throttling notes in `results/README.md`.

## On-demand model loading (`serve/`)

systemd listens on port 8080 at no cost. The first request starts the server (port 8081) and loads the model; after
`IDLE_SLEEP` seconds idle, llama.cpp unloads the weights and the process shrinks to under 1 GB.

```bash
cp serve/model.env.example serve/model.env     # set MODEL_PATH, ALIAS, LLAMA_CMD
serve/install-systemd.sh                       # writes user units with this checkout's path
systemctl --user enable --now llama-proxy.socket
curl http://127.0.0.1:8080/v1/models           # first call loads the model; expect a wait
```

Notes from testing: the proxy exits after 10 idle minutes but `llama-serve` stays registered; **memory is freed by
`--sleep-idle-seconds`, not by the proxy**. Don't pass `-ngl` together with `--fit` (it aborts). The `systemd-socket-proxyd`
path differs by distro; the installer looks in the usual places. Point your agent at `http://127.0.0.1:8080/v1` and set
its context length to at least 64k.

## License

[MIT](LICENSE). The model weights and the model outputs in `results/` are produced by third-party models
and keep their own licenses (Ornith-1.5 is MIT per its model card; check Qwen's terms before redistributing weights).
