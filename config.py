import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

if not DISCORD_TOKEN or not OLLAMA_API_KEY:
    raise ValueError("Faltan DISCORD_TOKEN o OLLAMA_API_KEY en el archivo .env")