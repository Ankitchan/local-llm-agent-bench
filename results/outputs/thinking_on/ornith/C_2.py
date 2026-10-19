from docx import Document

doc = Document()

# Title
doc.add_heading("Q1 Budget Review", 0)

# Summary
doc.add_heading("Summary", 1)
doc.add_paragraph(
    "Total actual spending this quarter was 6,900, which came in 300 under the total budget of 7,200. "
    "The favorable variance was driven mostly by lower-than-planned grocery spending, partially offset by higher dining costs. "
    "Overall the budget remained on track and no corrective action is required at this time."
)

# Budget vs Actual
doc.add_heading("Budget vs Actual", 1)
table = doc.add_table(rows=1, cols=3)
table.style = "Table Grid"

header_cells = table.rows[0].cells
header_cells[0].text = "Category"
header_cells[1].text = "Budget"
header_cells[2].text = "Actual"
for cell in header_cells:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True

data_rows = [
    ("Rent", "4200", "4200"),
    ("Groceries", "1500", "1380"),
    ("Dining", "600", "720"),
    ("Transport", "900", "600"),
]
for category, budget, actual in data_rows:
    row_cells = table.add_row().cells
    row_cells[0].text = category
    row_cells[1].text = budget
    row_cells[2].text = actual

# Recommendations
doc.add_heading("Recommendations", 1)
doc.add_paragraph(
    "Dining costs exceeded budget by 120 this quarter, so the following actions are recommended to bring spending back in line.",
    style="Normal"
)
doc.add_paragraph(
    "Set a monthly cap on restaurant and takeout spending so it aligns with the dining budget.",
    style="List Bullet",
)
doc.add_paragraph(
    "Introduce a work-from-home meal plan or catered-lunch initiative to reduce frequent dining-out visits.",
    style="List Bullet",
)
doc.add_paragraph(
    "Review and renegotiate corporate accounts with popular dining vendors for bulk discounts.",
    style="List Bullet",
)

doc.save("memo.docx")
