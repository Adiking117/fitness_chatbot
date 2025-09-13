from langchain_core.tools import tool
from typing import Optional
import requests
from config.env import NUTRITIONIX_APP_ID, NUTRITIONIX_APP_KEY

# Shared headers for Nutritionix API
HEADERS = {
    "Content-Type": "application/json",
    "x-app-id": NUTRITIONIX_APP_ID,
    "x-app-key": NUTRITIONIX_APP_KEY
}

NUTRIENTS_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"
EXERCISE_URL = "https://trackapi.nutritionix.com/v2/natural/exercise"


@tool
def nutritionix_natural_nutrients(query: str) -> list:
    """
    Get nutrition information for a natural language food query.

    This tool calls Nutritionix's `/natural/nutrients` endpoint and returns
    only the key nutrient fields up to `nf_p` (phosphorus) to minimize payload size.

    Args:
        query (str): A natural language description of the food(s).
                     Example: "2 eggs and toast"

    Returns:
        list: A list of dictionaries containing nutrient information for each food item.
    """
    try:
        resp = requests.post(NUTRIENTS_URL, headers=HEADERS, json={"query": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return [
            {
                "food_name": item.get("food_name"),
                "brand_name": item.get("brand_name"),
                "serving_qty": item.get("serving_qty"),
                "serving_unit": item.get("serving_unit"),
                "serving_weight_grams": item.get("serving_weight_grams"),
                "nf_calories": item.get("nf_calories"),
                "nf_total_fat": item.get("nf_total_fat"),
                "nf_saturated_fat": item.get("nf_saturated_fat"),
                "nf_cholesterol": item.get("nf_cholesterol"),
                "nf_sodium": item.get("nf_sodium"),
                "nf_total_carbohydrate": item.get("nf_total_carbohydrate"),
                "nf_dietary_fiber": item.get("nf_dietary_fiber"),
                "nf_sugars": item.get("nf_sugars"),
                "nf_protein": item.get("nf_protein"),
                "nf_potassium": item.get("nf_potassium"),
                "nf_p": item.get("nf_p")
            }
            for item in data.get("foods", [])
        ]

    except requests.exceptions.RequestException as e:
        return {"error": str(e)} # type: ignore


@tool
def nutritionix_natural_exercise(
    query: str,
    gender: Optional[str] = None,
    weight_kg: Optional[float] = None,
    height_cm: Optional[float] = None,
    age: Optional[int] = None
) -> list:
    """
    Estimate calories burned for exercises described in natural language.

    This tool calls Nutritionix's `/natural/exercise` endpoint and can optionally
    include demographic data for more accurate calorie burn estimates.

    Args:
        query (str): Exercise description in natural language.
                     Example: "ran for 1 hour"
        gender (Optional[str]): "male" or "female" (optional)
        weight_kg (Optional[float]): Weight in kilograms (optional)
        height_cm (Optional[float]): Height in centimeters (optional)
        age (Optional[int]): Age in years (optional)

    Returns:
        list: A list of dictionaries containing exercise details, duration, MET, and calories burned.
    """
    payload = {"query": query}
    if gender:
        payload["gender"] = gender
    if weight_kg:
        payload["weight_kg"] = weight_kg # type: ignore
    if height_cm:
        payload["height_cm"] = height_cm # type: ignore
    if age:
        payload["age"] = age # type: ignore

    try:
        resp = requests.post(EXERCISE_URL, headers=HEADERS, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return [
            {
                "name": ex.get("name"),
                "user_input": ex.get("user_input"),
                "duration_min": ex.get("duration_min"),
                "met": ex.get("met"),
                "calories_burned": ex.get("nf_calories"),
                "image": ex.get("photo", {}).get("thumb")
            }
            for ex in data.get("exercises", [])
        ]

    except requests.exceptions.RequestException as e:
        return {"error": str(e)} # type: ignore
