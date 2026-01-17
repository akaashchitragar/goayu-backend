"""PDF generation service for constitutional analysis reports"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Circle, Wedge, String
from reportlab.graphics import renderPDF
import math


class PDFService:
    """Service for generating PDF reports"""
    
    # Color palette matching the website
    PRIMARY_COLOR = colors.HexColor('#30785d')
    PRIMARY_DARK = colors.HexColor('#245a46')
    ACCENT_GOLD = colors.HexColor('#FFC800')
    VATA_COLOR = colors.HexColor('#94a3b8')
    PITTA_COLOR = colors.HexColor('#30785d')
    KAPHA_COLOR = colors.HexColor('#40B440')
    TEXT_MAIN = colors.HexColor('#131615')
    TEXT_MUTED = colors.HexColor('#5C6E66')
    BACKGROUND_LIGHT = colors.HexColor('#fcfcf8')
    
    @staticmethod
    def create_donut_chart(vata_score: float, pitta_score: float, kapha_score: float, 
                          dominant_dosha: str, width: int = 200, height: int = 200):
        """Create a donut chart for dosha distribution"""
        drawing = Drawing(width, height)
        
        # Center and radius
        cx, cy = width / 2, height / 2
        outer_radius = min(width, height) / 2.5
        inner_radius = outer_radius * 0.6
        
        # Calculate angles
        total = vata_score + pitta_score + kapha_score
        vata_angle = (vata_score / total) * 360
        pitta_angle = (pitta_score / total) * 360
        kapha_angle = (kapha_score / total) * 360
        
        # Draw segments with inner radius for donut effect
        start_angle = 90
        
        # Vata segment
        from reportlab.graphics.shapes import Wedge as WedgeShape
        vata_wedge = WedgeShape(cx, cy, outer_radius, start_angle, start_angle - vata_angle,
                               fillColor=PDFService.VATA_COLOR, strokeColor=colors.white, 
                               strokeWidth=1, strokeLineJoin=1)
        vata_wedge.annular = True
        vata_wedge.radius1 = inner_radius
        drawing.add(vata_wedge)
        start_angle -= vata_angle
        
        # Pitta segment
        pitta_wedge = WedgeShape(cx, cy, outer_radius, start_angle, start_angle - pitta_angle,
                                fillColor=PDFService.PITTA_COLOR, strokeColor=colors.white, 
                                strokeWidth=1, strokeLineJoin=1)
        pitta_wedge.annular = True
        pitta_wedge.radius1 = inner_radius
        drawing.add(pitta_wedge)
        start_angle -= pitta_angle
        
        # Kapha segment
        kapha_wedge = WedgeShape(cx, cy, outer_radius, start_angle, start_angle - kapha_angle,
                                fillColor=PDFService.KAPHA_COLOR, strokeColor=colors.white, 
                                strokeWidth=1, strokeLineJoin=1)
        kapha_wedge.annular = True
        kapha_wedge.radius1 = inner_radius
        drawing.add(kapha_wedge)
        
        # Add dominant dosha text in center
        dominant_text = String(cx, cy + 10, dominant_dosha, 
                              fontSize=14, fontName='Helvetica-Bold',
                              fillColor=PDFService.TEXT_MAIN, textAnchor='middle')
        drawing.add(dominant_text)
        
        dominant_label = String(cx, cy - 10, 'DOMINANT',
                               fontSize=8, fontName='Helvetica',
                               fillColor=PDFService.TEXT_MUTED, textAnchor='middle')
        drawing.add(dominant_label)
        
        return drawing
    
    @staticmethod
    def create_health_radar_chart(energy: int, sleep: int, digestion: int, mood: int,
                                  width: int = 200, height: int = 200):
        """Create a radar chart for health markers"""
        drawing = Drawing(width, height)
        
        cx, cy = width / 2, height / 2
        max_radius = min(width, height) / 2.5
        
        # Draw grid circles
        for i in range(3, 0, -1):
            radius = max_radius * (i / 3)
            circle = Circle(cx, cy, radius, fillColor=None, 
                          strokeColor=colors.HexColor('#e5e5e5'), strokeWidth=0.5)
            drawing.add(circle)
        
        # Calculate points for each metric (4 points in a square pattern)
        angles = [90, 0, 270, 180]  # Top, Right, Bottom, Left
        labels = ['SLEEP', 'ENERGY', 'DIGESTION', 'MOOD']
        values = [sleep, energy, digestion, mood]
        
        # Draw axis lines
        from reportlab.graphics.shapes import Line
        for angle in angles:
            rad = math.radians(angle)
            x = cx + max_radius * math.cos(rad)
            y = cy + max_radius * math.sin(rad)
            line = Line(cx, cy, x, y, strokeColor=colors.HexColor('#e5e5e5'), 
                       strokeWidth=0.5, strokeDashArray=[2, 2])
            drawing.add(line)
        
        # Calculate data points
        points = []
        for i, (angle, value) in enumerate(zip(angles, values)):
            rad = math.radians(angle)
            radius = max_radius * (value / 100)
            x = cx + radius * math.cos(rad)
            y = cy + radius * math.sin(rad)
            points.extend([x, y])  # Flatten the points list
            
            # Add data point circles
            point_circle = Circle(x, y, 3, fillColor=PDFService.PRIMARY_COLOR, 
                                strokeColor=PDFService.PRIMARY_COLOR)
            drawing.add(point_circle)
        
        # Draw polygon connecting points
        from reportlab.graphics.shapes import Polygon
        polygon = Polygon(points=points, fillColor=colors.Color(0.188, 0.471, 0.365, alpha=0.2),
                         strokeColor=PDFService.PRIMARY_COLOR, strokeWidth=2)
        drawing.add(polygon)
        
        # Add labels
        label_offset = max_radius + 15
        for angle, label in zip(angles, labels):
            rad = math.radians(angle)
            x = cx + label_offset * math.cos(rad)
            y = cy + label_offset * math.sin(rad)
            text = String(x, y, label, fontSize=7, fontName='Helvetica-Bold',
                         fillColor=PDFService.TEXT_MUTED, textAnchor='middle')
            drawing.add(text)
        
        return drawing
    
    @staticmethod
    def add_watermark(canvas_obj, doc):
        """Add watermark to each page"""
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.setFillColor(colors.HexColor('#e5e5e5'))
        canvas_obj.drawCentredString(A4[0] / 2, 30, "Generated by Ayushya - AI-Powered Ayurvedic Wellness")
        canvas_obj.restoreState()
    
    @staticmethod
    def generate_constitutional_report(analysis_data: dict) -> BytesIO:
        """Generate a complete constitutional analysis PDF report"""
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        # Container for PDF elements
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=PDFService.PRIMARY_COLOR,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=PDFService.TEXT_MUTED,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=PDFService.PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=PDFService.TEXT_MAIN,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=14
        )
        
        # Extract data
        vata_score = analysis_data.get('vata_score', 0)
        pitta_score = analysis_data.get('pitta_score', 0)
        kapha_score = analysis_data.get('kapha_score', 0)
        dominant_dosha = analysis_data.get('dominant_dosha', 'Unknown')
        prakruti_type = analysis_data.get('prakruti_type', 'Unknown')
        analysis_summary = analysis_data.get('analysis_summary', '')
        
        # Calculate health markers
        energy_score = min(100, int(pitta_score * 1.2 + (100 - kapha_score) * 0.8))
        sleep_score = min(100, int(kapha_score * 1.2 + (100 - vata_score) * 0.8))
        digestion_score = min(100, int(100 - abs(pitta_score - 40) * 1.5))
        mood_score = min(100, int((100 - vata_score) * 0.7 + kapha_score * 0.5))
        
        # Header
        elements.append(Paragraph("Your Constitutional Analysis", title_style))
        elements.append(Paragraph("Ayushya - AI-Powered Ayurvedic Wellness", subtitle_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Summary section
        elements.append(Paragraph("Constitutional Summary", heading_style))
        elements.append(Paragraph(analysis_summary, body_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Dosha Distribution Section
        elements.append(Paragraph("Dosha Distribution", heading_style))
        
        # Create table with donut chart and dosha breakdown
        donut_chart = PDFService.create_donut_chart(vata_score, pitta_score, kapha_score, dominant_dosha)
        
        # Dosha breakdown table
        dosha_data = [
            ['Dosha', 'Score', 'Status'],
            ['Vata (Air + Space)', f'{int(vata_score)}%', 
             'Elevated' if vata_score >= 50 else 'Balanced' if vata_score >= 30 else 'Low'],
            ['Pitta (Fire + Water)', f'{int(pitta_score)}%',
             'Elevated' if pitta_score >= 50 else 'Balanced' if pitta_score >= 30 else 'Low'],
            ['Kapha (Earth + Water)', f'{int(kapha_score)}%',
             'Elevated' if kapha_score >= 50 else 'Balanced' if kapha_score >= 30 else 'Low'],
        ]
        
        dosha_table = Table(dosha_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        dosha_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), PDFService.TEXT_MAIN),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        # Combine chart and table
        chart_table = Table([[donut_chart, dosha_table]], colWidths=[2.5*inch, 5*inch])
        chart_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ]))
        
        elements.append(chart_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Health Markers Section
        elements.append(Paragraph("Health Markers", heading_style))
        elements.append(Paragraph(
            "How your current Dosha balance manifests across key areas of your life.",
            body_style
        ))
        
        # Health markers radar chart
        radar_chart = PDFService.create_health_radar_chart(energy_score, sleep_score, 
                                                           digestion_score, mood_score)
        
        # Health markers table
        health_data = [
            ['Marker', 'Score', 'Status'],
            ['Energy', f'{energy_score}%', 
             'High' if energy_score >= 70 else 'Moderate' if energy_score >= 40 else 'Low'],
            ['Sleep Quality', f'{sleep_score}%',
             'Good' if sleep_score >= 70 else 'Fair' if sleep_score >= 40 else 'Poor'],
            ['Digestion', f'{digestion_score}%',
             'Strong' if digestion_score >= 70 else 'Moderate' if digestion_score >= 40 else 'Weak'],
            ['Mood Stability', f'{mood_score}%',
             'Stable' if mood_score >= 70 else 'Variable' if mood_score >= 40 else 'Unstable'],
        ]
        
        health_table = Table(health_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        health_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), PDFService.TEXT_MAIN),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        # Combine radar and table
        health_chart_table = Table([[radar_chart, health_table]], colWidths=[2.5*inch, 5*inch])
        health_chart_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ]))
        
        elements.append(health_chart_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # AI Insights
        elements.append(Paragraph("AI Insights", heading_style))
        insight_text = f"""Your current state (Vikriti) shows elevated {dominant_dosha} in your constitution. 
        This {prakruti_type} profile suggests a unique balance of energies that influences your physical, 
        mental, and emotional characteristics. Understanding your dominant dosha helps create personalized 
        wellness recommendations."""
        elements.append(Paragraph(insight_text, body_style))
        
        # Build PDF with watermark
        doc.build(elements, onFirstPage=PDFService.add_watermark, 
                 onLaterPages=PDFService.add_watermark)
        
        buffer.seek(0)
        return buffer
