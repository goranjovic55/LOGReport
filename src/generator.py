from typing import List, Dict
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, PageBreak
from docx import Document
from docx.shared import Pt

class ReportGenerator:
    def __init__(self):
        # Define standardized styles
        self.styles = {
            'title': ParagraphStyle(
                'Title',
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=16,
                spaceAfter=12
            ),
            'filename': ParagraphStyle(
                'Filename',
                fontName='Helvetica-Bold',
                fontSize=12,
                textColor='#333333',
                leading=14,
                spaceAfter=8
            ),
            'content': ParagraphStyle(
                'Content',
                fontName='Courier',
                fontSize=10,
                leading=12,
                spaceAfter=0
            ),
            'spacer': ParagraphStyle(
                'Spacer',
                spaceBefore=20,
                spaceAfter=20
            )
        }

    def generate_pdf(self, logs: List[Dict], output_path: str):
        """Generate PDF with consistent styling and spacing"""
        doc = SimpleDocTemplate(output_path)
        story = []
        
        # Add title
        story.append(Paragraph("<b>LOG REPORT</b>", self.styles['title']))
        story.append(Spacer(1, 24))
        
        for log in logs:
            # File section header
            story.append(Paragraph(
                f"File: {log['filename']}",
                self.styles['filename']
            ))
            
            # File content
            for line in log['content']:
                story.append(Paragraph(line, self.styles['content']))
            
            # Section separator
            story.extend([
                PageBreak(),  # Or Spacer(1, 48) for space without page break
                Paragraph("<br/><br/>", self.styles['spacer'])
            ])
        
        doc.build(story)

    def generate_docx(self, logs: List[Dict], output_path: str):
        """Generate DOCX with consistent styling"""
        doc = Document()
        
        # Set default font
        doc.styles['Normal'].font.name = 'Courier New'
        doc.styles['Normal'].font.size = Pt(10)
        
        # Add title
        doc.add_heading('LOG REPORT', 0)
        
        for log in logs:
            # File section
            doc.add_heading(log['filename'], level=1)
            
            # File content
            for line in log['content']:
                p = doc.add_paragraph(line)
                p.style = doc.styles['Normal']
            
            # Section separator
            doc.add_paragraph(" ")  # Extra space
            doc.add_page_break()    # Or doc.add_paragraph(" ") for space without break
        
        doc.save(output_path)