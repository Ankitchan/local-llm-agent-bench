"""Regenerate tasks/transactions.csv (seed 7). The shipped CSV is canonical: every published score was computed on it.
Usage: python bench/make_transactions.py [output.csv]   (default: prints to tasks/transactions.generated.csv)"""
import csv, datetime, random, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tasks" / "transactions.generated.csv"
random.seed(7)
cats = {"Groceries": (20, 140), "Rent": (1400, 1400), "Dining": (12, 70), "Transport": (5, 60), "Utilities": (40, 160), "Entertainment": (8, 90)}
rows = []
for m in (1, 2, 3):
    rows.append((datetime.date(2026, m, 1), "Salary", "Income", 4200.00))
    rows.append((datetime.date(2026, m, 2), "Landlord", "Rent", -1400.00))
    for _ in range(30):
        c = random.choice([k for k in cats if k != "Rent"])
        lo, hi = cats[c]
        rows.append((datetime.date(2026, m, random.randint(1, 28)), f"{c} purchase", c, -round(random.uniform(lo, hi), 2)))
rows.sort()
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "description", "category", "amount"]); w.writerows(rows)
print(f"wrote {len(rows)} rows to {out}")
