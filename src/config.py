import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "")
RUNPOD_BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}"

BUCKET_ENDPOINT_URL = os.getenv("BUCKET_ENDPOINT_URL", "")
BUCKET_ACCESS_KEY_ID = os.getenv("BUCKET_ACCESS_KEY_ID", "")
BUCKET_SECRET_ACCESS_KEY = os.getenv("BUCKET_SECRET_ACCESS_KEY", "")

COMFY_ORG_API_KEY = os.getenv("COMFY_ORG_API_KEY", "")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "jobs.db")
WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "..", "workflows")
MODELS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "models_config.json")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

TIMEOUT_RUNSYNC = 300
