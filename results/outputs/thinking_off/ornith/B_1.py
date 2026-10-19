import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows

EXPENSE_FILE = "transactions.csv"
OUTPUT_FILE = "summary.xlsx"

df = pd.read_csv(EXPENSE_FILE)
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
expenses = df[df["amount"] < 0].copy()
expenses["abs_amount"] = -expenses["amount"]

# ---- Sheet 1: By Category ----
by_cat = (
    expenses.groupby("category")
    .agg(**{
        "Total Spent": ("abs_amount", "sum"),
        "Transactions": ("abs_amount", "count"),
    })
    .reset_index()
)
total_spent = by_cat["Total Spent"].sum()
by_cat["% of Total Spent"] = (
    100 * by_cat["Total Spent"] / total_spent if total_spent else 0.0
)
by_cat = by_cat.sort_values("Total Spent", ascending=False).reset_index(drop=True)
by_cat["Total Spent"] = by_cat["Total Spent"].round(2)
by_cat["% of Total Spent"] = by_cat["% of Total Spent"].round(2)

wb = Workbook()

ws1 = wb.active
ws1.title = "By Category"
ws1.append(["Category", "Total Spent", "Transactions", "% of Total Spent"])
for _, row in by_cat.iterrows():
    ws1.append(
        [
            row["Category"],
            round(float(row["Total Spent"]), 2),
            int(row["Transactions"]),
            round(float(row["% of Total Spent"]), 2),
        ]
    )
ws1.append(
    [
        "TOTAL",
        f'=SUM(B2:B{1 + len(by_cat)})',
        f'=SUM(C2:C{1 + len(by_cat)})',
        f'=SUM(D2:D{1 + len(by_cat)})',
    ]
)
for cell in ws1[1]:
    cell.font = Font(bold=True)

# ---- Sheet 2: Monthly ----
monthly = (
    expenses.assign(month=expenses["date"].dt.strftime("%Y-%m"))
    .groupby(["month", "category"])["abs_amount"]
    .sum()
    .unstack(fill_value=0.0)
)
categories = list(monthly.columns)
monthly = monthly.reindex(sorted(monthly.index))

ws2 = wb.create_sheet("Monthly")
ws2.append([""] + categories + ["Total"])
for month in monthly.index:
    vals = [round(float(v), 2) for v in monthly.loc[month, categories]]
    ws2.append([month] + vals + [""])
    last_col = ws2.cell(ws2.max_row, len(categories) + 1)
    first_val = ws2.cell(ws2.max_row, 2)
    last_val = ws2.cell(ws2.max_row, len(categories) + 1)
    last_val.value = f'=SUM(B{ws2.max_row}:Z{ws2.max_row})'

for cell in ws2[1]:
    cell.font = Font(bold=True)

wb.save(OUTPUT_FILE)
