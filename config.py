import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
KILO_PROMPT_API_KEY = os.getenv("KILO_PROMPT_API_KEY", "")
KILO_PROMPT_MODEL = os.getenv("KILO_PROMPT_MODEL", "nex-agi/nex-n2.5-pro:free")
KILO_VISION_API_KEY = os.getenv("KILO_VISION_API_KEY", "")
KILO_VISION_MODEL = os.getenv("KILO_VISION_MODEL", "dots-studio/dots-3-note-preview:free")
KIE_AI_API_KEY = os.getenv("KIE_AI_API_KEY", "")

# Gateway base URL for Kilo Code
KILO_BASE_URL = "https://api.kilo.ai/api/gateway"

# Storage Directories
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
IMAGES_DIR = OUTPUTS_DIR / "images"
VIDEOS_DIR = OUTPUTS_DIR / "videos"

DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# SQLite Database Path
DATABASE_PATH = DATA_DIR / "ugc_ads.db"

# Polling Interval
WORKER_POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "10"))

# Models
GEMINI_VEO_MODEL = "models/veo-3.1-generate-preview"
GEMINI_VEO_FAST_MODEL = "models/veo-3.1-fast-generate-preview"
GEMINI_IMAGE_MODEL = "models/nano-banana-pro-preview"
GEMINI_FALLBACK_IMAGE_MODEL = "models/gemini-2.5-flash-image"
