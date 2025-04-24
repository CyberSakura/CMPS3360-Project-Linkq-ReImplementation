import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Database Configuration
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "chat_history.db"))

# API Configuration
SPARQL_ENDPOINT = os.getenv("SPARQL_ENDPOINT", "https://query.wikidata.org/sparql")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT", "https://www.wikidata.org/w/api.php")

# API Headers
HEADERS = {
    "User-Agent": os.getenv("USER_AGENT", "LinkQ-Entity-Search/1.0"),
    "Accept": "application/json"
}

# Entity Types Configuration
ENTITY_TYPES = {
    "cat": "Q146",    # Domestic Cat
    "dog": "Q144",    # Domestic Dog
    "city": "Q515",   # Cities
    "country": "Q6256",  # Countries
    "person": "Q5",   # Humans
    "book": "Q571"    # Books
}

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in environment variables")

# Application Configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5001"))

# Frontend Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000") 