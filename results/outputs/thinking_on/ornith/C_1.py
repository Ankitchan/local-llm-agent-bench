from docx import Document

doc = Document()

# Title
doc.add_heading("Q1 Budget Review", 0)

# Summary
doc.add_heading("Summary", 1)
doc.add_paragraph(
    "Total actual spending of 6,900 came in 300 under the total budget of 7,200. "
    "The favorable variance was driven mostly by lower-than-planned grocery spending, "
    "which more than offset a slight overspend on dining."
)

# Budget vs Actual
doc.add_heading("Budget vs Actual", 1)
table = doc.add_table(rows=5, cols=3)
table.style = 'Table Grid'

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
for i, (category, budget, actual) in enumerate(data_rows, start=1):
    row = table.rows[i]
    row.cells[0].text = category
    row.cells[1].text = budget
    row.cells[2].text = actual

# Recommendations
doc.add_heading("Recommendations", 1)
doc.add_paragraph(
    "Set a fixed weekly limit on dining-out expenses and monitor it throughout the month.",
    style="List Bullet"
)
doc.add_paragraph(
    "Introduce a monthly dining budget cap and review actual dining costs at each review.",
    style="List Bullet"
)
doc.add_paragraph(
    "Encourage team meals to be planned in advance with pre-approved spending limits.",
    style="List Bullet"
)

doc.save("memo.docx")
