import streamlit as st
from triage_core import (
    initialise_drug_config,
    load_tripsit_combos,
    triage_from_text_and_context,
    # build_referral_text,  # not needed now, so optional
)

# -------------------------------------------------------------------------
# Initialise configs once when the app starts
# -------------------------------------------------------------------------
@st.cache_resource
def init_engine():
    initialise_drug_config(tripsit_path="drugs.json")
    load_tripsit_combos("combos.json")
    return True


init_engine()

# -------------------------------------------------------------------------
# Session state to persist last triage run
# -------------------------------------------------------------------------
if "triage_result" not in st.session_state:
    st.session_state.triage_result = None
    st.session_state.triage_context = None
    st.session_state.triage_text = ""

# -------------------------------------------------------------------------
# PAGE HEADER
# -------------------------------------------------------------------------
st.title("Drug & Context Triage Tool")

st.markdown(
    """
This tool estimates **relative acute overdose / life-threatening risk**
based on detected substances and brief person-level context.

- A **lower score** means *lower acute overdose risk relative to other
  profiles in this tool* – it does **not** mean the drugs are safe or
  low-harm overall.
- The tool does **not** capture long-term physical, psychological or
  social harms from substance use.

It is intended as **decision support only** and does not replace
clinical judgement.
"""
)

# --- Drug input ---
drugs_text = st.text_area(
    "Substances (free text)",
    placeholder="e.g. 'heroin and pregabalin with alcohol'",
)

# --- Context inputs ---
st.subheader("Client context")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    weight_kg = st.number_input(
        "Weight (kg)", min_value=20.0, max_value=200.0, step=0.5
    )
    height_cm = st.number_input(
        "Height (cm)", min_value=120.0, max_value=220.0, step=0.5
    )

with col2:
    sex = st.selectbox(
        "Sex (for context – optional)",
        ["Prefer not to record", "Female", "Male", "Intersex / other"],
    )
    opioid_dependent = st.checkbox(
        "Known or suspected opioid dependence?", value=False
    )
    homeless = st.checkbox("Currently homeless or unstable housing?")
    recent_overdose = st.checkbox("Recent non-fatal overdose (last 3–6 months)?")
    severe_mental_health = st.checkbox("Severe mental health difficulty?")
    polysubstance_history = st.checkbox("History of regular polysubstance use?")

context = {
    "age": int(age) if age else None,
    "weight_kg": float(weight_kg) if weight_kg else None,
    "height_cm": float(height_cm) if height_cm else None,
    "sex": sex.lower() if sex and not sex.startswith("Prefer") else None,
    "opioid_dependent": opioid_dependent,
    "homeless": homeless,
    "recent_overdose": recent_overdose,
    "severe_mental_health": severe_mental_health,
    "polysubstance_history": polysubstance_history,
}

# -------------------------------------------------------------------------
# MAIN RUN BUTTON – store result in session_state
# -------------------------------------------------------------------------
if st.button("Run triage") and drugs_text.strip():
    result = triage_from_text_and_context(drugs_text, context)
    st.session_state.triage_result = result
    st.session_state.triage_context = context
    st.session_state.triage_text = drugs_text

# Always read from session_state for display
result = st.session_state.triage_result
context_for_display = st.session_state.triage_context

if result is not None:
    st.markdown("## Triage result")

    st.write(
        f"**Detected drugs:** {', '.join(result['detected_drugs']) or 'None'}"
    )
    if result["unknown_drugs"]:
        st.write(
            f"**Unknown drugs (flagged):** "
            f"{', '.join(result['unknown_drugs'])}"
        )

    st.write(
        f"**Drug score (acute pharmacological risk):** "
        f"{result['drug_score']}"
    )
    st.write(f"- Category synergy component: {result['synergy_component']}")
    st.write(f"- TripSit combo component: {result['tripsit_combo_component']}")
    st.write(
        f"**Context score (client vulnerability factors):** "
        f"{result['context_score']}"
    )
    st.write(
        f"**TOTAL triage score (acute overdose risk):** "
        f"{result['total_score']}"
    )

    st.caption(
        "The total triage score reflects **relative acute overdose / "
        "life-threatening risk** within this model. It does not mean the "
        "drugs are safe or low-harm overall when the score is lower."
    )

    st.markdown(
        f"### Acute risk branch / pathway: **{result['branch']}**"
    )
