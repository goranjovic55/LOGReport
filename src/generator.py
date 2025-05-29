from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from docx import Document
from docx.shared import Pt
from typing import List, Dict
from pathlib import Path
import os

class ReportGenerator:
    def __init__(self):
        self.styles = {
            'pdf': {
                'title': ParagraphStyle(
                    'Title',
                    fontName='Helvetica-Bold',
                    fontSize=14,
                    spaceAfter=14,
                    textColor='#5D3E8E'
                ),
                'subtitle': ParagraphStyle(
                    'Subtitle',
                    fontName='Helvetica-Bold',
                    fontSize=12,
                    spaceAfter=6,
                    textColor='#7A5299'
                ),
                'body': ParagraphStyle(
                    'Body',
                    fontName='Courier',
                    fontSize=10,
                    leading=12
                )
            }
        }

    def generate_pdf(self, logs: List[Dict], output_path: str, 
                    lines_mode: str = 'all', 
                    line_limit: int = 0,
                    range_start: int = 0, 
                    range_end: int = 0):
        """Generate PDF with configurable line filtering"""
        try:
            output_path = str(Path(output_path).absolute())
            if not output_path.lower().endswith('.pdf'):
                output_path += '.pdf'
                
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                leftMargin=20*mm,
                rightMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            story = []
            for log in logs:
                # Create a copy of the log to modify
                processed_log = dict(log)
                
                # Apply line filtering based on parameters
                processed_log['content'] = self._filter_lines(
                    processed_log['content'],
                    lines_mode,
                    line_limit,
                    range_start,
                    range_end
                )
                
                # Add section
                story.append(Paragraph(
                    f"File: {processed_log['filename']}",
                    self.styles['pdf']['title']
                ))
                
                # Add filtered content
                story.extend(
                    Paragraph(line, self.styles['pdf']['body'])
                    for line in processed_log['content']
                )
                
                story.append(Spacer(1, 12*mm))
            
            doc.build(story)

        except Exception as e:
            raise RuntimeError(f"PDF generation failed: {str(e)}")

    def _filter_lines(self, lines: List[str], mode: str, 
                    limit: int = 0, start: int = 0, end: int = 0) -> List[str]:
        """Filter lines according to specified mode"""
        if not lines:
            return []
        
        if mode == 'first' and limit > 0:
            return lines[:limit]
        elif mode == 'last' and limit > 0:
            return lines[-limit:]
        elif mode == 'range' and start > 0 and end > start:
            return lines[start-1:end]
        return lines

    def generate_docx(self, logs: List[Dict], output_path: str, lines_mode: str = 'all'):
        """Generate DOCX with line filtering"""
        doc = Document()
        
        # Configure styles
        styles = doc.styles
        title_style = styles.add_style('LogTitle', 1)
        title_style.font.name = 'Arial'
        title_style.font.size = Pt(14)
        title_style.font.color.rgb = 0x5D3E8E
        
        body_style = styles['Normal']
        body_style.font.name = 'Courier New'
        body_style.font.size = Pt(10)
        
        for log in logs:
            # Add title
            doc.add_paragraph(log['filename'], style='LogTitle')
            
            # Process lines
            content = self._filter_lines(
                log['content'],
                lines_mode,
                log.get('line_limit', 0),
                log.get('range_start', 0),
                log.get('range_end', 0)
            )
            
            # Add content
            for line in content:
                doc.add_paragraph(line, style='Normal')
            
            doc.add_page_break()
            
        doc.save(output_path)