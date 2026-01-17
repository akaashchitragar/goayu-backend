from google import genai
from google.genai import types
from app.core.config import settings
from app.models.questionnaire import ConstitutionalAnalysis
from app.models.consultation import ConsultationResponse, Remedy, ScriptureReference
from typing import List, Dict, Any
import json
import re


class AIService:
    """Service for Google Gemini AI integration"""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # Using Gemini 3 Pro Preview - Latest and most advanced model
        # Alternative options: 'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.0-flash-exp'
        self.model = 'gemini-3-pro-preview'
    
    async def generate_consultation(
        self,
        symptoms: str,
        constitutional_analysis: ConstitutionalAnalysis,
        additional_notes: str = None
    ) -> Dict[str, Any]:
        """
        Generate personalized Ayurvedic consultation using Gemini AI
        """
        
        prompt = self._build_consultation_prompt(
            symptoms, constitutional_analysis, additional_notes
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            consultation_data = self._parse_ai_response(response.text)
            return consultation_data
        except Exception as e:
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
