from dotenv import load_dotenv
import os

load_dotenv()

NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
NUTRITIONIX_APP_KEY = os.getenv("NUTRITIONIX_APP_KEY")
GROQ_MODEL = "deepseek-r1-distill-llama-70b"
