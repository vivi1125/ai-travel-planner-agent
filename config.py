"""
config.py
---------
Loads environment variables and exposes typed constants used across the app.
All IBM credentials are read from the .env file — never hardcoded.
"""

import os
from dotenv import load_dotenv

# Load .env (silently ignored if the file doesn't exist)
load_dotenv()


# ── IBM watsonx.ai credentials ────────────────────────────────
IBM_CLOUD_API_KEY: str   = os.getenv("IBM_CLOUD_API_KEY", "")
WATSONX_PROJECT_ID: str  = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL: str         = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_MODEL_ID: str    = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")

# ── Granite generation parameters ────────────────────────────
GRANITE_MAX_TOKENS: int      = int(os.getenv("GRANITE_MAX_TOKENS", "1200"))
GRANITE_TEMPERATURE: float   = float(os.getenv("GRANITE_TEMPERATURE", "0.7"))
GRANITE_TOP_P: float         = float(os.getenv("GRANITE_TOP_P", "0.9"))

# ── Are real IBM credentials present? ────────────────────────
def credentials_available() -> bool:
    """Return True only when both required IBM fields are non-placeholder values."""
    placeholder = {"your_ibm_cloud_api_key_here", "your_watsonx_project_id_here", ""}
    return (
        IBM_CLOUD_API_KEY  not in placeholder and
        WATSONX_PROJECT_ID not in placeholder
    )


# ── Travel interest options shown in the UI ───────────────────
TRAVEL_INTERESTS = [
    "Adventure & Trekking",
    "Nature & Wildlife",
    "Beaches & Water Sports",
    "Historical & Heritage",
    "Food & Culinary",
    "Spiritual & Pilgrimage",
    "Luxury & Wellness",
    "Backpacking & Budget",
    "Family & Kids",
    "Honeymoon & Romance",
    "Shopping & City Life",
    "Art, Music & Culture",
]

# ── Transport modes ───────────────────────────────────────────
TRANSPORT_MODES = ["Flight", "Train", "Bus", "Self-Drive / Car Rental", "Cruise / Boat", "Mixed"]

# ── Accommodation styles ──────────────────────────────────────
ACCOMMODATION_STYLES = ["Budget (Hostel / Guesthouse)", "Mid-range Hotel", "Boutique Hotel",
                        "Luxury Resort", "Homestay / Airbnb", "Camping / Glamping"]

# ── Currency ──────────────────────────────────────────────────
CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"
