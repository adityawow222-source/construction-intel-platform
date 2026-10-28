"""Multimodal Construction Intelligence Platform
Skill Wallet Capstone Project 1

Entry point: `streamlit run app.py`
"""
from __future__ import annotations

import hashlib

import streamlit as st

st.set_page_config(
    page_title="Construction Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.gemini_client import GENAI_AVAILABLE, MODEL_OPTIONS, GeminiClient, GeminiError  # noqa: E402
from ui import components as ui  # noqa: E402
from ui.tabs import (  # noqa: E402
    render_assistant_tab,
    render_crack_tab,
    render_planning_tab,
    render_safety_tab,
)

ARCHITECTURE = """\
┌─────────────── Streamlit UI ───────────────┐
│ Safety │ Cracks │ Valuation │ Assistant    │
└────┬────────┬────────┬──────────┬──────────┘
     │ image  │ image  │ inputs   │ chat
     ▼        ▼        ▼          ▼
┌──────────────┐  ┌───────────┐ ┌──────────┐
│ Prompt layer │  │ Valuation │ │ Weather  │
│ (JSON spec)  │  │  engine   │ │  rules   │
└──────┬───────┘  └─────┬─────┘ └──────────┘
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ Gemini API   │  │ Pollinations │
│ (vision+LLM) │  │  AI render   │
└──────┬───────┘  └──────────────┘
       ▼
┌──────────────┐
│ Schema check │──► cards · JSON report
└──────────────┘"""

FEATURES = [
    ("🦺", "Site Safety & PPE Audit", "Score, PPE checklist, hazards"),
    ("🧱", "Crack Diagnostics", "Defect type, width, repairs"),
    ("📐", "Planning & Valuation", "Budget, value, materials, render"),
    ("🌦️", "Site Assistant & Weather", "Alerts, go/no-go, chatbot"),
]


def _secret_key() -> str:
    """Read GEMINI_API_KEY from Streamlit secrets if configured; never raise."""
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:  # noqa: BLE001 - no secrets.toml present
        return ""


def _get_client(api_key: str, model: str) -> tuple[GeminiClient | None, str | None]:
    """Create (or reuse) a per-session client. Keys are never cached across users."""
    if not api_key:
        return None, None
    sig = hashlib.sha256(f"{api_key}|{model}".encode()).hexdigest()
    if st.session_state.get("_client_sig") == sig and st.session_state.get("_client"):
        return st.session_state["_client"], None
    try:
        client = GeminiClient(api_key, model)
    except GeminiError as exc:
        st.session_state.pop("_client", None)
        st.session_state.pop("_client_sig", None)
        return None, str(exc)
    st.session_state["_client"], st.session_state["_client_sig"] = client, sig
    return client, None


def render_sidebar() -> tuple[GeminiClient | None, str]:
    with st.sidebar:
        st.markdown("## 🏗️ Control Center")

        st.markdown("**Google Gemini API key**")
        secret = _secret_key()
        typed = st.text_input(
            "API key", type="password", placeholder="Paste your key (AIza…)", label_visibility="collapsed",
            help="Get a free key at aistudio.google.com. The key stays in this browser session and is never stored.",
        )
        api_key = typed.strip() or secret

        model_choice = st.selectbox("Model", MODEL_OPTIONS + ["Custom…"], index=0)
        model = (
            st.text_input("Custom model id", value="gemini-2.5-flash").strip() or "gemini-2.5-flash"
            if model_choice == "Custom…"
            else model_choice
        )

        client, error = (None, None)
        if not GENAI_AVAILABLE:
            st.error("google-genai is not installed. Running in demonstration mode.")
        else:
            client, error = _get_client(api_key, model)

        if error:
            st.error(error)
        if client:
            source = "secrets" if (secret and not typed.strip()) else "sidebar"
            st.success(f"Live mode · {model} (key from {source})", icon="✅")
            if st.button("Test connection"):
                try:
                    with st.spinner("Contacting Gemini…"):
                        name = client.ping()
                    st.toast(f"Connected to {name}", icon="✅")
                except GeminiError as exc:
                    st.error(str(exc))
        else:
            st.info("**Demonstration mode.** Sample outputs are shown. Add a key for live AI analysis.", icon="🧪")

        st.divider()
        st.markdown("**Feature navigation**")
        for icon, name, desc in FEATURES:
            st.markdown(f"{icon} **{name}**  \n<span class='small-muted'>{desc}</span>", unsafe_allow_html=True)
        st.caption("Use the tabs at the top of the page to switch modules.")

        with st.expander("Architecture overview"):
            st.markdown(f'<div class="arch">{ui.e(ARCHITECTURE)}</div>', unsafe_allow_html=True)
            st.markdown(
                "- **Frontend:** Streamlit with custom CSS components\n"
                "- **AI layer:** Google Gemini multimodal (vision + text) through `google-genai`\n"
                "- **Contracts:** prompts enforce a JSON schema, and `core/schemas.py` validates and normalises it\n"
                "- **Deterministic engines:** valuation and weather rules run locally\n"
                "- **Rendering:** Pollinations AI text-to-image\n"
                "- **State:** `st.session_state` only, with no database"
            )

        st.divider()
        st.caption(
            "AI outputs support engineering judgement and do not replace it. Verify structural and "
            "safety decisions with a licensed professional."
        )
    return client, model


def main() -> None:
    ui.inject_css()
    client, model = render_sidebar()
    ui.hero("● Live AI mode" if client else "● Demonstration mode", "good" if client else "warn")

    tabs = st.tabs([f"{icon} {name}" for icon, name, _ in FEATURES])
    with tabs[0]:
        render_safety_tab(client, model)
    with tabs[1]:
        render_crack_tab(client, model)
    with tabs[2]:
        render_planning_tab()
    with tabs[3]:
        render_assistant_tab(client)


if __name__ == "__main__":
    main()
