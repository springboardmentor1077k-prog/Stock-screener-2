from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DATABASE_URL = "sqlite:///Database/stock_database.db"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODEL_NAME = "llama-3.1-8b-instant"

settings = Settings()