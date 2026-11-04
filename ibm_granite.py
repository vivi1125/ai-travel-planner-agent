"""
ibm_granite.py
--------------
IBM watsonx.ai client that calls the IBM Granite model.

• When real IBM credentials are present  → calls ibm-watsonx-ai SDK.
• When credentials are missing/demo      → returns clearly labelled
  demo data so the app stays fully usable without API keys.

IBM Granite model used: ibm/granite-3-8b-instruct  (Lite tier — free)
"""

from __future__ import annotations
import textwrap
from config import (
    IBM_CLOUD_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL, WATSONX_MODEL_ID,
    GRANITE_MAX_TOKENS, GRANITE_TEMPERATURE, GRANITE_TOP_P,
    credentials_available, CURRENCY_SYMBOL,
)

# ── Lazy-import the IBM SDK (only needed when credentials are present) ──
def _get_model():
    """Return an initialised WatsonxLLM / ModelInference instance."""
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params

    creds = Credentials(url=WATSONX_URL, api_key=IBM_CLOUD_API_KEY)
    client = APIClient(credentials=creds, project_id=WATSONX_PROJECT_ID)

    model = ModelInference(
        model_id=WATSONX_MODEL_ID,
        api_client=client,
        project_id=WATSONX_PROJECT_ID,
        params={
            Params.MAX_NEW_TOKENS      : GRANITE_MAX_TOKENS,
            Params.TEMPERATURE         : GRANITE_TEMPERATURE,
            Params.TOP_P               : GRANITE_TOP_P,
            Params.REPETITION_PENALTY  : 1.1,
        },
    )
    return model


# ── Prompt builder (Granite instruct format) ─────────────────
def _build_prompt(system: str, user: str) -> str:
    return f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"


# ── System prompt ─────────────────────────────────────────────
_SYSTEM = (
    "You are an expert AI Travel Planner specialised in Indian and international travel. "
    "You give practical, culturally aware, budget-conscious travel advice. "
    "Always respond in clear, well-structured markdown with headings and bullet points. "
    "Tailor every response to the user's budget (in INR), duration, and interests."
)


# ── Public API ────────────────────────────────────────────────

def generate(user_prompt: str) -> tuple[str, bool]:
    """
    Call IBM Granite and return (response_text, is_demo).

    is_demo=True  → response came from the built-in demo fallback.
    is_demo=False → response came from the real IBM Granite model.
    """
    if not credentials_available():
        return _demo_response(user_prompt), True

    try:
        model  = _get_model()
        prompt = _build_prompt(_SYSTEM, user_prompt)
        result = model.generate_text(prompt=prompt)
        # SDK may return str or dict depending on version
        if isinstance(result, dict):
            text = result.get("results", [{}])[0].get("generated_text", "")
        else:
            text = str(result)
        return text.strip(), False
    except Exception as exc:
        # Surface the error clearly but still return demo data
        error_note = f"\n\n> ⚠️ **IBM Granite API error:** `{exc}`  \n> Showing demo data instead.\n\n"
        return error_note + _demo_response(user_prompt), True


# ── Demo fallback ─────────────────────────────────────────────
_DEMO_BANNER = (
    "> 🟡 **DEMO MODE** — IBM API credentials are not configured.  \n"
    "> The content below is illustrative sample data, **not** a real AI response.  \n"
    "> Add your IBM Cloud API Key and watsonx Project ID to `.env` to enable live AI.\n\n"
)


def _demo_response(prompt: str) -> str:
    """Return topic-matched demo text based on keywords in the prompt."""
    p = prompt.lower()

    if "itinerary" in p or "day" in p:
        return _DEMO_BANNER + _demo_itinerary(prompt)
    if "budget" in p or "breakdown" in p or "cost" in p:
        return _DEMO_BANNER + _demo_budget(prompt)
    if "transport" in p or "accommodation" in p or "hotel" in p:
        return _DEMO_BANNER + _demo_transport_stay(prompt)
    if "tip" in p or "pack" in p:
        return _DEMO_BANNER + _demo_tips(prompt)
    return _DEMO_BANNER + _demo_full_plan(prompt)


def _demo_itinerary(prompt: str) -> str:
    return textwrap.dedent("""\
        ## 📅 Sample Day-wise Itinerary

        ### Day 1 — Arrival & Orientation
        - **Morning:** Arrive at destination, check into hotel, freshen up
        - **Afternoon:** Explore the city centre, visit the main market
        - **Evening:** Welcome dinner at a popular local restaurant

        ### Day 2 — Cultural Highlights
        - **Morning:** Visit the iconic heritage monument (open 9 AM – 5 PM, ~₹50 entry)
        - **Afternoon:** Guided walking tour of the old town (~₹300/person)
        - **Evening:** Street food walk; try local specialities

        ### Day 3 — Nature & Adventure
        - **Morning:** Early morning trek or nature walk (guide: ~₹500)
        - **Afternoon:** Picnic lunch, visit a scenic viewpoint
        - **Evening:** Bonfire / local cultural performance

        ### Day 4 — Leisure & Shopping
        - **Morning:** Relaxed breakfast, visit local handicraft market
        - **Afternoon:** Free time for shopping / spa
        - **Evening:** Rooftop dinner with a city view

        ### Day 5 — Departure
        - **Morning:** Final sightseeing or café hopping
        - **Afternoon:** Head to airport/station; depart

        > *Timings and costs are approximate sample values.*
    """)


def _demo_budget(prompt: str) -> str:
    return textwrap.dedent(f"""\
        ## {CURRENCY_SYMBOL} Sample Budget Breakdown

        | Category | Estimated Cost (per person) |
        |---|---|
        | ✈️ Transportation (to/from) | {CURRENCY_SYMBOL}8,000 – {CURRENCY_SYMBOL}15,000 |
        | 🚌 Local Transport | {CURRENCY_SYMBOL}1,500 – {CURRENCY_SYMBOL}3,000 |
        | 🏨 Accommodation (4 nights) | {CURRENCY_SYMBOL}6,000 – {CURRENCY_SYMBOL}20,000 |
        | 🍽️ Food & Dining | {CURRENCY_SYMBOL}3,000 – {CURRENCY_SYMBOL}6,000 |
        | 🎟️ Activities & Entries | {CURRENCY_SYMBOL}2,000 – {CURRENCY_SYMBOL}5,000 |
        | 🛍️ Shopping & Souvenirs | {CURRENCY_SYMBOL}1,000 – {CURRENCY_SYMBOL}3,000 |
        | 🩺 Misc / Emergency Buffer | {CURRENCY_SYMBOL}1,000 – {CURRENCY_SYMBOL}2,000 |
        | **Total (approx.)** | **{CURRENCY_SYMBOL}22,500 – {CURRENCY_SYMBOL}54,000** |

        ### 💡 Money-Saving Tips
        - Book transport 3–4 weeks in advance for 20–30% savings
        - Opt for local dhabas/street food over tourist restaurants
        - Travel off-season (shoulder months) for 40% cheaper hotels
        - Use city day-passes for local transport

        > *Values are sample estimates. Your actual spend will vary.*
    """)


def _demo_transport_stay(prompt: str) -> str:
    return textwrap.dedent(f"""\
        ## ✈️ Transport Options (Sample)

        | Mode | Approx. Cost | Duration | Notes |
        |---|---|---|---|
        | Flight | {CURRENCY_SYMBOL}5,000–{CURRENCY_SYMBOL}12,000 | 1–3 hrs | Book on MakeMyTrip / Ixigo |
        | Train (AC 2-tier) | {CURRENCY_SYMBOL}800–{CURRENCY_SYMBOL}2,500 | 6–14 hrs | Best value for overnight journeys |
        | Bus (Volvo) | {CURRENCY_SYMBOL}400–{CURRENCY_SYMBOL}1,200 | 8–16 hrs | KSRTC / MSRTC / private operators |
        | Self-Drive | {CURRENCY_SYMBOL}1,500–{CURRENCY_SYMBOL}3,000/day | Flexible | Zoomcar / Savaari |

        ## 🏨 Accommodation Options (Sample)

        | Type | Price/Night | Best For |
        |---|---|---|
        | Hostel / Dorm | {CURRENCY_SYMBOL}500–{CURRENCY_SYMBOL}1,200 | Solo backpackers |
        | Budget hotel | {CURRENCY_SYMBOL}1,200–{CURRENCY_SYMBOL}2,500 | Budget travellers |
        | Mid-range hotel | {CURRENCY_SYMBOL}2,500–{CURRENCY_SYMBOL}5,000 | Couples & families |
        | Boutique / Heritage | {CURRENCY_SYMBOL}5,000–{CURRENCY_SYMBOL}10,000 | Unique experience seekers |
        | Luxury resort | {CURRENCY_SYMBOL}10,000+ | Luxury travellers |

        > Book via Booking.com, MakeMyTrip, Goibibo, or Airbnb.
    """)


def _demo_tips(prompt: str) -> str:
    return textwrap.dedent("""\
        ## 🧳 Packing Checklist (Sample)

        **Documents**
        - ✅ Govt. ID / Passport + photocopies
        - ✅ Travel insurance documents
        - ✅ Hotel booking confirmations

        **Clothing**
        - ✅ Comfortable walking shoes / trekking sandals
        - ✅ Lightweight, breathable clothes (2–3 pairs per person)
        - ✅ Light jacket / shawl (for evenings)
        - ✅ Rain poncho / compact umbrella

        **Health & Safety**
        - ✅ Basic first-aid kit (ORS, antacids, Band-Aids)
        - ✅ Personal prescription medicines
        - ✅ Sunscreen SPF 50+, insect repellent

        **Tech & Gadgets**
        - ✅ Universal power bank (20,000 mAh)
        - ✅ Local SIM card / travel data eSIM
        - ✅ Offline maps downloaded (Google Maps)

        ## 💡 Travel Tips (Sample)
        - Always carry {CURRENCY_SYMBOL}500–{CURRENCY_SYMBOL}1,000 in cash for local vendors
        - Negotiate auto/taxi fares before boarding in non-meter cities
        - Respect local customs — dress modestly at religious sites
        - Stay hydrated; carry a reusable water bottle
        - Share your itinerary with a trusted contact back home
    """)


def _demo_full_plan(prompt: str) -> str:
    return (
        "## 🌍 Sample Travel Plan\n\n"
        + _demo_itinerary(prompt) + "\n\n"
        + _demo_budget(prompt) + "\n\n"
        + _demo_transport_stay(prompt) + "\n\n"
        + _demo_tips(prompt)
    )
