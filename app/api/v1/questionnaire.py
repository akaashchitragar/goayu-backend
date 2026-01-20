from fastapi import APIRouter, HTTPException, status
from app.models.questionnaire import QuestionnaireSubmission, QuestionnaireResponse, ConstitutionalAnalysis
from app.services.ayurveda_service import AyurvedaService
from app.services.user_service import UserService
from app.core.database import get_database
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any


router = APIRouter()

def get_user_service():
    return UserService()


@router.post("/submit", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def submit_questionnaire(submission: QuestionnaireSubmission):
    """
    Submit questionnaire responses and get constitutional analysis
    """
    try:
        # Calculate constitutional analysis
        ayurveda_service = AyurvedaService()
        constitutional_analysis = ayurveda_service.calculate_dosha_scores(submission.responses)
        
        # Prepare document for MongoDB
        questionnaire_doc = {
            "user_id": submission.user_id,
            "responses": submission.responses.model_dump(),
            "constitutional_analysis": constitutional_analysis.model_dump(),
            "submitted_at": submission.submitted_at,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save to MongoDB
        db = get_database()
        result = db.questionnaires.insert_one(questionnaire_doc)
        
        questionnaire_id = str(result.inserted_id)
        
        # Add questionnaire_id field to the document for easier querying
        db.questionnaires.update_one(
            {"_id": result.inserted_id},
            {"$set": {"questionnaire_id": questionnaire_id}}
        )
        
        # Link questionnaire to user if user_id provided
        if submission.user_id:
            user_service = get_user_service()
            await user_service.add_questionnaire_to_user(submission.user_id, questionnaire_id)
            await user_service.log_activity(
                user_id=submission.user_id,
                activity_type="questionnaire_submitted",
                activity_data={"questionnaire_id": questionnaire_id}
            )
        
        # Return response with questionnaire ID and analysis
        return {
            "questionnaire_id": questionnaire_id,
            "constitutional_analysis": constitutional_analysis.model_dump(),
            "message": "Questionnaire submitted successfully"
        }
        
    except Exception as e:
        print(f"Error submitting questionnaire: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting questionnaire: {str(e)}"
        )


@router.get("/{questionnaire_id}", response_model=Dict[str, Any])
async def get_questionnaire(questionnaire_id: str):
    """
    Get questionnaire by ID
    """
    try:
        db = get_database()
        questionnaire = db.questionnaires.find_one({"_id": ObjectId(questionnaire_id)})
        
        if not questionnaire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Questionnaire not found"
            )
        
        # Convert ObjectId to string
        questionnaire["_id"] = str(questionnaire["_id"])
        
        return questionnaire
        
    except Exception as e:
        print(f"Error fetching questionnaire: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching questionnaire: {str(e)}"
        )


@router.get("/", response_model=List[Dict[str, Any]])
async def list_questionnaires(skip: int = 0, limit: int = 10):
    """
    List all questionnaires (for testing purposes)
    """
    try:
        db = get_database()
        questionnaires = list(
            db.questionnaires.find()
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        
        # Convert ObjectId to string
        for q in questionnaires:
            q["_id"] = str(q["_id"])
        
        return questionnaires
        
    except Exception as e:
        print(f"Error listing questionnaires: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing questionnaires: {str(e)}"
        )
