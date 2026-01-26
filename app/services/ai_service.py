from google import genai
from google.genai import types
from app.core.config import settings
from app.models.questionnaire import ConstitutionalAnalysis
from app.models.consultation import ConsultationResponse, Remedy, ScriptureReference
from app.core.database import get_database
from typing import List, Dict, Any
from datetime import datetime
import json
import re


class AIService:
    """Service for Google Gemini AI integration"""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # Using Gemini 3 Pro Preview - Latest and most advanced model
        # Alternative options: 'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.0-flash-exp'
        self.model = 'gemini-3-pro-preview'
    
    def _log_ai_usage(
        self,
        model: str,
        operation: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        response_time_ms: int,
        success: bool,
        error_message: str = None,
        user_id: str = None,
        user_email: str = None,
        user_name: str = None,
        consultation_id: str = None,
        symptoms: str = None
    ):
        """Log AI usage to database for tracking"""
        try:
            db = get_database()
            if db is None:
                print("Database not available for AI usage logging")
                return
            
            usage_doc = {
                "model": model,
                "operation": operation,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "response_time_ms": response_time_ms,
                "success": success,
                "error_message": error_message,
                "user_id": user_id,
                "user_email": user_email,
                "user_name": user_name,
                "consultation_id": consultation_id,
                "symptoms": symptoms[:200] if symptoms else None,  # Store first 200 chars of symptoms
                "created_at": datetime.utcnow()
            }
            
            result = db.ai_usage.insert_one(usage_doc)
            print(f"AI usage logged: {result.inserted_id}")
        except Exception as e:
            print(f"Error logging AI usage: {e}")
    
    async def generate_consultation(
        self,
        symptoms: str,
        constitutional_analysis: ConstitutionalAnalysis,
        additional_notes: str = None,
        user_id: str = None,
        user_email: str = None,
        user_name: str = None,
        consultation_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate personalized Ayurvedic consultation using Gemini AI
        """
        
        prompt = self._build_consultation_prompt(
            symptoms, constitutional_analysis, additional_notes
        )
        
        import time
        start_time = time.time()
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Extract token usage from response metadata
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                completion_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                total_tokens = getattr(usage, 'total_token_count', 0) or (prompt_tokens + completion_tokens)
            
            # Estimate tokens if not available (rough estimate: 4 chars per token)
            if total_tokens == 0:
                prompt_tokens = len(prompt) // 4
                completion_tokens = len(response.text) // 4 if response.text else 0
                total_tokens = prompt_tokens + completion_tokens
            
            # Log successful AI usage
            self._log_ai_usage(
                model=self.model,
                operation="consultation",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_time_ms=response_time_ms,
                success=True,
                user_id=user_id,
                user_email=user_email,
                user_name=user_name,
                consultation_id=consultation_id,
                symptoms=symptoms
            )
            
            consultation_data = self._parse_ai_response(response.text)
            return consultation_data
        except Exception as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Log failed AI usage
            self._log_ai_usage(
                model=self.model,
                operation="consultation",
                prompt_tokens=len(prompt) // 4,
                completion_tokens=0,
                total_tokens=len(prompt) // 4,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e),
                user_id=user_id,
                user_email=user_email,
                user_name=user_name,
                consultation_id=consultation_id,
                symptoms=symptoms
            )
            
            print(f"Error generating consultation: {e}")
            raise
    
    def _build_consultation_prompt(
        self,
        symptoms: str,
        constitutional_analysis: ConstitutionalAnalysis,
        additional_notes: str = None
    ) -> str:
        """Build the prompt for Gemini AI"""
        
        prompt = f"""You are an expert Ayurvedic practitioner with deep knowledge of classical Ayurvedic texts including Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya, and other authoritative scriptures.

PATIENT CONSTITUTIONAL PROFILE (Prakruti):
- Constitutional Type: {constitutional_analysis.prakruti_type}
- Dominant Dosha: {constitutional_analysis.dominant_dosha}
- Dosha Distribution: Vata {constitutional_analysis.vata_score}%, Pitta {constitutional_analysis.pitta_score}%, Kapha {constitutional_analysis.kapha_score}%
- Analysis: {constitutional_analysis.analysis_summary}

CURRENT SYMPTOMS (Vikriti):
{symptoms}

"""
        
        if additional_notes:
            prompt += f"""ADDITIONAL NOTES:
{additional_notes}

"""
        
        prompt += """TASK:
Provide a comprehensive Ayurvedic consultation with personalized home remedies based on the patient's unique constitution and current symptoms. Your response must be in the following JSON format:

{
  "dosha_analysis": "Detailed analysis of current dosha imbalance based on symptoms and constitution",
  "remedies": [
    {
      "name": "Remedy name",
      "description": "Brief description of the remedy and its benefits",
      "preparation_method": "Step-by-step preparation instructions",
      "dosage": "Exact dosage information",
      "timing": "When to take (morning/evening/with meals, etc.)",
      "duration": "How long to continue the remedy",
      "precautions": "Any precautions or contraindications",
      "ingredients": ["ingredient1", "ingredient2", "ingredient3"]
    }
  ],
  "scripture_references": [
    {
      "text_name": "Name of Ayurvedic text",
      "chapter": "Chapter name or number",
      "verse": "Verse number or range",
      "content": "Brief explanation of what the scripture says about this condition"
    }
  ],
  "lifestyle_recommendations": [
    "Specific lifestyle recommendation 1",
    "Specific lifestyle recommendation 2",
    "Specific lifestyle recommendation 3"
  ],
  "dietary_recommendations": [
    "Specific dietary recommendation 1",
    "Specific dietary recommendation 2",
    "Specific dietary recommendation 3"
  ],
  "general_advice": "Overall wellness advice and what to expect from the treatment"
}

IMPORTANT GUIDELINES:
1. Tailor ALL remedies specifically to the patient's {constitutional_analysis.prakruti_type} constitution
2. Provide 3-5 practical home remedies using commonly available ingredients
3. Reference authentic Ayurvedic texts (Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya, etc.)
4. Consider the dominant dosha ({constitutional_analysis.dominant_dosha}) in all recommendations
5. Provide clear, actionable instructions that can be followed at home
6. Include both immediate relief measures and long-term constitutional balancing
7. Ensure all recommendations are safe and based on classical Ayurvedic principles
8. Return ONLY valid JSON, no additional text before or after

Generate the consultation now:"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response and extract structured data"""
        
        try:
            # Try to extract JSON from the response
            # Remove markdown code blocks if present
            json_text = response_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            
            json_text = json_text.strip()
            
            # Parse JSON
            consultation_data = json.loads(json_text)
            
            # Validate required fields
            required_fields = [
                "dosha_analysis", "remedies", "scripture_references",
                "lifestyle_recommendations", "dietary_recommendations", "general_advice"
            ]
            
            for field in required_fields:
                if field not in consultation_data:
                    consultation_data[field] = [] if field != "dosha_analysis" and field != "general_advice" else ""
            
            return consultation_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response text: {response_text[:500]}")
            
            # Return a fallback structure
            return {
                "dosha_analysis": "Unable to parse AI response. Please try again.",
                "remedies": [],
                "scripture_references": [],
                "lifestyle_recommendations": [],
                "dietary_recommendations": [],
                "general_advice": response_text[:500]
            }
    
    async def generate_daily_tip(self, user_dosha: str = None) -> Dict[str, Any]:
        """
        Generate a personalized daily Ayurvedic wellness tip using AI
        """
        import time
        start_time = time.time()
        
        # Get current date info for variety
        today = datetime.utcnow()
        day_of_year = today.timetuple().tm_yday
        weekday = today.strftime("%A")
        month = today.strftime("%B")
        
        dosha_context = ""
        if user_dosha:
            dosha_context = f"\nThe user has a {user_dosha} dominant constitution. Tailor the tip to be especially beneficial for {user_dosha} types."
        
        prompt = f"""You are an expert Ayurvedic wellness advisor. Generate a unique, practical daily wellness tip based on Ayurvedic principles.

Context:
- Today is {weekday}, day {day_of_year} of the year
- Current month: {month}
- Season consideration: Adjust advice based on typical seasonal patterns{dosha_context}

Generate a fresh, actionable wellness tip that covers ONE of these categories (rotate based on the day):
- Morning routine (Dinacharya)
- Diet and nutrition (Ahara)
- Exercise and yoga (Vyayama)
- Sleep hygiene (Nidra)
- Mental wellness (Manas)
- Seasonal living (Ritucharya)
- Self-care practices (Svasthavritta)
- Digestive health (Agni)
- Detox and cleansing (Shodhana)
- Herbal remedies (Aushadhi)

Return ONLY valid JSON in this exact format:
{{
  "category": "Category name",
  "title": "Short catchy title (3-5 words)",
  "tip": "The main tip content (2-3 sentences, practical and actionable)",
  "benefit": "Brief explanation of the benefit (1 sentence)",
  "sanskrit_term": "Relevant Sanskrit term if applicable",
  "best_time": "Best time to practice this (e.g., morning, evening, before meals)"
}}

Make the tip unique, specific, and immediately actionable. Avoid generic advice."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Log AI usage
            prompt_tokens = len(prompt) // 4
            completion_tokens = len(response.text) // 4 if response.text else 0
            
            self._log_ai_usage(
                model=self.model,
                operation="daily_tip",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                response_time_ms=response_time_ms,
                success=True
            )
            
            # Parse response
            json_text = response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            
            tip_data = json.loads(json_text.strip())
            tip_data["generated_at"] = today.isoformat()
            tip_data["day_of_year"] = day_of_year
            
            return tip_data
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            self._log_ai_usage(
                model=self.model,
                operation="daily_tip",
                prompt_tokens=len(prompt) // 4,
                completion_tokens=0,
                total_tokens=len(prompt) // 4,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )
            
            print(f"Error generating daily tip: {e}")
            # Return fallback tip
            return {
                "category": "General Wellness",
                "title": "Stay Hydrated",
                "tip": "Start your day with a glass of warm water to stimulate digestion and flush toxins. Add a squeeze of lemon for extra cleansing benefits.",
                "benefit": "Improves digestion and helps maintain dosha balance throughout the day.",
                "sanskrit_term": "Ushnodaka",
                "best_time": "First thing in the morning",
                "generated_at": today.isoformat(),
                "day_of_year": day_of_year,
                "is_fallback": True
            }