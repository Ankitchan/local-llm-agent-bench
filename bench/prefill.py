"""Measure prompt-processing (prefill) and generation speed with a fresh, uncached prompt.

Each call builds a long system prompt of numbered records. Use a different --seed per run so the server's prompt cache
can't reuse a previous prompt. Prints one CSV line: seed,prompt_tokens,cached_tokens,prefill_tok_s,gen_tok_s,wall_s,temp_c,cpu_max_mhz
"""
import argparse, time
from common import DEFAULT_URL, chat, cpu_temp_c, cpu_max_mhz, fmt

ap = argparse.ArgumentParser()
ap.add_argument("--url", default=DEFAULT_URL)
ap.add_argument("--seed", required=True, help="any string; change it for every run to defeat the prompt cache")
ap.add_argument("--records", type=int, default=150, help="150 is about 4.2k tokens")
ap.add_argument("--question", default="What is the first record?")
ap.add_argument("--max-tokens", type=int, default=128)
a = ap.parse_args()

system = "\n".join(f"Record {a.seed}-{i}: item {i*7%113} costs {i*13%977} dollars on day {i%28+1}." for i in range(a.records))
t0 = time.time()
d = chat(a.url, [{"role": "system", "content": system}, {"role": "user", "content": a.question}], a.max_tokens)
tm = d["timings"]
print(",".join(map(str, [a.seed, tm["prompt_n"], tm["cache_n"], f"{tm['prompt_per_second']:.1f}", f"{tm['predicted_per_second']:.1f}",
                         f"{time.time()-t0:.0f}", fmt(cpu_temp_c()), fmt(cpu_max_mhz())])))
