"""
guardrails.py
-------------
Guardrails Module for AI Travel Planner Agent
Powered by IBM Granite via IBM watsonx.ai

This module provides layered safety and reliability checks:

  1. INPUT GUARDRAILS    — validate & screen user inputs before sending to AI
  2. CONTENT SAFETY      — block harmful / illegal / off-topic requests
  3. OUTPUT GUARDRAILS   — validate AI responses before displaying them
  4. PRIVACY & SECURITY  — mask PII, block credential leaks, protect system config
  5. IBM AI GUARDRAILS   — placeholder hooks for IBM watsonx.ai content filtering

Implementation note
-------------------
All guardrails in this file are CUSTOM PYTHON implementations.
IBM Granite Guardian and IBM watsonx.ai content-filtering APIs are NOT yet
called here — the stubs are clearly marked so they can be activated once
the appropriate IBM service entitlements are available.
No IBM guardrail integration is falsely claimed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════
#  RESULT DATACLASS
# ══════════════════════════════════════════════════════════════

@dataclass
class GuardrailResult:
    """Holds the outcome of any guardrail check."""
    allowed: bool
    reason: str = ""                          # machine-readable category
    message: str = ""                         # user-friendly display message
    warnings: list[str] = field(default_factory=list)  # non-blocking notices


# ══════════════════════════════════════════════════════════════
#  CONSTANTS — keyword lists used by multiple checks
# ══════════════════════════════════════════════════════════════

# Travel-domain keywords that indicate a valid travel request
_TRAVEL_KEYWORDS: list[str] = [
    "travel", "trip", "journey", "tour", "visit", "holiday", "vacation",
    "destination", "flight", "train", "bus", "hotel", "hostel", "resort",
    "itinerary", "plan", "booking", "ticket", "passport", "visa", "luggage",
    "packing", "sightseeing", "explore", "beach", "mountain", "city", "country",
    "place", "go to", "going to", "want to go", "suggest", "recommend",
    "budget", "cost", "expense", "rupee", "inr", "₹", "abroad", "domestic",
    "backpack", "adventure", "trek", "hike", "cruise", "road trip",
    "goa", "kerala", "rajasthan", "himachal", "manali", "shimla", "ooty",
    "mumbai", "delhi", "bangalore", "kolkata", "hyderabad", "chennai",
    "jaipur", "agra", "varanasi", "rishikesh", "leh", "ladakh", "kashmir",
    "europe", "paris", "london", "dubai", "singapore", "bangkok", "bali",
    "new york", "tokyo", "sydney", "maldives", "sri lanka", "nepal", "bhutan",
    "weather", "temperature", "season", "monsoon", "winter", "summer",
    "culture", "food", "cuisine", "local", "temple", "museum", "fort",
    "nature", "wildlife", "safari", "national park", "waterfall", "lake",
    "airport", "railway station", "taxi", "auto", "cab", "uber", "ola",
    "makemytrip", "goibibo", "booking.com", "airbnb", "trivago",
    "days", "nights", "week", "month", "duration", "travellers", "tourists",
]

# Prompt injection / jailbreak patterns
_INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?(previous|prior|above|system)\s+(instructions?|prompts?|rules?|constraints?)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"override\s+(your\s+)?(instructions?|programming|guidelines?|rules?|system)",
    r"you\s+are\s+now\s+(a\s+)?(different|new|another|unrestricted|jailbreak)",
    r"pretend\s+(you\s+are|to\s+be|that\s+you)",
    r"act\s+as\s+(if\s+you\s+are|a\s+)?(?!a\s+travel)",  # "act as X" unless "act as a travel..."
    r"reveal\s+(your\s+)?(api\s+key|password|secret|system\s+prompt|hidden|internal|credentials?)",
    r"show\s+(me\s+)?(your\s+)?(api\s+key|password|secret|system\s+prompt|credentials?|tokens?)",
    r"what\s+is\s+your\s+(api\s+key|password|secret|system\s+prompt|credentials?)",
    r"print\s+(your\s+)?(api\s+key|password|secret|system\s+prompt|env\s+variables?)",
    r"display\s+(your\s+)?(api\s+key|password|secret|system\s+prompt)",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"no\s+restrictions?",
    r"without\s+(any\s+)?(restrictions?|filters?|limits?|censorship)",
    r"bypass\s+(the\s+)?(filter|guardrail|safety|restriction|rule)",
    r"system\s*:\s*you\s+are",   # inline system prompt injection
    r"<\s*system\s*>",           # XML-style system injection
    r"\[system\]",               # bracket-style system injection
]

# Unsafe / harmful / illegal content patterns
_UNSAFE_PATTERNS: list[str] = [
    r"illegal\s+(travel|document|visa|border)",
    r"fake\s+(passport|visa|id|document|ticket)",
    r"forged?\s+(passport|visa|id|document)",
    r"counterfeit\s+(currency|money|document)",
    r"smuggl(e|ing)\s+(drug|weapon|person|goods)",
    r"human\s+trafficking",
    r"drug\s+traffick(ing|er)",
    r"terrorism|terrorist",
    r"bomb|explosive|weapon",
    r"hack(ing)?\s+someone",
    r"steal|theft|robbery",
    r"murder|kill|assassin",
    r"child\s+(abuse|exploit|pornography)",
    r"sex\s+traffick(ing|er)",
    r"launder(ing)?\s+money",
    r"cross\s+(the\s+)?border\s+(illegally|without\s+documents?)",
    r"sneak\s+(into|across|through)\s+(a\s+country|the\s+border)",
    r"evade\s+(customs?|immigration|border|security)",
    r"bribe\s+(officials?|police|customs?|immigration)",
]

# Clearly off-topic (non-travel) patterns
_OFFTOPIC_PATTERNS: list[str] = [
    r"write\s+(me\s+)?(a\s+)?(code|program|script|algorithm|essay|poem|story|novel)",
    r"help\s+me\s+(hack|crack|break|exploit|bypass|steal|cheat)",
    r"how\s+to\s+hack",
    r"how\s+to\s+(make|build|create)\s+(a\s+)?(bomb|weapon|drug|poison)",
    r"medical\s+(diagnosis|prescription|treatment|advice)",
    r"legal\s+(advice|opinion|case)",
    r"financial\s+(investment|stock|crypto|forex)\s+advice",
    r"relationship\s+advice",
    r"homework\s+(help|assignment)",
    r"solve\s+(this\s+)?(math|equation|problem)\s+(for\s+me)?",
    r"write\s+(my\s+)?(essay|assignment|thesis|dissertation)",
]

# PII patterns for masking in outputs
_PII_PATTERNS: list[tuple[str, str]] = [
    (r"\b[A-Z]{5}\d{4}[A-Z]{1}\b", "[AADHAAR/PAN MASKED]"),          # PAN card
    (r"\b\d{4}\s?\d{4}\s?\d{4}\b", "[AADHAAR MASKED]"),              # Aadhaar
    (r"\b[6-9]\d{9}\b", "[PHONE MASKED]"),                            # Indian mobile
    (r"\b[A-Z]\d{7}\b", "[PASSPORT MASKED]"),                        # Indian passport
    (r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b", "[EMAIL MASKED]"),
    (r"\b(?:\d[ -]?){15,18}\b", "[CARD NUMBER MASKED]"),             # Credit/debit card
    (r"\b\d{9,18}\b", "[ACCOUNT NUMBER MASKED]"),                    # Bank account
]

# Phrases that must never appear in outputs (credential leakage)
_FORBIDDEN_OUTPUT_PATTERNS: list[str] = [
    r"api[_\-\s]?key\s*[:=]\s*['\"]?[a-zA-Z0-9\-_]{20,}",
    r"password\s*[:=]\s*['\"]?\S{6,}",
    r"secret\s*[:=]\s*['\"]?\S{6,}",
    r"token\s*[:=]\s*['\"]?[a-zA-Z0-9\-_\.]{20,}",
    r"IBM_CLOUD_API_KEY",
    r"WATSONX_PROJECT_ID",
    r"bearer\s+[a-zA-Z0-9\-_\.]{20,}",
]

# Unverified claims that should carry a disclaimer label
_UNVERIFIED_CLAIM_TRIGGERS: list[str] = [
    "has been booked", "is confirmed", "booking confirmed",
    "reservation confirmed", "successfully booked",
    "live price", "real-time price", "current availability",
    "checked availability", "flights are available",
    "hotels are available", "rooms available",
]


# ══════════════════════════════════════════════════════════════
#  HELPER UTILITIES
# ══════════════════════════════════════════════════════════════

def _matches_any(text: str, patterns: list[str]) -> bool:
    """Return True if *text* matches any regex in *patterns* (case-insensitive)."""
    lower = text.lower()
    for pat in patterns:
        if re.search(pat, lower, re.IGNORECASE):
            return True
    return False


def _is_travel_related(text: str) -> bool:
    """
    Heuristic: return True if the input contains at least one travel keyword
    or travel-related question structure.
    """
    lower = text.lower()
    # Direct keyword match
    for kw in _TRAVEL_KEYWORDS:
        if kw in lower:
            return True
    # Geographic proper nouns: capitalised 2+ word phrases common in travel
    if re.search(r"\b[A-Z][a-z]{2,}\b", text):
        # If the capitalised word is part of a place-like context
        if re.search(r"\b(in|to|from|visit|at|near|around|through)\b", lower):
            return True
    return False


def _mask_pii(text: str) -> str:
    """Replace known PII patterns with masked tokens."""
    for pattern, replacement in _PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


# ══════════════════════════════════════════════════════════════
#  1. INPUT GUARDRAILS
# ══════════════════════════════════════════════════════════════

def check_input_fields(
    origin: str,
    destination: str,
    travellers: int,
    duration: int,
    budget: int | float,
    interests: list[str],
) -> GuardrailResult:
    """
    Structural validation: ensure all required fields are present and sane.
    This is the FIRST gate — called before content/safety checks.
    """
    errors: list[str] = []

    if not origin or not origin.strip():
        errors.append("Starting location cannot be empty.")
    if not destination or not destination.strip():
        errors.append("Destination cannot be empty.")
    if travellers is None or travellers < 1:
        errors.append("Number of travellers must be at least 1.")
    if travellers > 50:
        errors.append("Number of travellers cannot exceed 50.")
    if duration is None or duration < 1:
        errors.append("Travel duration must be at least 1 day.")
    if duration > 90:
        errors.append("Travel duration cannot exceed 90 days.")
    if budget is None or budget <= 0:
        errors.append("Budget must be a positive amount. Zero or negative budgets are not accepted.")
    if budget is not None and budget < 1000:
        errors.append("Minimum budget is ₹1,000 INR.")
    if not interests:
        errors.append("Please select at least one travel interest.")

    if errors:
        return GuardrailResult(
            allowed=False,
            reason="invalid_fields",
            message="⚠️ Please fix the following before generating your plan:\n\n• " + "\n• ".join(errors),
        )
    return GuardrailResult(allowed=True)


def check_prompt_injection(text: str) -> GuardrailResult:
    """
    Detect prompt injection / jailbreak attempts in any free-text field.
    Checks for instructions to ignore system rules, reveal API keys, etc.
    """
    if _matches_any(text, _INJECTION_PATTERNS):
        return GuardrailResult(
            allowed=False,
            reason="prompt_injection",
            message=(
                "🚫 Your request contains instructions that attempt to override the assistant's "
                "safety guidelines or reveal internal configuration. "
                "Please submit a normal travel planning question."
            ),
        )
    return GuardrailResult(allowed=True)


def check_unsafe_content(text: str) -> GuardrailResult:
    """
    Detect requests for illegal, harmful or dangerous travel arrangements.
    """
    if _matches_any(text, _UNSAFE_PATTERNS):
        return GuardrailResult(
            allowed=False,
            reason="unsafe_content",
            message=(
                "🚫 Your request has been blocked because it may involve illegal activities, "
                "unsafe arrangements, or content that violates travel safety guidelines. "
                "This assistant only provides legal, safe, and ethical travel advice. "
                "Please ensure you follow local laws and official travel advisories."
            ),
        )
    return GuardrailResult(allowed=True)


def check_topic_relevance(text: str) -> GuardrailResult:
    """
    Ensure the request is travel-related.
    Off-topic requests (coding, hacking, medical advice, etc.) are blocked.
    """
    # First check for clearly off-topic patterns (high confidence block)
    if _matches_any(text, _OFFTOPIC_PATTERNS):
        return GuardrailResult(
            allowed=False,
            reason="off_topic",
            message=(
                "🚫 This assistant is designed exclusively for travel planning. "
                "Your request appears to be unrelated to travel. "
                "Please ask about destinations, itineraries, budgets, transport, or packing."
            ),
        )

    # For longer freeform text, require at least one travel keyword
    text_stripped = text.strip()
    if len(text_stripped) > 15 and not _is_travel_related(text_stripped):
        return GuardrailResult(
            allowed=False,
            reason="off_topic",
            message=(
                "🚫 Your request does not appear to be travel-related. "
                "This assistant helps with trip planning, itineraries, budgets, and travel advice. "
                "Please describe your travel needs."
            ),
        )

    return GuardrailResult(allowed=True)


def run_input_guardrails(
    origin: str = "",
    destination: str = "",
    travellers: int = 1,
    duration: int = 1,
    budget: int | float = 0,
    interests: list[str] | None = None,
    freetext: str = "",
) -> GuardrailResult:
    """
    Master input guardrail: runs all input checks in order.
    Pass ``freetext`` for any open-ended user question.
    Pass the trip parameters for structured form validation.

    Returns the FIRST failed result, or GuardrailResult(allowed=True) if all pass.
    """
    interests = interests or []

    # Gate 1 — Prompt injection (highest priority, checked first)
    combined_text = f"{origin} {destination} {freetext}".strip()
    if combined_text:
        result = check_prompt_injection(combined_text)
        if not result.allowed:
            return result

    # Gate 2 — Unsafe / illegal content
    if combined_text:
        result = check_unsafe_content(combined_text)
        if not result.allowed:
            return result

    # Gate 3 — Structured field validation (only when trip fields are provided)
    if any([origin, destination, budget, freetext]):
        # Only validate structured fields if a "generate plan" scenario
        if origin or destination or budget:
            result = check_input_fields(origin, destination, travellers, duration, budget, interests)
            if not result.allowed:
                return result

    # Gate 4 — Topic relevance (for free-text questions)
    if freetext.strip():
        result = check_topic_relevance(freetext)
        if not result.allowed:
            return result

    return GuardrailResult(allowed=True)


# ══════════════════════════════════════════════════════════════
#  2. OUTPUT GUARDRAILS
# ══════════════════════════════════════════════════════════════

def check_output_credential_leak(text: str) -> GuardrailResult:
    """
    Scan AI output for accidental credential or API key exposure.
    If detected, block the response entirely.
    """
    if _matches_any(text, _FORBIDDEN_OUTPUT_PATTERNS):
        return GuardrailResult(
            allowed=False,
            reason="credential_leak",
            message=(
                "⚠️ The AI response was blocked because it may contain sensitive credentials "
                "or internal configuration data. Please try again."
            ),
        )
    return GuardrailResult(allowed=True)


def check_output_false_booking_claim(text: str) -> GuardrailResult:
    """
    Detect if the AI falsely claims that a booking was made or confirmed.
    The app has no live booking integration, so such claims are fabricated.
    Returns allowed=True but appends a warning so the UI can display a notice.
    """
    lower = text.lower()
    triggered = [t for t in _UNVERIFIED_CLAIM_TRIGGERS if t in lower]
    if triggered:
        return GuardrailResult(
            allowed=True,
            reason="unverified_booking_claim",
            message=text,
            warnings=[
                "ℹ️ **Disclaimer:** This assistant does not make real bookings. "
                "Any mention of 'confirmed' or 'booked' is illustrative AI text only. "
                "Please use MakeMyTrip, Booking.com, or IRCTC for actual reservations."
            ],
        )
    return GuardrailResult(allowed=True, message=text)


def check_output_relevance(text: str) -> GuardrailResult:
    """
    Light check: ensure the AI response appears to be about travel.
    Very long non-travel responses (>200 chars with no travel keywords) are flagged.
    """
    if len(text) > 200 and not _is_travel_related(text):
        return GuardrailResult(
            allowed=False,
            reason="off_topic_output",
            message=(
                "⚠️ The AI response did not appear to be related to travel planning and has been withheld. "
                "Please try rephrasing your request."
            ),
        )
    return GuardrailResult(allowed=True, message=text)


def mask_pii_in_output(text: str) -> str:
    """
    Scan AI output for PII patterns and replace with masked tokens.
    Returns the sanitised text.
    """
    return _mask_pii(text)


def run_output_guardrails(ai_response: str) -> GuardrailResult:
    """
    Master output guardrail: runs all output checks in order.
    Returns a GuardrailResult with:
      - allowed=False  → do NOT display the response; show result.message instead
      - allowed=True   → display result.message (which is the (possibly modified) response)
        and optionally show result.warnings as notices above the response
    """
    if not ai_response or not ai_response.strip():
        return GuardrailResult(
            allowed=False,
            reason="empty_response",
            message=(
                "⚠️ The AI did not return a response. "
                "This may be a temporary issue — please try again."
            ),
        )

    # Gate 1 — Credential leak (hard block)
    result = check_output_credential_leak(ai_response)
    if not result.allowed:
        return result

    # Gate 2 — Mask PII in the response text
    sanitised = mask_pii_in_output(ai_response)

    # Gate 3 — Relevance check
    result = check_output_relevance(sanitised)
    if not result.allowed:
        return result

    # Gate 4 — False booking claim (soft warning, not a block)
    result = check_output_false_booking_claim(sanitised)
    # result.allowed is always True here; just carry through warnings
    return GuardrailResult(
        allowed=True,
        reason=result.reason,
        message=sanitised,
        warnings=result.warnings,
    )


# ══════════════════════════════════════════════════════════════
#  3. PRIVACY & SECURITY GUARDRAILS
# ══════════════════════════════════════════════════════════════

def check_system_prompt_exposure(text: str) -> GuardrailResult:
    """
    Ensure no internal system prompt content or env variables are leaked.
    This guards against direct string leakage from config modules.
    """
    sensitive_markers = [
        "IBM_CLOUD_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL",
        "GRANITE_MAX_TOKENS", "GRANITE_TEMPERATURE",
        "<|system|>", "<|user|>", "<|assistant|>",  # Granite prompt format tags
    ]
    for marker in sensitive_markers:
        if marker in text:
            return GuardrailResult(
                allowed=False,
                reason="system_config_exposure",
                message=(
                    "🚫 Your request has been blocked because it contains internal configuration "
                    "identifiers. Please submit a regular travel planning question."
                ),
            )
    return GuardrailResult(allowed=True)


# ══════════════════════════════════════════════════════════════
#  4. IBM AI GUARDRAILS — STUBS
#     These are hooks for future IBM Granite Guardian integration.
#     Currently NOT called — requires IBM watsonx.ai entitlements.
# ══════════════════════════════════════════════════════════════

def ibm_granite_guardian_check(text: str) -> Optional[GuardrailResult]:  # noqa: F821
    """
    STUB — IBM Granite Guardian input/output risk check.

    When activated, this would call IBM Granite Guardian
    (ibm/granite-guardian-3-8b or ibm/granite-guardian-hap-38m)
    via the IBM watsonx.ai SDK to score the text for:
      - Hate, Abuse and Profanity (HAP)
      - PII detection
      - Prompt injection risk
      - Unsafe content

    To enable: uncomment the block below and ensure the appropriate
    IBM watsonx.ai service plan includes Granite Guardian entitlement.

    Returns None when IBM credentials / entitlements are unavailable,
    so the caller falls back to custom Python checks seamlessly.
    """
    # ── IBM Granite Guardian integration (requires IBM credentials) ──────────
    # try:
    #     from config import IBM_CLOUD_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL, credentials_available
    #     if not credentials_available():
    #         return None
    #     from ibm_watsonx_ai import APIClient, Credentials
    #     from ibm_watsonx_ai.foundation_models import ModelInference
    #     creds = Credentials(url=WATSONX_URL, api_key=IBM_CLOUD_API_KEY)
    #     client = APIClient(credentials=creds, project_id=WATSONX_PROJECT_ID)
    #     guardian = ModelInference(
    #         model_id="ibm/granite-guardian-3-8b",   # or granite-guardian-hap-38m
    #         api_client=client,
    #         project_id=WATSONX_PROJECT_ID,
    #     )
    #     result = guardian.generate_text(prompt=f"<|user|>\n{text}\n<|assistant|>")
    #     if "unsafe" in result.lower() or "risk" in result.lower():
    #         return GuardrailResult(
    #             allowed=False,
    #             reason="ibm_guardian_blocked",
    #             message="🚫 Content blocked by IBM Granite Guardian safety check.",
    #         )
    # except Exception:
    #     pass
    # ─────────────────────────────────────────────────────────────────────────
    return None   # IBM integration not active — fall back to custom checks


def ibm_watsonx_content_filter(text: str) -> Optional[GuardrailResult]:  # noqa: F821
    """
    STUB — IBM watsonx.ai content filtering for PII and harmful content.

    When activated, this would use the IBM watsonx.ai Moderation API to
    filter harmful content and detect PII before the response is shown.

    Returns None when not active so the caller uses custom checks.
    """
    return None   # IBM integration not active — fall back to custom checks


# ══════════════════════════════════════════════════════════════
#  5. COMBINED PIPELINE — convenience wrapper
# ══════════════════════════════════════════════════════════════

def screen_user_input(
    origin: str = "",
    destination: str = "",
    travellers: int = 1,
    duration: int = 1,
    budget: int | float = 0,
    interests: list[str] | None = None,
    freetext: str = "",
) -> GuardrailResult:
    """
    Full input screening pipeline.

    Order of checks:
      1. IBM Granite Guardian (if credentials present and service enabled)
      2. System prompt exposure
      3. Prompt injection
      4. Unsafe / illegal content
      5. Structured field validation
      6. Topic relevance
    """
    interests = interests or []
    combined = f"{origin} {destination} {freetext}".strip()

    # 1. IBM Granite Guardian (stub — returns None if not active)
    ibm_result = ibm_granite_guardian_check(combined)
    if ibm_result is not None and not ibm_result.allowed:
        return ibm_result

    # 2. System config / prompt exposure
    result = check_system_prompt_exposure(combined)
    if not result.allowed:
        return result

    # 3–6. Custom Python guardrails
    return run_input_guardrails(origin, destination, travellers, duration, budget, interests, freetext)


def screen_ai_output(ai_response: str) -> GuardrailResult:
    """
    Full output screening pipeline.

    Order of checks:
      1. IBM watsonx.ai content filter (stub — returns None if not active)
      2. Credential leak detection
      3. PII masking
      4. Output relevance check
      5. False booking claim warning
    """
    # 1. IBM watsonx.ai content filter (stub)
    ibm_result = ibm_watsonx_content_filter(ai_response)
    if ibm_result is not None and not ibm_result.allowed:
        return ibm_result

    # 2–5. Custom Python output guardrails
    return run_output_guardrails(ai_response)


# ══════════════════════════════════════════════════════════════
#  SAFE FALLBACK MESSAGE
# ══════════════════════════════════════════════════════════════

SAFE_FALLBACK = (
    "⚠️ **Something went wrong.** The assistant was unable to generate a safe response "
    "for your request at this time.\n\n"
    "Please try:\n"
    "- Rephrasing your request as a travel planning question\n"
    "- Ensuring your destination and budget details are valid\n"
    "- Checking your internet connection\n\n"
    "If the issue persists, please refresh the page and try again."
)
