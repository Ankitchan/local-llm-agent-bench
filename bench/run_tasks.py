"""Run the three benchmark tasks (A coding fix, B finance to xlsx, C docx memo) against a running server.

  python bench/run_tasks.py --out results/local/mymodel --samples 3 --thinking on
Results land in <out>/{A,B,C}_<k>.py plus <out>/{A,B,C}_<k>.meta.json. Existing samples are skipped, so it resumes.
--thinking off uses chat_template_kwargs.enable_thinking=false (works for Qwen3/3.5-style templates).
"""
import argparse, json, pathlib, re, time
from common import DEFAULT_URL, ROOT, chat, cpu_temp_c, fmt

ap = argparse.ArgumentParser()
ap.add_argument("--url", default=DEFAULT_URL)
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=3)
ap.add_argument("--thinking", choices=["on", "off"], default="on")
ap.add_argument("--max-tokens", type=int, default=6000)
a = ap.parse_args()

out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
extra = {"top_p": 0.95, "top_k": 20}
if a.thinking == "off":
    extra["chat_template_kwargs"] = {"enable_thinking": False}
for k in range(1, a.samples + 1):
    for t in "ABC":
        if (out / f"{t}_{k}.meta.json").exists():
            continue
        prompt = (ROOT / "tasks" / f"{t}_prompt.txt").read_text()
        t0, t_start = time.time(), cpu_temp_c()
        try:
            d = chat(a.url, [{"role": "user", "content": prompt}], a.max_tokens, temperature=0.6, extra=extra)
        except Exception as e:
            print(f"task {t} sample {k}: ERROR {e}", flush=True); continue
        msg = d["choices"][0]["message"]; txt = msg.get("content") or ""
        code = re.findall(r"```python\n(.*?)```", txt, re.S)
        (out / f"{t}_{k}.py").write_text(code[-1] if code else "")
        meta = {"secs": round(time.time() - t0), "tokens": d["usage"]["completion_tokens"], "finish": d["choices"][0]["finish_reason"],
                "think_chars": len(msg.get("reasoning_content") or ""), "temp_start_c": t_start, "temp_end_c": cpu_temp_c()}
        (out / f"{t}_{k}.meta.json").write_text(json.dumps(meta))
        print(f"task {t} sample {k}: {meta['secs']}s tokens={meta['tokens']} finish={meta['finish']} temp {fmt(t_start)}->{fmt(meta['temp_end_c'])}C", flush=True)
