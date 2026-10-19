"""Regenerate the figures from the measured data in results/. Run from anywhere: python figures/make_figs.py
Fig 2, 3, 4 read results/ files. Fig 1 and 5 use constants taken from server logs (see comments), not from files in this repo.
Output goes to figures/ (override with FIG_OUT=/some/dir)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import csv, glob, json, os, pathlib, textwrap

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = os.environ.get("FIG_OUT", str(HERE)); os.makedirs(OUT, exist_ok=True)
SWEEP = list(csv.DictReader(open(ROOT / "results" / "prefill_sweep.csv")))
SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
ORNITH, QWEN = "#2a78d6", "#eb6834"      # fixed per entity in every chart
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "savefig.facecolor": SURF, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID})

def base(w=10, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h))
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID); ax.tick_params(length=0)
    return fig, ax

def titles(fig, title, sub, source):
    fig.text(0.055, 0.955, title, fontsize=17, fontweight="bold", va="top", color=INK)
    fig.text(0.055, 0.895, sub, fontsize=11.5, va="top", color=INK2)
    fig.text(0.055, 0.015, "\n".join(textwrap.wrap(source, 125)), fontsize=8.5, va="bottom", color=MUTED, linespacing=1.4)

# ---- 1. Time to first reply -------------------------------------------------------------
fig, ax = base()
labels = ["Before tuning\n(batch 512)", "After tuning\n(batch 4096)", "Warm\n(prefix cached)"]
# 380 s: extrapolated from a server log (10,240 tokens took 292 s at batch 512). 130 s and 3 s: measured in server logs
# (13,331-token prompt, 129.7 s at batch 4096; 25 new tokens, 2.8 s when cached). Not in results/ files.
secs = [380, 130, 3]
ax.barh(range(3), secs, height=0.5, color=[ORNITH]*3, zorder=3)
ax.patches[0].set_hatch("////"); ax.patches[0].set_facecolor("#9dbfe9"); ax.patches[0].set_edgecolor(ORNITH)
ax.set_yticks(range(3)); ax.set_yticklabels(labels, fontsize=12, color=INK); ax.invert_yaxis()
ax.set_xlim(0, 600); ax.xaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.set_xlabel("Seconds until Hermes starts replying (13,331-token opening prompt)")
for i, (s, t) in enumerate(zip(secs, ["~6 min (extrapolated)", "2 min 10 s (measured)", "3 s (measured)"])):
    ax.text(s + 8, i, t, va="center", fontsize=12, color=INK, fontweight="bold")
fig.subplots_adjust(left=0.2, right=0.96, top=0.78, bottom=0.22)
titles(fig, "Hermes reads 13,000 tokens before it says a word",
       "Prompt processing, not text generation, is what made my local agent feel broken.",
       "Hatched bar is an extrapolation: 10,240 tokens took 292 s at batch 512 (35 tok/s). Others measured. GTX 1060 6GB, Ornith-1.5-35B-A3B IQ3_M.")
fig.savefig(f"{OUT}/fig1-time-to-first-reply.png", dpi=200); plt.close(fig)

# ---- 2. Prefill vs batch size ------------------------------------------------------------
fig, ax = base()
batches = sorted({r["batch"] for r in SWEEP}, key=int)
r1 = [float(next(r for r in SWEEP if r["batch"] == b and r["run"] == "1")["prefill_tok_s"]) for b in batches]
r2 = [float(next(r for r in SWEEP if r["batch"] == b and r["run"] == "2")["prefill_tok_s"]) for b in batches]
mean = [(a+b)/2 for a, b in zip(r1, r2)]
ax.bar(range(4), mean, width=0.52, color=ORNITH, zorder=3)
for i in range(4):
    ax.plot([i, i], [r2[i], r1[i]], color=INK, lw=2, zorder=4)
    ax.scatter([i, i], [r1[i], r2[i]], s=34, color=SURF, edgecolor=INK, linewidth=1.6, zorder=5)
    ax.text(i, r1[i] + 4, f"{mean[i]:.0f} tok/s", ha="center", fontsize=12.5, fontweight="bold", color=INK)
ax.set_xticks(range(4)); ax.set_xticklabels(batches, fontsize=12.5, color=INK)
ax.set_xlabel("Batch size (-b / -ub)"); ax.set_ylabel("Prompt processing speed (tokens/sec)")
ax.set_ylim(0, 138); ax.yaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.annotate("", xy=(3.0, 124), xytext=(0, 124), arrowprops=dict(arrowstyle="->", color=INK2, lw=1.4))
ax.text(1.5, 128, "2.3x faster", ha="center", fontsize=12, color=INK2, fontweight="bold")
fig.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.21)
titles(fig, "A bigger batch size made prompt processing 2.3x faster",
       "Same GPU memory (5.1 to 5.2 GB). Bars are the mean of two fresh runs; dots show each run.",
       "Same ~4.2k-token prompt per run, different content so nothing was cached. CPU was hot, so absolute numbers run low; an earlier, cooler run reached 127 tok/s at 4096.")
fig.savefig(f"{OUT}/fig2-prefill-vs-batch.png", dpi=200); plt.close(fig)

# ---- 3. Generation speed vs CPU clock ------------------------------------------------------
fig, ax = base()
mhz = [int(r["cpu_max_mhz"]) for r in SWEEP]; tg = [float(r["gen_tok_s"]) for r in SWEEP]
from collections import defaultdict
_g = defaultdict(list)
for i, m in enumerate(mhz): _g[m].append(i)
jit = [0] * len(mhz)
for idxs in _g.values():
    for j, i in enumerate(idxs): jit[i] = (j - (len(idxs) - 1) / 2) * 24 if len(idxs) > 1 else 0
floor = [t for m, t in zip(mhz, tg) if m == min(mhz)]
ax.scatter([m + j for m, j in zip(mhz, jit)], tg, s=95, color=ORNITH, edgecolor=SURF, linewidth=2, zorder=4)
ax.set_xlim(500, 4200); ax.set_ylim(0, 13); ax.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.set_xlabel("Highest CPU core clock at the end of the run (MHz)"); ax.set_ylabel("Generation speed (tokens/sec)")
ax.text(830, 5.2, f"{len(floor)} runs at the {min(mhz)} MHz floor:\n{min(floor):.1f} to {max(floor):.1f} tok/s", fontsize=11.5, color=INK, va="bottom")
ax.text(3600, 11.5, "10.5", fontsize=11.5, color=INK, ha="center", fontweight="bold")
ax.text(2507, 10.8, "9.8", fontsize=11.5, color=INK, ha="center", fontweight="bold")
ax.text(4150, 1.0, "i7-8750H max turbo: 4100 MHz", fontsize=10, color=MUTED, ha="right")
fig.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.21)
titles(fig, "When my laptop's CPU throttled, generation speed fell with it",
       "The model keeps most expert weights in system RAM, so generation is CPU-bound.",
       f"{len(mhz)} runs (points at the {min(mhz)} MHz floor are nudged sideways so none hide each other), one clock reading each at the end of a run (a snapshot, not an average). Package hit 98 C; the kernel's throttle counter passed 230,000. Correlation, not a controlled test.")
fig.savefig(f"{OUT}/fig3-throttling.png", dpi=200); plt.close(fig)

# ---- 4. Tokens used per sample (thinking on) -------------------------------------------------
fig, ax = base(10, 5.8)
CAP = 6000
def _tok(model, t):
    return [json.load(open(f))["tokens"] for f in sorted(glob.glob(str(ROOT / "results" / "outputs" / "thinking_on" / model / f"{t}_*.meta.json")))]
data = {name: (_tok("ornith", t), _tok("qwen", t)) for name, t in (("Coding fix", "A"), ("Finance to xlsx", "B"), ("docx memo", "C"))}
for gi, (name, (o, q)) in enumerate(data.items()):
    for k, (vals, col, dx) in enumerate(((o, ORNITH, -0.17), (q, QWEN, 0.17))):
        for j, v in enumerate(vals):
            x = gi + dx + (j-1)*0.045
            capped = v >= CAP
            ax.scatter([x], [v], s=105, marker="X" if capped else "o", color=col, edgecolor=SURF, linewidth=1.6, zorder=5)
ax.axhline(CAP, color=INK2, lw=1.3, ls=(0, (5, 4)), zorder=2)
ax.text(2.48, CAP + 150, "6,000-token cap: ran out of tokens while thinking, no answer delivered", ha="right", fontsize=10.5, color=INK2)
ax.set_xticks(range(3)); ax.set_xticklabels(list(data), fontsize=12.5, color=INK)
ax.set_ylim(0, 6900); ax.set_xlim(-0.6, 2.6); ax.yaxis.grid(True, color=GRID, zorder=0); ax.set_axisbelow(True)
ax.set_ylabel("Tokens generated per attempt (thinking + answer)")
ax.scatter([], [], s=95, color=ORNITH, label="Ornith-1.5-35B-A3B"); ax.scatter([], [], s=95, color=QWEN, label="Qwen3.6-35B-A3B")
ax.scatter([], [], s=95, marker="X", color=INK2, label="X = hit the cap, no answer")
ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.58), frameon=False, fontsize=11, labelcolor=INK)
fig.subplots_adjust(left=0.1, right=0.97, top=0.80, bottom=0.2)
titles(fig, "With thinking on, Qwen spent far more tokens before answering",
       "Every delivered answer passed its checks. All 9 failures were hitting the cap, not writing wrong code.",
       "3 attempts per task per model, temperature 0.6, thinking enabled. Ornith finished 6 of 9 attempts, Qwen 3 of 9. At 5 to 8 tok/s, 6,000 tokens is 12 to 20 minutes.")
fig.savefig(f"{OUT}/fig4-tokens-per-attempt.png", dpi=200); plt.close(fig)

# ---- 5. Architecture diagram --------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6.2)); ax.set_xlim(0, 110); ax.set_ylim(0, 52); ax.axis("off")
def box(x, y, w, h, text, fc="#ffffff", ec=GRID, tc=INK, fs=11.5, bold=False, lw=1.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6", fc=fc, ec=ec, lw=lw, zorder=3))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", zorder=4, linespacing=1.35)
def arrow(x1, y1, x2, y2, label=None, lx=0, ly=2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=15, color=INK2, lw=1.6, zorder=2))
    if label: ax.text((x1+x2)/2 + lx, (y1+y2)/2 + ly, label, ha="center", fontsize=9.5, color=INK2)
fig.text(0.04, 0.955, "How the model appears only when Hermes needs it", fontsize=17, fontweight="bold", va="top")
fig.text(0.04, 0.905, "systemd socket activation: the model loads on the first request and unloads when idle.", fontsize=11.5, va="top", color=INK2)
box(2, 38, 18, 9, "Hermes Agent\n(any launcher,\ncron, gateway)", fs=11)
box(29, 38, 20, 9, "Socket :8080\nsystemd listens,\nuses no RAM", ec=ORNITH, lw=2.2)
box(58, 38, 20, 9, "socket-proxyd\nexits after\n10 min idle", fs=11)
box(87, 38, 21, 9, "llama serve :8081\nloads model on the\nfirst request", ec=ORNITH, lw=2.2, fs=11)
arrow(20.6, 42.5, 28.4, 42.5, "1. request"); arrow(49.6, 42.5, 57.4, 42.5, "2. starts"); arrow(78.6, 42.5, 86.4, 42.5, "3. forwards")
ax.text(2, 31, "Wait for the model: about 2 to 6 minutes on the first message (load + reading the 13k-token prompt), seconds after.", fontsize=10.5, color=INK2)
box(8, 4, 44, 20, "", fc="#eef4fc", ec=ORNITH, lw=2)
ax.text(30, 22, "GPU: 6 GB VRAM  (about 5.1 GB used)", ha="center", va="center", fontsize=12, fontweight="bold", color=INK)
ax.text(30, 17.2, "Attention layers\nKV cache (q8_0)\nas many experts as fit", ha="center", va="top", fontsize=11, color=INK, linespacing=1.45)
box(58, 4, 50, 20, "", fc="#f3f2ee", ec=MUTED, lw=2)
ax.text(83, 22, "System RAM: 32 GB  (about 9 GB used)", ha="center", va="center", fontsize=12, fontweight="bold", color=INK)
ax.text(83, 17.2, "Remaining expert weights (mapped file ~17 GB)\nOnly ~3B parameters read per token\nIdle: process shrinks 17.7 GB to 0.7 GB", ha="center", va="top", fontsize=11, color=INK, linespacing=1.45)
ax.add_patch(FancyArrowPatch((52.6, 14), (57.4, 14), arrowstyle="<|-|>", mutation_scale=14, color=INK2, lw=1.5, zorder=2))
ax.text(55, 17, "PCIe", ha="center", fontsize=9.5, color=INK2)
ax.add_patch(FancyArrowPatch((97, 37.2), (97, 24.8), arrowstyle="-|>", mutation_scale=14, color=INK2, lw=1.5, zorder=2, linestyle=(0, (4, 3))))
ax.text(98.3, 30.5, "loads", ha="left", fontsize=9.5, color=INK2)
fig.text(0.04, 0.02, "Measured on GTX 1060 Max-Q 6GB, 32GB RAM. Memory figures come from nvidia-smi and free during runs. llama.cpp 0.6.0-dev (build 11630), Vulkan.", fontsize=8.5, color=MUTED)
fig.subplots_adjust(left=0.01, right=0.99, top=0.84, bottom=0.07)
fig.savefig(f"{OUT}/fig5-architecture.png", dpi=200); plt.close(fig)
print("done")
