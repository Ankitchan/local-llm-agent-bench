"""Score model outputs produced by run_tasks.py.

  python bench/score.py results/outputs/thinking_on/ornith results/outputs/thinking_on/qwen --samples 3 [--csv out.csv]

WARNING: this EXECUTES the Python code the models wrote, with your user's permissions. The temp directory and timeouts
are not a sandbox. Run it inside a container or VM if you don't fully trust the outputs.
"""
import argparse, csv, json, pathlib, shutil, subprocess, sys, tempfile
from common import ROOT
import checks

TASKS = {"A": "coding fix", "B": "finance->xlsx", "C": "docx memo"}


def score_one(outdir, t, k):
    code = outdir / f"{t}_{k}.py"; mp = outdir / f"{t}_{k}.meta.json"
    if not mp.exists():
        return "ERROR", "no result"
    meta = json.loads(mp.read_text())
    if meta["finish"] == "length":
        return "FAIL", "hit token cap"
    if not code.exists() or not code.read_text().strip():
        return "FAIL", "no code block"
    w = pathlib.Path(tempfile.mkdtemp()); shutil.copy(ROOT / "tasks" / "transactions.csv", w); shutil.copy(code, w / "sol.py")
    try:
        if t == "A":
            try:
                p, n, fails = checks.check_merge_intervals(str(w / "sol.py"))
            except Exception as e:
                return "FAIL", f"error: {type(e).__name__}: {e}"[:90]
            return ("PASS", f"{p}/{n}") if p == n else ("FAIL", f"{p}/{n} cases passed")
        r = subprocess.run([sys.executable, "sol.py"], cwd=w, capture_output=True, text=True, timeout=120)
        if r.returncode:
            return "FAIL", "script error: " + (r.stderr.strip().splitlines() or ["?"])[-1][:70]
        res = checks.check_xlsx(w / "summary.xlsx", ROOT / "tasks" / "transactions.csv") if t == "B" else checks.check_docx(w / "memo.docx")
        bad = [k2 for k2, v in res.items() if not v]
        return ("PASS", f"{sum(res.values())}/{len(res)}") if not bad else ("FAIL", "failed checks: " + ",".join(bad))
    except subprocess.TimeoutExpired:
        return "FAIL", "timeout"
    except Exception as e:
        return "FAIL", f"verify error: {type(e).__name__}: {e}"[:90]
    finally:
        shutil.rmtree(w, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+"); ap.add_argument("--samples", type=int, default=3); ap.add_argument("--csv")
    a = ap.parse_args()
    rows = []
    for d in a.dirs:
        od = pathlib.Path(d)
        for t in TASKS:
            for k in range(1, a.samples + 1):
                s, why = score_one(od, t, k)
                meta = json.loads((od / f"{t}_{k}.meta.json").read_text()) if (od / f"{t}_{k}.meta.json").exists() else {}
                rows.append({"set": od.name, "task": t, "sample": k, "result": s, "detail": why, "tokens": meta.get("tokens", ""),
                             "finish": meta.get("finish", ""), "secs": meta.get("secs", "")})
    print("PER-SAMPLE DETAIL")
    for d in a.dirs:
        name = pathlib.Path(d).name
        for t in TASKS:
            rs = [r for r in rows if r["set"] == name and r["task"] == t]
            print(f"{name} {t}: " + " | ".join(f"s{r['sample']} {r['result']}" + ("" if r["result"] == "PASS" else f" ({r['detail']})") for r in rs))
    print("\nSUMMARY (passes / samples)")
    for t, label in TASKS.items():
        print(f"{label:16s} " + "   ".join(f"{pathlib.Path(d).name} {sum(1 for r in rows if r['set']==pathlib.Path(d).name and r['task']==t and r['result']=='PASS')}/{a.samples}" for d in a.dirs))
    print(f"{'TOTAL':16s} " + "   ".join(f"{pathlib.Path(d).name} {sum(1 for r in rows if r['set']==pathlib.Path(d).name and r['result']=='PASS')}/{3*a.samples}" for d in a.dirs))
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
