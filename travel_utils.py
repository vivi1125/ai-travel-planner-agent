"""
travel_utils.py
---------------
Pure-Python helper functions for:
  • Building prompts sent to IBM Granite
  • Estimating a budget breakdown (local computation, no API)
  • Generating packing suggestions and travel tips (rule-based)
  • Input validation

No IBM SDK calls here — all AI calls go through ibm_granite.py.
"""

from __future__ import annotations
from config import CURRENCY_SYMBOL


# ══════════════════════════════════════════════════════════════
#  PROMPT BUILDERS
# ══════════════════════════════════════════════════════════════

def build_recommendation_prompt(
    origin: str,
    destination: str,
    travellers: int,
    duration: int,
    budget: int,
    interests: list[str],
    transport_pref: str,
    accommodation_pref: str,
) -> str:
    interest_str = ", ".join(interests) if interests else "general sightseeing"
    return (
        f"I am planning a trip from {origin} to {destination}.\n"
        f"Details:\n"
        f"- Travellers: {travellers}\n"
        f"- Duration: {duration} days\n"
        f"- Total budget: {CURRENCY_SYMBOL}{budget:,} INR\n"
        f"- Interests: {interest_str}\n"
        f"- Preferred transport: {transport_pref}\n"
        f"- Preferred accommodation: {accommodation_pref}\n\n"
        "Please provide:\n"
        "1. A brief destination overview and why it suits my interests\n"
        "2. The best time to visit and current season suitability\n"
        "3. Top 5 must-visit places or experiences\n"
        "4. Cultural etiquette and local customs to know\n"
        "5. Any important safety or health advisories\n"
    )


def build_itinerary_prompt(
    origin: str,
    destination: str,
    travellers: int,
    duration: int,
    budget: int,
    interests: list[str],
    transport_pref: str,
    accommodation_pref: str,
) -> str:
    interest_str = ", ".join(interests) if interests else "general sightseeing"
    daily_budget = budget // duration if duration else budget
    return (
        f"Create a detailed day-by-day itinerary for a {duration}-day trip "
        f"from {origin} to {destination} for {travellers} traveller(s).\n"
        f"Details:\n"
        f"- Total budget: {CURRENCY_SYMBOL}{budget:,} INR "
        f"(approx. {CURRENCY_SYMBOL}{daily_budget:,}/day)\n"
        f"- Interests: {interest_str}\n"
        f"- Preferred transport: {transport_pref}\n"
        f"- Preferred accommodation: {accommodation_pref}\n\n"
        "Format each day with:\n"
        "### Day N — <Theme/Title>\n"
        "- **Morning:** activity, location, estimated cost\n"
        "- **Afternoon:** activity, location, estimated cost\n"
        "- **Evening:** activity, dining recommendation, estimated cost\n"
        "- **Daily spend estimate:** ₹XXXX\n\n"
        "End with practical travel logistics (check-in/out timings, transport between spots).\n"
    )


def build_budget_prompt(
    destination: str,
    travellers: int,
    duration: int,
    budget: int,
    transport_pref: str,
    accommodation_pref: str,
) -> str:
    per_person = budget // travellers if travellers else budget
    return (
        f"Provide a detailed budget breakdown for a {duration}-day trip to {destination} "
        f"for {travellers} traveller(s) with a total budget of {CURRENCY_SYMBOL}{budget:,} INR "
        f"({CURRENCY_SYMBOL}{per_person:,} per person).\n"
        f"Preferred transport: {transport_pref}.\n"
        f"Preferred accommodation: {accommodation_pref}.\n\n"
        "Include:\n"
        "1. A table showing estimated cost per category "
        "(transport, accommodation, food, activities, shopping, miscellaneous)\n"
        "2. Per-person and total group cost\n"
        "3. Budget vs mid-range vs luxury tiers for this trip\n"
        "4. Money-saving tips specific to this destination\n"
        "5. Which booking platforms to use for best deals\n"
    )


def build_transport_accommodation_prompt(
    origin: str,
    destination: str,
    travellers: int,
    duration: int,
    budget: int,
    transport_pref: str,
    accommodation_pref: str,
) -> str:
    return (
        f"Recommend transport and accommodation options for travelling from {origin} to {destination} "
        f"for {travellers} traveller(s) over {duration} days.\n"
        f"Total budget: {CURRENCY_SYMBOL}{budget:,} INR.\n"
        f"Preferred transport: {transport_pref}.\n"
        f"Preferred accommodation: {accommodation_pref}.\n\n"
        "Cover:\n"
        "1. Best transport options to reach the destination (with approximate costs and booking tips)\n"
        "2. Local transport options within the destination\n"
        "3. Top 3–5 accommodation recommendations across price ranges\n"
        "4. Which neighbourhoods to stay in and why\n"
        "5. Useful booking apps / websites for India\n"
    )


def build_tips_prompt(destination: str, duration: int, interests: list[str]) -> str:
    interest_str = ", ".join(interests) if interests else "general travel"
    return (
        f"Provide practical travel tips and a packing list for a {duration}-day trip to {destination}.\n"
        f"Travel interests: {interest_str}.\n\n"
        "Include:\n"
        "1. Essential packing checklist (categorised: documents, clothing, health, tech, misc)\n"
        "2. Top 10 travel tips specific to this destination\n"
        "3. Apps to download before the trip\n"
        "4. Emergency contacts and important numbers\n"
        "5. Common tourist mistakes to avoid\n"
    )


# ══════════════════════════════════════════════════════════════
#  LOCAL BUDGET ESTIMATOR  (no AI needed)
# ══════════════════════════════════════════════════════════════

# Rough per-person-per-day cost bands in INR
_COST_BANDS = {
    "Budget (Hostel / Guesthouse)": {
        "accommodation_per_night": (500,  1200),
        "food_per_day"           : (300,   600),
        "local_transport_per_day": (150,   300),
        "activity_per_day"       : (200,   500),
    },
    "Mid-range Hotel": {
        "accommodation_per_night": (1500, 4000),
        "food_per_day"           : (600,  1200),
        "local_transport_per_day": (300,   600),
        "activity_per_day"       : (500,  1200),
    },
    "Boutique Hotel": {
        "accommodation_per_night": (3500, 8000),
        "food_per_day"           : (1000, 2000),
        "local_transport_per_day": (500,  1000),
        "activity_per_day"       : (800,  2000),
    },
    "Luxury Resort": {
        "accommodation_per_night": (8000, 25000),
        "food_per_day"           : (2000, 5000),
        "local_transport_per_day": (1000, 2500),
        "activity_per_day"       : (1500, 4000),
    },
    "Homestay / Airbnb": {
        "accommodation_per_night": (800,  3000),
        "food_per_day"           : (400,   900),
        "local_transport_per_day": (200,   500),
        "activity_per_day"       : (300,   800),
    },
    "Camping / Glamping": {
        "accommodation_per_night": (500,  2000),
        "food_per_day"           : (300,   700),
        "local_transport_per_day": (200,   500),
        "activity_per_day"       : (500,  1500),
    },
}

_TRANSPORT_TO_DEST = {
    "Flight"                  : (4000, 15000),
    "Train"                   : (500,  3000),
    "Bus"                     : (300,  1500),
    "Self-Drive / Car Rental" : (1500, 4000),
    "Cruise / Boat"           : (3000, 20000),
    "Mixed"                   : (1500, 8000),
}


def estimate_budget(
    travellers: int,
    duration: int,
    total_budget_inr: int,
    transport_pref: str,
    accommodation_pref: str,
) -> dict:
    """
    Return a budget breakdown dict based on simple rule-based estimates.
    Uses the midpoint of each cost band for the chosen category.
    """
    band = _COST_BANDS.get(accommodation_pref, _COST_BANDS["Mid-range Hotel"])

    def mid(lo, hi): return (lo + hi) // 2

    accom_per_night  = mid(*band["accommodation_per_night"])
    food_per_day     = mid(*band["food_per_day"])
    local_tx_per_day = mid(*band["local_transport_per_day"])
    activity_per_day = mid(*band["activity_per_day"])

    transport_range  = _TRANSPORT_TO_DEST.get(transport_pref, (2000, 8000))
    transport_pp     = mid(*transport_range)

    nights = max(duration - 1, 1)

    accommodation_total = accom_per_night  * nights    * travellers
    food_total          = food_per_day     * duration  * travellers
    local_tx_total      = local_tx_per_day * duration  * travellers
    activity_total      = activity_per_day * duration  * travellers
    transport_total     = transport_pp     * travellers * 2        # return trip
    shopping            = int(total_budget_inr * 0.05)             # 5 % of budget
    misc_buffer         = int(total_budget_inr * 0.05)

    computed_total = (accommodation_total + food_total + local_tx_total +
                      activity_total + transport_total + shopping + misc_buffer)

    # Scale proportionally if estimate overshoots the stated budget
    scale = total_budget_inr / computed_total if computed_total > total_budget_inr else 1.0

    return {
        "✈️ To/From Transport"  : int(transport_total   * scale),
        "🚌 Local Transport"    : int(local_tx_total     * scale),
        "🏨 Accommodation"      : int(accommodation_total* scale),
        "🍽️ Food & Dining"      : int(food_total         * scale),
        "🎟️ Activities"         : int(activity_total     * scale),
        "🛍️ Shopping"           : int(shopping           * scale),
        "🩺 Misc / Buffer"      : int(misc_buffer        * scale),
        "_total_budget"         : total_budget_inr,
        "_travellers"           : travellers,
        "_duration"             : duration,
    }


# ══════════════════════════════════════════════════════════════
#  INPUT VALIDATION
# ══════════════════════════════════════════════════════════════

def validate_inputs(
    origin: str,
    destination: str,
    travellers: int,
    duration: int,
    budget: int,
    interests: list[str],
) -> list[str]:
    """Return a list of error strings; empty list means inputs are valid."""
    errors: list[str] = []
    if not origin.strip():
        errors.append("Please enter your starting location.")
    if not destination.strip():
        errors.append("Please enter a destination or travel type.")
    if travellers < 1 or travellers > 50:
        errors.append("Number of travellers must be between 1 and 50.")
    if duration < 1 or duration > 90:
        errors.append("Travel duration must be between 1 and 90 days.")
    if budget < 1000:
        errors.append(f"Minimum budget is {CURRENCY_SYMBOL}1,000 INR.")
    if budget > 100_000_000:
        errors.append("Budget value seems unrealistically large. Please check.")
    if not interests:
        errors.append("Please select at least one travel interest.")
    return errors
