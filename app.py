"""
app.py
------
AI Travel Planner Agent — Streamlit frontend
Powered by IBM Granite via IBM watsonx.ai (Lite tier)

Run:  streamlit run app.py
"""

import streamlit as st
import traceback

from config import (
    TRAVEL_INTERESTS, TRANSPORT_MODES, ACCOMMODATION_STYLES,
    CURRENCY_SYMBOL, credentials_available,
)
from ibm_granite import generate
from travel_utils import (
    validate_inputs,
    estimate_budget,
    build_recommendation_prompt,
    build_itinerary_prompt,
    build_budget_prompt,
    build_transport_accommodation_prompt,
    build_tips_prompt,
)
from guardrails import (
    screen_user_input,
    screen_ai_output,
    SAFE_FALLBACK,
)

# ══════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Travel Planner Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
#  CUSTOM CSS — modern card look
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Global ───────────────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

/* ── Hero banner ─────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 60%, #004d99 100%);
    border-radius: 16px;
    padding: 2.2rem 2.5rem;
    color: white;
    margin-bottom: 1.5rem;
    text-align: center;
}
.hero h1 { font-size: 2.4rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
.hero p  { font-size: 1.05rem; opacity: 0.88; margin: 0.4rem 0 0; }

/* ── IBM badge ───────────────────────────────────────────── */
.ibm-badge {
    display: inline-block;
    background: #0f62fe;
    color: white;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-top: 0.6rem;
}

/* ── Demo banner ─────────────────────────────────────────── */
.demo-banner {
    background: #fff8e1;
    border-left: 5px solid #f9a825;
    padding: 0.7rem 1rem;
    border-radius: 6px;
    font-size: 0.87rem;
    margin-bottom: 1rem;
}

/* ── Result cards ────────────────────────────────────────── */
.result-card {
    background: #f8faff;
    border: 1px solid #dce8ff;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

/* ── Budget bar ──────────────────────────────────────────── */
.budget-row {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
    font-size: 0.92rem;
}
.budget-label { width: 210px; flex-shrink: 0; }
.budget-bar-wrap { flex: 1; background: #e9ecef; border-radius: 6px; height: 14px; margin: 0 10px; }
.budget-bar { height: 14px; border-radius: 6px; background: #1a73e8; }
.budget-amount { width: 120px; text-align: right; font-weight: 600; color: #1a73e8; }

/* ── Section divider ─────────────────────────────────────── */
.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1a1a2e;
    border-bottom: 2px solid #1a73e8;
    padding-bottom: 6px;
    margin: 1.2rem 0 0.8rem;
}

/* ── Stat tiles ──────────────────────────────────────────── */
.stat-tile {
    background: white;
    border: 1px solid #e3e8f0;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    text-align: center;
}
.stat-value { font-size: 1.6rem; font-weight: 800; color: #1a73e8; }
.stat-label { font-size: 0.78rem; color: #666; margin-top: 2px; }

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] { background: #f0f4ff; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _fmt_inr(amount: int) -> str:
    """Format a number as Indian currency string, e.g. ₹1,20,000."""
    s = str(amount)
    if len(s) <= 3:
        return f"{CURRENCY_SYMBOL}{s}"
    # Indian numbering: last 3 digits, then groups of 2
    last3 = s[-3:]
    rest  = s[:-3]
    groups = []
    while len(rest) > 2:
        groups.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.append(rest)
    groups.reverse()
    return f"{CURRENCY_SYMBOL}{','.join(groups)},{last3}"


def _render_budget_bars(breakdown: dict) -> None:
    """Render a horizontal bar chart for the budget breakdown using HTML."""
    total = breakdown["_total_budget"]
    items = {k: v for k, v in breakdown.items() if not k.startswith("_")}

    html = ""
    for label, amount in items.items():
        pct = min(int((amount / total) * 100), 100)
        html += (
            f'<div class="budget-row">'
            f'<span class="budget-label">{label}</span>'
            f'<div class="budget-bar-wrap"><div class="budget-bar" style="width:{pct}%"></div></div>'
            f'<span class="budget-amount">{_fmt_inr(amount)}</span>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)


def _ai_section(title: str, prompt: str, key: str) -> None:
    """Call IBM Granite, run output guardrails, then render the result in a card."""
    with st.spinner(f"🤖 IBM Granite is generating {title.lower()}…"):
        try:
            response, is_demo = generate(prompt)
        except Exception:
            st.error(f"Unexpected error generating {title}:\n```\n{traceback.format_exc()}\n```")
            st.warning(SAFE_FALLBACK)
            return

    # ── OUTPUT GUARDRAIL ──────────────────────────────────────
    output_check = screen_ai_output(response)
    if not output_check.allowed:
        st.error(output_check.message)
        return

    # Use the (possibly PII-masked) sanitised response
    safe_response = output_check.message

    st.markdown(f'<div class="section-title">🔷 {title}</div>', unsafe_allow_html=True)

    if is_demo:
        st.markdown(
            '<div class="demo-banner">🟡 <strong>Demo Mode</strong> — '
            'IBM credentials not configured. Showing illustrative sample data.</div>',
            unsafe_allow_html=True,
        )

    # Show any output guardrail warnings (e.g. false booking claim notice)
    for warn in output_check.warnings:
        st.info(warn)

    with st.container():
        st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
        st.markdown(safe_response)
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  HERO HEADER
# ══════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero">
  <h1>✈️ AI Travel Planner Agent</h1>
  <p>Your personalised trip planning assistant powered by IBM Granite AI</p>
  <span class="ibm-badge">⬛ IBM watsonx.ai · Granite-3-8B-Instruct · AICTE 2026</span>
</div>
""", unsafe_allow_html=True)

# Credential status pill
if credentials_available():
    st.success("✅ **Live Mode** — Connected to IBM watsonx.ai (Granite model active)")
else:
    st.warning(
        "🟡 **Demo Mode** — IBM API credentials not set. "
        "Add your keys to `.env` to enable real AI responses. "
        "See `.env.example` for instructions."
    )


# ══════════════════════════════════════════════════════════════
#  SIDEBAR — TRIP INPUTS
# ══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🗺️ Plan Your Trip")
    st.markdown("---")

    origin = st.text_input(
        "📍 Starting Location",
        placeholder="e.g. Mumbai, Delhi, Bangalore",
        help="Your city or airport of departure",
    )

    destination = st.text_input(
        "🌏 Destination / Travel Type",
        placeholder="e.g. Goa, Himachal Pradesh, Europe, Beach Holiday",
        help="Specific place or type of travel",
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        travellers = st.number_input("👥 Travellers", min_value=1, max_value=50, value=2, step=1)
    with col2:
        duration   = st.number_input("📅 Duration (days)", min_value=1, max_value=90, value=5, step=1)

    budget = st.number_input(
        f"💰 Total Budget ({CURRENCY_SYMBOL} INR)",
        min_value=1000,
        max_value=100_000_000,
        value=50000,
        step=1000,
        format="%d",
        help="Total trip budget for all travellers",
    )

    st.markdown(f"*Per person: {_fmt_inr(budget // max(travellers, 1))}*")

    st.markdown("---")
    st.markdown("**🎯 Travel Interests** *(select all that apply)*")
    interests = st.multiselect(
        label="Interests",
        options=TRAVEL_INTERESTS,
        default=["Nature & Wildlife", "Food & Culinary"],
        label_visibility="collapsed",
    )

    transport_pref     = st.selectbox("🚗 Preferred Transport",     TRANSPORT_MODES,       index=0)
    accommodation_pref = st.selectbox("🏨 Preferred Accommodation", ACCOMMODATION_STYLES,  index=1)

    st.markdown("---")
    plan_button = st.button("🚀 Generate Travel Plan", use_container_width=True, type="primary")


# ══════════════════════════════════════════════════════════════
#  MAIN CONTENT — TABS
# ══════════════════════════════════════════════════════════════

tab_home, tab_itinerary, tab_budget, tab_transport, tab_tips = st.tabs([
    "🌍 Overview & Recommendations",
    "📅 Day-wise Itinerary",
    "💰 Budget Breakdown",
    "🚗 Transport & Accommodation",
    "🧳 Tips & Packing",
])

# ── Quick-stat tiles on the home tab (always visible) ────────
with tab_home:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-tile"><div class="stat-value">{travellers}</div>'
                    f'<div class="stat-label">Travellers</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-tile"><div class="stat-value">{duration}d</div>'
                    f'<div class="stat-label">Duration</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-tile"><div class="stat-value">{_fmt_inr(budget)}</div>'
                    f'<div class="stat-label">Total Budget</div></div>', unsafe_allow_html=True)
    with c4:
        ppd = budget // max(travellers * duration, 1)
        st.markdown(f'<div class="stat-tile"><div class="stat-value">{_fmt_inr(ppd)}</div>'
                    f'<div class="stat-label">Per Person/Day</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not plan_button:
        st.info(
            "👈 **Fill in your trip details** in the sidebar and click **Generate Travel Plan** to get started.",
            icon="✈️",
        )


# ══════════════════════════════════════════════════════════════
#  PLAN GENERATION — triggered by button
# ══════════════════════════════════════════════════════════════

if plan_button:
    # ── GUARDRAILS: full input screening ─────────────────────
    guard = screen_user_input(
        origin=origin,
        destination=destination,
        travellers=travellers,
        duration=duration,
        budget=budget,
        interests=interests,
    )
    if not guard.allowed:
        st.sidebar.error(guard.message)
        st.error(
            f"🛡️ **Request Blocked by Guardrails**\n\n{guard.message}",
        )
        st.stop()

    # ── Legacy validation (structural field checks) ───────────
    errors = validate_inputs(origin, destination, travellers, duration, budget, interests)
    if errors:
        for e in errors:
            st.sidebar.error(e)
        st.stop()

    # ── Common args dict ──────────────────────────────────────
    common = dict(
        origin=origin, destination=destination,
        travellers=travellers, duration=duration, budget=budget,
        interests=interests, transport_pref=transport_pref,
        accommodation_pref=accommodation_pref,
    )

    # ── Tab 1: Overview & Recommendations ────────────────────
    with tab_home:
        prompt = build_recommendation_prompt(**common)
        _ai_section("Destination Overview & Recommendations", prompt, "rec")

    # ── Tab 2: Itinerary ──────────────────────────────────────
    with tab_itinerary:
        prompt = build_itinerary_prompt(**common)
        _ai_section(f"{duration}-Day Itinerary for {destination}", prompt, "itin")

    # ── Tab 3: Budget breakdown ───────────────────────────────
    with tab_budget:
        # Local rule-based estimate (no API)
        breakdown = estimate_budget(
            travellers, duration, budget, transport_pref, accommodation_pref
        )

        st.markdown('<div class="section-title">📊 Estimated Budget Breakdown</div>',
                    unsafe_allow_html=True)
        st.caption("Local estimate based on your inputs — actual costs may vary.")
        _render_budget_bars(breakdown)

        total_shown = sum(v for k, v in breakdown.items() if not k.startswith("_"))
        st.markdown(
            f"**Estimated Total: {_fmt_inr(total_shown)}** "
            f"out of your budget of {_fmt_inr(budget)}",
        )
        remaining = budget - total_shown
        if remaining >= 0:
            st.success(f"✅ Fits within budget — {_fmt_inr(remaining)} buffer remaining.")
        else:
            st.warning(f"⚠️ Estimate slightly exceeds budget by {_fmt_inr(abs(remaining))}. Consider adjustments.")

        st.markdown("---")

        # AI-generated detailed budget from Granite
        prompt = build_budget_prompt(
            destination, travellers, duration, budget, transport_pref, accommodation_pref
        )
        _ai_section("AI-Generated Detailed Budget Advice", prompt, "budg")

    # ── Tab 4: Transport & Accommodation ─────────────────────
    with tab_transport:
        prompt = build_transport_accommodation_prompt(
            origin=origin, destination=destination,
            travellers=travellers, duration=duration, budget=budget,
            transport_pref=transport_pref, accommodation_pref=accommodation_pref,
        )
        _ai_section("Transport & Accommodation Recommendations", prompt, "trans")

    # ── Tab 5: Tips & Packing ─────────────────────────────────
    with tab_tips:
        prompt = build_tips_prompt(destination, duration, interests)
        _ai_section("Travel Tips & Packing List", prompt, "tips")


# ══════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#888; font-size:0.8rem;">'
    'AI Travel Planner Agent · Powered by '
    '<strong>IBM Granite</strong> via <strong>IBM watsonx.ai</strong> (Lite tier) · '
    'IBM AICTE Internship 2026 · Built with Streamlit'
    '</p>',
    unsafe_allow_html=True,
)
