from typing import List, Dict
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from docx import Document
from docx.shared import Pt
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    Paragraph, Spacer, SimpleDocTemplate, 
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER

class ReportGenerator:
    def __init__(self):
        # Define standardized styles
        self.styles = {
            'title': ParagraphStyle(
                'Title', fontName='Helvetica-Bold', 
                fontSize=16, alignment=TA_CENTER,
                spaceAfter=24
            ),
            'chapter1': ParagraphStyle(
                'Chapter1', fontName='Helvetica-Bold',
                fontSize=14, textColor='#0066CC',
                spaceBefore=12, spaceAfter=6
            ),
            'chapter2': ParagraphStyle(
                'Chapter2', fontName='Helvetica-Bold',
                fontSize=12, textColor='#008800',
                spaceBefore=10, spaceAfter=4
            ),
            'content': ParagraphStyle(
                'Content', fontName='Courier',
                fontSize=10, leading=12,
                spaceAfter=0
            ),
            'filename': ParagraphStyle(
                'Filename', fontName='Courier-Bold',
                fontSize=10, textColor='#990000',
                spaceBefore=8, spaceAfter=4
            )
        }

    def generate_pdf(self, items: List[Dict], output_path: str):
        """Generate PDF with consistent styling and spacing"""
        doc = SimpleDocTemplate(output_path)
        story = []
        
        story.append(Paragraph("LOG REPORT", self.styles['title']))
        story.append(Spacer(1, 24))
        
        current_chapter = ""
        for item in items:
            if item['type'] == 'chapter':
                style = self.styles['chapter1'] if item['level'] == 1 else self.styles['chapter2']
                story.append(Paragraph(item['name'].upper(), style))
                current_chapter = item['name']
            else:
                # File content with folder path
                header = f"{current_chapter}/{item['filename']}" if current_chapter else item['filename']
                story.append(Paragraph(header, self.styles['filename']))
                
                for line in item['content']:
                    story.append(Paragraph(line, self.styles['content']))
                
                story.append(Spacer(1, 12))
        
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