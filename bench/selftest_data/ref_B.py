import pandas as pd
df=pd.read_csv("transactions.csv",parse_dates=["date"]); ex=df[df.amount<0].copy(); ex["spent"]=-ex.amount
cat=ex.groupby("category").agg(t=("spent","sum"),n=("spent","size")).sort_values("t",ascending=False).reset_index()
cat["p"]=cat.t/cat.t.sum()
mon=ex.assign(m=ex.date.dt.strftime("%Y-%m")).pivot_table(index="m",columns="category",values="spent",aggfunc="sum").fillna(0); mon["Total"]=mon.sum(axis=1)
with pd.ExcelWriter("summary.xlsx",engine="openpyxl") as w:
    cat.rename(columns={"category":"Category","t":"Total Spent","n":"Transactions","p":"% of Total Spent"}).to_excel(w,sheet_name="By Category",index=False)
    mon.reset_index().rename(columns={"m":"Month"}).to_excel(w,sheet_name="Monthly",index=False)
    ws=w.sheets["By Category"]; n=len(cat)+2; ws[f"A{n}"]="TOTAL"; ws[f"B{n}"]=f"=SUM(B2:B{n-1})"
