from fastapi import APIRouter, HTTPException, status
from app.models.consultation import ConsultationRequest, ConsultationResponse, Remedy, ScriptureReference
from app.services.ai_service import AIService
from app.services.user_service import UserService
from app.core.database import get_database
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any


router = APIRouter()

def get_user_service():
    return UserService()


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_consultation(request: ConsultationRequest):
    """
    Create a new consultation based on questionnaire and symptoms
    """
    try:
        db = get_database()
        
        # Fetch questionnaire data
        questionnaire = db.questionnaires.find_one({"_id": ObjectId(request.questionnaire_id)})
        
        if not questionnaire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Questionnaire not found"
            )
        
        # Extract constitutional analysis
        constitutional_analysis_dict = questionnaire.get("constitutional_analysis")
        
        if not constitutional_analysis_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Constitutional analysis not found in questionnaire"
            )
        
        # Convert dict to ConstitutionalAnalysis model
        from app.models.questionnaire import ConstitutionalAnalysis
        constitutional_analysis = ConstitutionalAnalysis(**constitutional_analysis_dict)
        
        # Get user info if available
        user_id = questionnaire.get("user_id")
        user_email = None
        user_name = None
        
        if user_id:
            user = db.users.find_one({"user_id": user_id})
            if user:
                user_email = user.get("email")
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
                user_name = f"{first_name} {last_name}".strip() or None
        
        # Generate consultation using AI
        ai_service = AIService()
        consultation_data = await ai_service.generate_consultation(
            symptoms=request.symptoms,
            constitutional_analysis=constitutional_analysis,
            additional_notes=request.additional_notes,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name
        )
        
        # Prepare consultation document
        consultation_doc = {
            "questionnaire_id": request.questionnaire_id,
            "symptoms": request.symptoms,
            "additional_notes": request.additional_notes,
            "constitutional_summary": constitutional_analysis.analysis_summary,
            "dosha_analysis": consultation_data.get("dosha_analysis", ""),
            "remedies": consultation_data.get("remedies", []),
            "scripture_references": consultation_data.get("scripture_references", []),
            "lifestyle_recommendations": consultation_data.get("lifestyle_recommendations", []),
            "dietary_recommendations": consultation_data.get("dietary_recommendations", []),
            "general_advice": consultation_data.get("general_advice", ""),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save to MongoDB
        result = db.consultations.insert_one(consultation_doc)
        
        consultation_id = str(result.inserted_id)
        
        # Add consultation_id field to the document for easier querying
        db.consultations.update_one(
            {"_id": result.inserted_id},
            {"$set": {"consultation_id": consultation_id}}
        )
        
        # Link consultation to user if user_id exists in questionnaire
        if questionnaire.get("user_id"):
            user_id = questionnaire.get("user_id")
            user_service = get_user_service()
            await user_service.add_consultation_to_user(user_id, consultation_id)
            await user_service.log_activity(
                user_id=user_id,
                activity_type="consultation_created",
                activity_data={
                    "consultation_id": consultation_id,
                    "questionnaire_id": request.questionnaire_id
                }
            )
        
        # Prepare response
        response_data = {
            "consultation_id": consultation_id,
            "questionnaire_id": request.questionnaire_id,
            "symptoms": request.symptoms,
            "constitutional_summary": constitutional_analysis.analysis_summary,
            "dosha_analysis": consultation_data.get("dosha_analysis", ""),
            "remedies": consultation_data.get("remedies", []),
            "scripture_references": consultation_data.get("scripture_references", []),
            "lifestyle_recommendations": consultation_data.get("lifestyle_recommendations", []),
            "dietary_recommendations": consultation_data.get("dietary_recommendations", []),
            "general_advice": consultation_data.get("general_advice", ""),
            "created_at": consultation_doc["created_at"]
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating consultation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating consultation: {str(e)}"
        )


@router.get("/{consultation_id}", response_model=Dict[str, Any])
async def get_consultation(consultation_id: str):
    """
    Get consultation by ID
    """
    try:
        db = get_database()
        consultation = db.consultations.find_one({"_id": ObjectId(consultation_id)})
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        # Convert ObjectId to string
        consultation["_id"] = str(consultation["_id"])
        consultation["consultation_id"] = consultation.pop("_id")
        
        return consultation
        
    except Exception as e:
        print(f"Error fetching consultation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching consultation: {str(e)}"
        )


@router.get("/", response_model=List[Dict[str, Any]])
async def list_consultations(skip: int = 0, limit: int = 10):
    """
    List all consultations
    """
    try:
        db = get_database()
        consultations = list(
            db.consultations.find()
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        
        # Convert ObjectId to string
        for c in consultations:
            c["consultation_id"] = str(c.pop("_id"))
        
        return consultations
        
    except Exception as e:
        print(f"Error listing consultations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing consultations: {str(e)}"
        )


@router.get("/by-questionnaire/{questionnaire_id}", response_model=List[Dict[str, Any]])
async def get_consultations_by_questionnaire(questionnaire_id: str):
    """
    Get all consultations for a specific questionnaire
    """
    try:
        db = get_database()
        consultations = list(
            db.consultations.find({"questionnaire_id": questionnaire_id})
            .sort("created_at", -1)
        )
        
        # Convert ObjectId to string
        for c in consultations:
            c["consultation_id"] = str(c.pop("_id"))
        
        return consultations
        
    except Exception as e:
        print(f"Error fetching consultations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching consultations: {str(e)}"
        )
