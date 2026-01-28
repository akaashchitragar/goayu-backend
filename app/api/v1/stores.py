from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings
from typing import Optional, List, Dict, Any
import googlemaps
import asyncio

router = APIRouter()

# Initialize Google Maps client
_gmaps_client = None

def get_gmaps_client():
    """Get Google Maps client instance (cached)"""
    global _gmaps_client
    if _gmaps_client is None:
        api_key = settings.GOOGLE_MAPS_API_KEY or settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("Google Maps API key not configured. Set GOOGLE_MAPS_API_KEY or ensure GEMINI_API_KEY is enabled for Maps/Places API.")
        _gmaps_client = googlemaps.Client(key=api_key)
    return _gmaps_client


@router.get("/nearby-ayurvedic-stores")
async def get_nearby_ayurvedic_stores(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: int = Query(5000, description="Search radius in meters (default: 5000m = 5km)")
):
    """
    Search for nearby Ayurvedic medical stores and shops using Google Places API
    """
    try:
        gmaps = get_gmaps_client()
        
        # Search for Ayurvedic stores using multiple search terms
        search_queries = [
            "Ayurvedic medicine store",
            "Ayurvedic pharmacy",
            "Ayurvedic shop",
            "Ayurvedic medical store",
            "herbal medicine store",
            "Ayurvedic clinic"
        ]
        
        all_results = []
        seen_place_ids = set()
        
        # Run searches in parallel
        def search_places(query: str):
            """Search for places synchronously"""
            try:
                places_result = gmaps.places_nearby(
                    location=(latitude, longitude),
                    radius=radius,
                    keyword=query,
                    type='pharmacy'  # Focus on pharmacies/medical stores
                )
                return places_result.get('results', [])
            except Exception as e:
                print(f"Error searching for {query}: {e}")
                return []
        
        # Execute searches in parallel using thread pool
        import concurrent.futures
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [loop.run_in_executor(executor, search_places, query) for query in search_queries]
            results_list = await asyncio.gather(*futures)
        
        # Combine and deduplicate results
        for results in results_list:
            for place in results:
                place_id = place.get('place_id')
                if place_id and place_id not in seen_place_ids:
                    seen_place_ids.add(place_id)
                    all_results.append(place)
        
        # If no results with 'pharmacy' type, try broader search
        if not all_results:
            try:
                broader_result = gmaps.places_nearby(
                    location=(latitude, longitude),
                    radius=radius,
                    keyword="Ayurvedic"
                )
                for place in broader_result.get('results', []):
                    place_id = place.get('place_id')
                    if place_id and place_id not in seen_place_ids:
                        seen_place_ids.add(place_id)
                        all_results.append(place)
            except Exception as e:
                print(f"Error in broader search: {e}")
        
        # Get detailed information for each place
        detailed_stores = []
        for place in all_results[:20]:  # Limit to top 20 results
            try:
                place_id = place.get('place_id')
                if not place_id:
                    continue
                
                # Get place details
                details_result = gmaps.place(
                    place_id=place_id,
                    fields=['name', 'formatted_address', 'geometry', 'rating', 'user_ratings_total', 
                           'opening_hours', 'phone_number', 'website', 'photos']
                )
                
                place_details = details_result.get('result', {})
                
                # Calculate distance
                place_location = place.get('geometry', {}).get('location', {})
                place_lat = place_location.get('lat')
                place_lng = place_location.get('lng')
                
                # Simple distance calculation (Haversine formula approximation)
                import math
                lat_diff = math.radians(place_lat - latitude)
                lng_diff = math.radians(place_lng - longitude)
                a = math.sin(lat_diff/2)**2 + math.cos(math.radians(latitude)) * math.cos(math.radians(place_lat)) * math.sin(lng_diff/2)**2
                c = 2 * math.asin(math.sqrt(a))
                distance_km = 6371 * c  # Earth radius in km
                
                store_info = {
                    'place_id': place_id,
                    'name': place_details.get('name', place.get('name', 'Unknown')),
                    'address': place_details.get('formatted_address', place.get('vicinity', 'Address not available')),
                    'latitude': place_lat,
                    'longitude': place_lng,
                    'rating': place_details.get('rating', place.get('rating')),
                    'user_ratings_total': place_details.get('user_ratings_total', place.get('user_ratings_total', 0)),
                    'distance_km': round(distance_km, 2),
                    'phone': place_details.get('formatted_phone_number', place_details.get('international_phone_number')),
                    'website': place_details.get('website'),
                    'opening_hours': place_details.get('opening_hours', {}).get('weekday_text', []),
                    'is_open_now': place_details.get('opening_hours', {}).get('open_now'),
                    'photo_reference': place_details.get('photos', [{}])[0].get('photo_reference') if place_details.get('photos') else None
                }
                
                detailed_stores.append(store_info)
            except Exception as e:
                print(f"Error getting details for place {place.get('place_id')}: {e}")
                continue
        
        # Sort by distance
        detailed_stores.sort(key=lambda x: x['distance_km'])
        
        return {
            "success": True,
            "stores": detailed_stores,
            "count": len(detailed_stores),
            "user_location": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"API configuration error: {str(e)}")
    except Exception as e:
        print(f"Error searching for Ayurvedic stores: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search for stores: {str(e)}")
