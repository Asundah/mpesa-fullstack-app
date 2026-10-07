import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    CONSUMER_KEY = os.getenv("CONSUMER_KEY")
    CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
    SHORTCODE = os.getenv("SHORTCODE", "174379")
    PASSKEY = os.getenv("PASSKEY")
    CALLBACK_URL = os.getenv("CALLBACK_URL", "http://localhost:8000/api/callback")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "sandbox")