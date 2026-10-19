"""Sanity-check the scorers against known-good and deliberately broken solutions. Run this first: python bench/selftest.py"""
import pathlib, shutil, subprocess, sys, tempfile
from common import ROOT
import checks

D = pathlib.Path(__file__).resolve().parent / "selftest_data"
ok = True
def expect(name, cond):
    global ok; ok &= bool(cond); print(("PASS  " if cond else "FAIL  ") + name)

p, n, _ = checks.check_merge_intervals(str(D / "good_merge.py")); expect("A: correct solution scores 6/6", (p, n) == (6, 6))
p, n, _ = checks.check_merge_intervals(str(D / "buggy_merge.py")); expect("A: buggy solution is caught (<6/6)", p < n)
w = pathlib.Path(tempfile.mkdtemp()); shutil.copy(ROOT / "tasks" / "transactions.csv", w)
for name in ("B", "C"):
    shutil.copy(D / f"ref_{name}.py", w / f"{name}.py"); subprocess.run([sys.executable, f"{name}.py"], cwd=w, check=True, capture_output=True)
good = checks.check_xlsx(w / "summary.xlsx", ROOT / "tasks" / "transactions.csv"); expect("B: reference xlsx passes every check", all(good.values()))
import openpyxl
wb = openpyxl.load_workbook(w / "summary.xlsx"); wb["By Category"]["B2"].value += 5; wb.save(w / "bad.xlsx")
bad = checks.check_xlsx(w / "bad.xlsx", ROOT / "tasks" / "transactions.csv"); expect("B: corrupted xlsx is caught", not bad["cat_totals"])
expect("C: reference docx passes every check", all(checks.check_docx(w / "memo.docx").values()))
shutil.rmtree(w, ignore_errors=True)
print("\nSELFTEST", "OK" if ok else "FAILED"); sys.exit(0 if ok else 1)
