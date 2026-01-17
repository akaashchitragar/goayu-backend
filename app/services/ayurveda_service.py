from app.models.questionnaire import QuestionnaireResponse, ConstitutionalAnalysis


class AyurvedaService:
    """Service for Ayurvedic constitutional analysis"""
    
    @staticmethod
    def calculate_dosha_scores(responses: QuestionnaireResponse) -> ConstitutionalAnalysis:
        """
        Calculate Vata, Pitta, Kapha scores based on questionnaire responses
        
        Scoring system:
        - Each answer contributes to one or more doshas
        - Scores are normalized to percentages
        """
        vata_score = 0
        pitta_score = 0
        kapha_score = 0
        
        # Body Frame scoring
        if responses.body_frame == "small_thin":
            vata_score += 2
        elif responses.body_frame == "medium_build":
            pitta_score += 2
        elif responses.body_frame == "large_heavyset":
            kapha_score += 2
        
        # Skin Type scoring
        if responses.skin_type == "usually_dry":
            vata_score += 2
        elif responses.skin_type == "usually_oily":
            pitta_score += 1
            kapha_score += 1
        elif responses.skin_type == "balanced":
            pitta_score += 1
        
        # Hair Type scoring
        if responses.hair_type == "thin_dry":
            vata_score += 2
        elif responses.hair_type == "thick_oily":
            kapha_score += 2
        elif responses.hair_type == "balanced":
            pitta_score += 2
        
        # Temperature Regulation scoring
        if responses.temperature_regulation == "cold_extremities":
            vata_score += 2
        elif responses.temperature_regulation == "warm_sweaty":
            pitta_score += 2
        elif responses.temperature_regulation == "balanced":
            kapha_score += 1
            pitta_score += 1
        
        # Appetite & Digestion scoring
        if responses.appetite_digestion == "unpredictable":
            vata_score += 2
        elif responses.appetite_digestion == "strong_consistent":
            pitta_score += 2
        elif responses.appetite_digestion == "moderate_steady":
            kapha_score += 2
        
        # Sleep Patterns scoring
        if responses.sleep_patterns == "difficulty_sleeping":
            vata_score += 2
        elif responses.sleep_patterns == "sleep_well":
            pitta_score += 2
        elif responses.sleep_patterns == "deep_sleep_refreshed":
            kapha_score += 2
        
        # Mental & Emotional Tendencies scoring
        if responses.mental_emotional_tendencies == "anxious":
            vata_score += 2
        elif responses.mental_emotional_tendencies == "irritable":
            pitta_score += 2
        elif responses.mental_emotional_tendencies == "calm_composed":
            kapha_score += 2
        
        # Digestive Health scoring
        if responses.digestive_health == "gas_bloating":
            vata_score += 2
        elif responses.digestive_health == "strong_digestion":
            pitta_score += 2
        elif responses.digestive_health == "slow_digestion":
            kapha_score += 2
        
        # Stress Response scoring
        if responses.stress_response == "anxious_overwhelmed":
            vata_score += 2
        elif responses.stress_response == "angry_frustrated":
            pitta_score += 2
        elif responses.stress_response == "withdraw_calm":
            kapha_score += 2
        
        # Normalize scores to percentages
        total_score = vata_score + pitta_score + kapha_score
        vata_percentage = (vata_score / total_score) * 100
        pitta_percentage = (pitta_score / total_score) * 100
        kapha_percentage = (kapha_score / total_score) * 100
        
        # Determine dominant and secondary doshas
        scores = {
            "Vata": vata_percentage,
            "Pitta": pitta_percentage,
            "Kapha": kapha_percentage
        }
        sorted_doshas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        dominant_dosha = sorted_doshas[0][0]
        secondary_dosha = sorted_doshas[1][0] if sorted_doshas[1][1] > 25 else None
        
        # Determine Prakruti type
        if secondary_dosha and sorted_doshas[0][1] - sorted_doshas[1][1] < 15:
            prakruti_type = f"{dominant_dosha}-{secondary_dosha}"
        else:
            prakruti_type = dominant_dosha
        
        # Generate analysis summary
        analysis_summary = AyurvedaService._generate_analysis_summary(
            prakruti_type, vata_percentage, pitta_percentage, kapha_percentage
        )
        
        return ConstitutionalAnalysis(
            vata_score=round(vata_percentage, 2),
            pitta_score=round(pitta_percentage, 2),
            kapha_score=round(kapha_percentage, 2),
            dominant_dosha=dominant_dosha,
            secondary_dosha=secondary_dosha,
            prakruti_type=prakruti_type,
            analysis_summary=analysis_summary
        )
    
    @staticmethod
    def _generate_analysis_summary(prakruti_type: str, vata: float, pitta: float, kapha: float) -> str:
        """Generate a human-readable analysis summary"""
        summary = f"Your constitutional type (Prakruti) is {prakruti_type}. "
        summary += f"Dosha distribution: Vata {vata:.1f}%, Pitta {pitta:.1f}%, Kapha {kapha:.1f}%. "
        
        if "Vata" in prakruti_type:
            summary += "Vata dominance indicates a light, quick, and creative nature. You may be prone to dryness, coldness, and irregularity. "
        if "Pitta" in prakruti_type:
            summary += "Pitta dominance indicates a sharp, focused, and intense nature. You may be prone to heat, inflammation, and intensity. "
        if "Kapha" in prakruti_type:
            summary += "Kapha dominance indicates a stable, grounded, and nurturing nature. You may be prone to heaviness, congestion, and slowness. "
        
        return summary.strip()
