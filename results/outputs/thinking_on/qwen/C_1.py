from docx import Document

doc = Document()

doc.add_heading('Q1 Budget Review', level=0)

doc.add_heading('Summary', level=1)
doc.add_paragraph(
    'Total actual spending of 6,900 was 300 under the total budget of 7,200. '
    'This favorable variance demonstrates effective cost management across all expense categories.'
)

doc.add_heading('Budget vs Actual', level=1)
table_data = [
    ('Category', 'Budget', 'Actual'),
    ('Rent', '4200', '4200'),
    ('Groceries', '1500', '1380'),
    ('Dining', '600', '720'),
    ('Transport', '900', '600')
]
table = doc.add_table(rows=len(table_data), cols=3)
for i, row_data in enumerate(table_data):
    for j, cell_text in enumerate(row_data):
        cell = table.cell(i, j)
        cell.text = cell_text
        if i == 0:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True

doc.add_heading('Recommendations', level=1)
doc.add_paragraph('Implement a strict weekly spending cap on restaurant visits to curb unnecessary dining expenses.', style='List Bullet')
doc.add_paragraph('Shift two meals per week to home-cooked options to significantly lower average dining costs.', style='List Bullet')
doc.add_paragraph('Negotiate corporate discounts or utilize meal subscription services for more affordable dining alternatives.', style='List Bullet')

doc.save('memo.docx')
