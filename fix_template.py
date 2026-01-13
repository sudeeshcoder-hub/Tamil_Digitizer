from docxtpl import DocxTemplate
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def create_mak_template():
    doc = Document()

    # --- 1. SETUP NARROW MARGINS ---
    section = doc.sections[0]
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)

    # --- 2. SET DEFAULT FONT (Nirmala UI, Size 10) ---
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Nirmala UI'
    font.size = Pt(10)
    style.element.rPr.rFonts.set(qn('w:cs'), 'Nirmala UI')

    # --- 3. THE HEADER (Table Layout) ---
    p_school = doc.add_paragraph("எம். ஏ.கே. குழுமப் பள்ளிகள்")
    p_school.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_school.runs[0].bold = True
    p_school.runs[0].font.size = Pt(14)

    table = doc.add_table(rows=3, cols=2)
    table.autofit = True
    table.width = Inches(7.5)

    # Row 1
    cell_1a = table.cell(0, 0)
    p = cell_1a.paragraphs[0]
    p.add_run("வகுப்பு: ").bold = True
    p.add_run("{{ header.class }}").bold = True
    
    cell_1b = table.cell(0, 1)
    p = cell_1b.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run("மதிப்பெண்கள்: {{ header.marks }}").bold = True

    # Row 2
    cell_2a = table.cell(1, 0)
    p = cell_2a.paragraphs[0]
    p.add_run("தேதி: {{ header.date }}").bold = True

    cell_2b = table.cell(1, 1)
    p = cell_2b.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run("நேரம்: {{ header.time }}").bold = True
    
    # Row 3
    cell_3a = table.cell(2, 0)
    p = cell_3a.paragraphs[0]
    p.add_run("தமிழ் முதல் தாள்").bold = True

    doc.add_paragraph("__________________________________________________________________________________________")

    # --- 4. DYNAMIC CONTENT LOOP ---
    doc.add_paragraph("{%p for section in sections %}")
    
    # Section Header
    p_sec = doc.add_paragraph()
    p_sec.add_run("{{ section.roman }}. {{ section.title }}")
    p_sec.runs[0].bold = True
    p_sec.paragraph_format.tab_stops.add_tab_stop(Inches(7.3), WD_ALIGN_PARAGRAPH.RIGHT)
    p_sec.add_run("\t{{ section.marks_eq }}").bold = True
    
    # Questions Loop
    doc.add_paragraph("{%p for q in section.questions %}")
    
    # Question Text
    doc.add_paragraph("{{ q.no }}. {{ q.text }}")
    
    # MCQ Options (FIXED: Using {% if %} instead of {%p if %} inside runs)
    doc.add_paragraph("{%p if q.options %}")
    p_opt = doc.add_paragraph()
    p_opt.paragraph_format.left_indent = Inches(0.4) 
    
    # Note: No 'p' in these tags because they are inside a line, not a paragraph block
    p_opt.add_run("{% if q.options[0] %} அ) {{ q.options[0] }}    {% endif %}")
    p_opt.add_run("{% if q.options[1] %} ஆ) {{ q.options[1] }}    {% endif %}")
    p_opt.add_run("{% if q.options[2] %} இ) {{ q.options[2] }}    {% endif %}")
    p_opt.add_run("{% if q.options[3] %} ஈ) {{ q.options[3] }}    {% endif %}")
    
    doc.add_paragraph("{%p endif %}") # End MCQ check
    doc.add_paragraph("{%p endfor %}") # End Question Loop
    
    doc.add_paragraph("{%p endfor %}") # End Section Loop
    
    doc.add_paragraph("_______________________________________________")

    doc.save("template_mak.docx")
    print("✅ SUCCESS: 'template_mak.docx' created successfully!")

if __name__ == "__main__":
    create_mak_template()