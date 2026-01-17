from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ConsultationRequest(BaseModel):
    questionnaire_id: str
    symptoms: str
    additional_notes: Optional[str] = None


class Remedy(BaseModel):
    name: str
    description: str
    preparation_method: str
    dosage: str
    timing: str
    duration: str
    precautions: Optional[str] = None
    ingredients: List[str]


class ScriptureReference(BaseModel):
    text_name: str
    chapter: str
    verse: str
    content: str


class ConsultationResponse(BaseModel):
    consultation_id: str
    questionnaire_id: str
    symptoms: str
    constitutional_summary: str
    dosha_analysis: str
    remedies: List[Remedy]
    scripture_references: List[ScriptureReference]
    lifestyle_recommendations: List[str]
    dietary_recommendations: List[str]
    general_advice: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConsultationHistory(BaseModel):
    id: str
    user_id: Optional[str] = None
    symptoms: str
    created_at: datetime
    constitutional_type: str
