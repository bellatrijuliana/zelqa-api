import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

    GROQ_MODEL = 'llama-3.3-70b-versatile'
    LLM_TIMEOUT = 60

    RISK_THRESHOLD = {
        'critical': 20,
        'high': 12,
        'medium': 6,
    }

    MAX_GENERATED_CASES = 15