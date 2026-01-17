from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BodyFrame(str, Enum):
    SMALL_THIN = "small_thin"
    MEDIUM_BUILD = "medium_build"
    LARGE_HEAVYSET = "large_heavyset"


class SkinType(str, Enum):
    USUALLY_DRY = "usually_dry"
    USUALLY_OILY = "usually_oily"
    BALANCED = "balanced"


class HairType(str, Enum):
    THIN_DRY = "thin_dry"
    THICK_OILY = "thick_oily"
    BALANCED = "balanced"


class TemperatureRegulation(str, Enum):
    COLD_EXTREMITIES = "cold_extremities"
    WARM_SWEATY = "warm_sweaty"
    BALANCED = "balanced"


class AppetiteDigestion(str, Enum):
    UNPREDICTABLE = "unpredictable"
    STRONG_CONSISTENT = "strong_consistent"
    MODERATE_STEADY = "moderate_steady"


class SleepPatterns(str, Enum):
    DIFFICULTY_SLEEPING = "difficulty_sleeping"
    SLEEP_WELL = "sleep_well"
    DEEP_SLEEP_REFRESHED = "deep_sleep_refreshed"


class MentalEmotionalTendencies(str, Enum):
    ANXIOUS = "anxious"
    IRRITABLE = "irritable"
    CALM_COMPOSED = "calm_composed"


class DigestiveHealth(str, Enum):
    GAS_BLOATING = "gas_bloating"
    STRONG_DIGESTION = "strong_digestion"
    SLOW_DIGESTION = "slow_digestion"


class StressResponse(str, Enum):
    ANXIOUS_OVERWHELMED = "anxious_overwhelmed"
    ANGRY_FRUSTRATED = "angry_frustrated"
    WITHDRAW_CALM = "withdraw_calm"


class QuestionnaireResponse(BaseModel):
    # Fixed Constitutional Profile
    body_frame: BodyFrame
    skin_type: SkinType
    hair_type: HairType
    temperature_regulation: TemperatureRegulation
    appetite_digestion: AppetiteDigestion
    sleep_patterns: SleepPatterns
    mental_emotional_tendencies: MentalEmotionalTendencies
    digestive_health: DigestiveHealth
    stress_response: StressResponse
    
    # Dynamic Health Profile
    current_health_conditions: Optional[str] = None
    lifestyle_notes: Optional[str] = None
    dietary_preferences: Optional[str] = None
    exercise_routine: Optional[str] = None
    
    # Additional metadata
    age: Optional[int] = None
    gender: Optional[str] = None


class QuestionnaireSubmission(BaseModel):
    user_id: Optional[str] = None  # For future auth integration
    responses: QuestionnaireResponse
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class ConstitutionalAnalysis(BaseModel):
    vata_score: float
    pitta_score: float
    kapha_score: float
    dominant_dosha: str
    secondary_dosha: Optional[str] = None
    prakruti_type: str  # e.g., "Vata-Pitta", "Kapha", etc.
    analysis_summary: str
