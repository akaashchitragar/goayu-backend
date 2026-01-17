"""PDF generation endpoints"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.services.pdf_service import PDFService
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ConstitutionalAnalysisData(BaseModel):
    """Data model for constitutional analysis"""
    vata_score: float
    pitta_score: float
    kapha_score: float
    dominant_dosha: str
    secondary_dosha: Optional[str] = None
    prakruti_type: str
    analysis_summary: str


@router.post("/generate-report")
async def generate_constitutional_report(data: ConstitutionalAnalysisData):
    """
    Generate a PDF report for constitutional analysis
    
    Args:
        data: Constitutional analysis data
        
    Returns:
        PDF file as streaming response
    """
    try:
        # Convert Pydantic model to dict
        analysis_dict = data.model_dump()
        
        # Generate PDF
        pdf_buffer = PDFService.generate_constitutional_report(analysis_dict)
        
        # Return as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=ayushya_constitutional_report.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
