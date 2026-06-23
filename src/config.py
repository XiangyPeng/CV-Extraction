import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv() # load evironment variables from .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///cv_extraction.db")
JSON_OUTPUT_DIR = os.getenv("JSON_OUTPUT_DIR", "output")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
