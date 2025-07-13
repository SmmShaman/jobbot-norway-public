"""PDF generator for cover letters."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
    def create_cover_letter_pdf(self, cover_letter_text, username, job_title):
        """Convert cover letter text to PDF."""
        try:
            # Create output directory
            pdf_dir = f'/app/data/users/{username}/letters'
            os.makedirs(pdf_dir, exist_ok=True)
            
            # Generate filename
            safe_title = job_title.replace(' ', '_').replace('/', '_')[:30]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_filename = f'cover_letter_{safe_title}_{timestamp}.pdf'
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            story = []
            
            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=16,
                spaceAfter=30
            )
            story.append(Paragraph('Søknadsbrev', title_style))
            story.append(Spacer(1, 12))
            
            # Add cover letter content
            content_style = ParagraphStyle(
                'CustomNormal',
                parent=self.styles['Normal'],
                fontSize=11,
                leading=14,
                spaceAfter=12
            )
            
            # Split text into paragraphs
            paragraphs = cover_letter_text.split('

')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), content_style))
                    story.append(Spacer(1, 6))
            
            # Build PDF
            doc.build(story)
            
            return {
                'success': True,
                'pdf_path': pdf_path,
                'filename': pdf_filename
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
