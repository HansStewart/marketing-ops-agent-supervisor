import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.hubspot_access_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
        self.app_env = os.getenv("APP_ENV", "local")

settings = Settings()