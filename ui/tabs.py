"""One render function per feature tab."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import time
from datetime import datetime, timezone
from typing import Any, Callable

import requests
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

from core.demo_data import DEMO_CRACK, DEMO_SAFETY, demo_chat_reply
from core.gemini_client import GeminiClient, GeminiError
from core.prompts import CRACK_PROMPT, SAFETY_PROMPT, chat_system_instruction
from core.schemas import PPE_ITEMS, normalize_crack, normalize_safety, width_band
from core.valuation import (
    RENDER_STYLES,
    STRUCTURES,
    TIERS,
    build_render_prompt,
    compute_valuation,
    format_indian_number,
    format_inr,
    pollinations_url,
)
from core.weather import ACTIVITY_MATRIX, ADVISORIES, WEATHER_CONDITIONS
from ui import components as ui

MAX_UPLOAD_MB = 10
MAX_IMAGE_SIDE = 1600


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _load_image(uploaded) -> tuple[Image.Image | None, str]:
    """Open, orient, convert and downscale an upload. Returns (image, file_signature)."""
    data = uploaded.getvalue()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        st.error(f"File is larger than {MAX_UPLOAD_MB} MB. Please upload a smaller image.")
        return None, ""
    try:
        img = Image.open(uploaded)
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    except (UnidentifiedImageError, OSError) as exc:
        st.error(f"Could not read this image ({exc}). Upload a valid JPG or PNG.")
        return None, ""
    return img, hashlib.md5(data).hexdigest()


def _run_vision(
    client: GeminiClient | None,
    prompt: str,
    image: Image.Image,
    demo_payload: dict,
    normalizer: Callable[[Any], dict],
) -> tuple[dict | None, str]:
    if client is None:
        time.sleep(0.8)  # brief pause so the demo feels like a real call
        return normalizer(copy.deepcopy(demo_payload)), "demo"
    try:
        return normalizer(client.analyze_image(prompt, image)), "live"
    except GeminiError as exc:
        st.error(str(exc))
        return None, "error"


def _report_bytes(kind: str, filename: str, mode: str, model: str, result: dict) -> bytes:
    report = {
        "report_type": kind,
        "platform": "Multimodal Construction Intelligence Platform",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_file": filename,
        "analysis_mode": "live" if mode == "live" else "demonstration (sample output)",
        "model": model if mode == "live" else None,
        "result": result,
    }
    return json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")


def _demo_notice(mode: str) -> None:
    if mode == "demo":
        st.info(
            "**Demonstration mode:** this is a sample report, not an analysis of your photo. "
            "Add a Gemini API key in the sidebar for live analysis.",
            icon="🧪",
        )


# --------------------------------------------------------------------------- #
# Tab 1 – Site Safety & PPE Audit
# --------------------------------------------------------------------------- #
def render_safety_tab(client: GeminiClient | None, model: str) -> None:
    ui.section(
        "Site Safety & PPE Audit", "EPIC 2",
        "Upload a site photo to audit helmets, high-vis vests, steel-toe boots and fall protection, "
        "and to flag hazards against OSHA 1926 and BOCW / IS safety codes.",
    )

    left, right = st.columns([1, 1.35], gap="large")
    with left:
        uploaded = st.file_uploader(
            "Construction site photo", type=["jpg", "jpeg", "png"], key="safety_upload",
            help=f"JPG or PNG, up to {MAX_UPLOAD_MB} MB. Wide shots with visible workers work best.",
        )
        image, sig = (None, "")
        if uploaded:
            image, sig = _load_image(uploaded)
            if image:
                st.image(image, caption=uploaded.name)
        run = st.button("Run safety audit", type="primary", disabled=image is None, key="safety_run")

    if run and image is not None:
        with right, st.spinner("Inspecting workers, PPE and hazards…"):
            result, mode = _run_vision(client, SAFETY_PROMPT, image, DEMO_SAFETY, normalize_safety)
        if result:
            st.session_state["safety"] = {"sig": sig, "file": uploaded.name, "mode": mode, "result": result}

    if not uploaded:
        st.session_state.pop("safety", None)
    state = st.session_state.get("safety")
    with right:
        if not state or state["sig"] != sig:
            st.markdown(
                '<div class="card"><div class="card-title">How it works</div><div class="body">'
                "1. Upload a clear photo of the active work area.<br>2. Gemini reads the scene and returns a strict "
                "JSON audit.<br>3. The app validates the JSON and renders the score, PPE checklist, hazards and a "
                "downloadable report.</div></div>",
                unsafe_allow_html=True,
            )
            return
        _render_safety_result(state, model)


def _render_safety_result(state: dict, model: str) -> None:
    r, mode = state["result"], state["mode"]
    _demo_notice(mode)
    if not r["image_valid"]:
        st.warning(r["summary"] or "This does not look like a construction site photo.")
        return

    crit = sum(1 for h in r["hazards"] if h["severity"] == "Critical")
    score_tone = "good" if r["safety_score"] >= 80 else "warn" if r["safety_score"] >= 50 else "bad"
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.metric_card("Safety Score", f"{r['safety_score']}/100", "Weighted site rating", score_tone)
    with c2:
        ui.metric_card_html("Overall Status", ui.pill(r["overall_status"], ui.STATUS_TONE[r["overall_status"]]),
                            "OSHA / BOCW basis", ui.STATUS_TONE[r["overall_status"]])
    with c3:
        ui.metric_card("Workers Detected", str(r["workers_detected"]), "Visible in frame", "info")
    with c4:
        ui.metric_card("Hazards", str(len(r["hazards"])), f"{crit} critical", "crit" if crit else "neutral")
    ui.score_bar(r["safety_score"])

    if r["summary"]:
        st.markdown(f"**Summary.** {r['summary']}")

    st.markdown("##### PPE detection checklist")
    cols = st.columns(4)
    for col, (key, label) in zip(cols, PPE_ITEMS.items()):
        item = r["ppe_detection"][key]
        with col:
            ui.ppe_tile(label, item["status"], item["compliant_workers"], r["workers_detected"], item["notes"])

    st.markdown("##### Identified hazards")
    if not r["hazards"]:
        st.success("No hazards identified in the visible area.")
    for h in r["hazards"]:
        meta = " · ".join(x for x in (h["category"], h["location"]) if x)
        ui.issue_card(h["hazard"], h["severity"], meta, h["remedy"], h["standard_reference"])

    if r["recommendations"]:
        st.markdown("##### Priority actions")
        st.markdown("\n".join(f"{i}. {rec}" for i, rec in enumerate(r["recommendations"], 1)))

    st.download_button(
        "⬇ Download JSON report",
        data=_report_bytes("site_safety_ppe_audit", state["file"], mode, model, r),
        file_name=f"safety_audit_{datetime.now():%Y%m%d_%H%M}.json",
        mime="application/json",
        key="safety_dl",
    )
    with st.expander("View raw JSON"):
        st.json(r)


# --------------------------------------------------------------------------- #
# Tab 2 – Crack Diagnostics
# --------------------------------------------------------------------------- #
def render_crack_tab(client: GeminiClient | None, model: str) -> None:
    ui.section(
        "Crack Diagnostics & Structural Integrity", "EPIC 2",
        "Classify concrete and masonry defects, estimate crack width, and get root causes and "
        "repair methods with urgency, referenced to IS 456 limits.",
    )

    left, right = st.columns([1, 1.35], gap="large")
    with left:
        uploaded = st.file_uploader(
            "Concrete / wall surface photo", type=["jpg", "jpeg", "png"], key="crack_upload",
            help="Take a close, square-on shot. Place a coin or scale next to the crack for better width estimates.",
        )
        image, sig = (None, "")
        if uploaded:
            image, sig = _load_image(uploaded)
            if image:
                st.image(image, caption=uploaded.name)
        run = st.button("Diagnose defect", type="primary", disabled=image is None, key="crack_run")

    if run and image is not None:
        with right, st.spinner("Measuring crack geometry and classifying defect…"):
            result, mode = _run_vision(client, CRACK_PROMPT, image, DEMO_CRACK, normalize_crack)
        if result:
            st.session_state["crack"] = {"sig": sig, "file": uploaded.name, "mode": mode, "result": result}

    state = st.session_state.get("crack")
    with right:
        if not uploaded:
            st.session_state.pop("crack", None)
        if not uploaded or not state or state["sig"] != sig:
            st.markdown(
                '<div class="card"><div class="card-title">Defect classes</div><div class="body">'
                "<b>Hairline</b> (&lt; 0.3 mm shrinkage) · <b>Settlement</b> (stepped/diagonal near openings) · "
                "<b>Structural Shear</b> (≈45° in members) · <b>Thermal Expansion</b> (junctions, roofs) · "
                "<b>Spalling</b> (delamination, exposed rebar).</div></div>",
                unsafe_allow_html=True,
            )
            return
        _render_crack_result(state, model)


def _render_crack_result(state: dict, model: str) -> None:
    r, mode = state["result"], state["mode"]
    _demo_notice(mode)
    if not r["image_valid"]:
        st.warning(r["summary"] or "This does not look like a concrete or masonry surface.")
        return

    sev_tone = ui.SEVERITY_TONE[r["severity"]]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.metric_card("Defect Type", r["defect_type"], f"Confidence {r['confidence']:.0%}", sev_tone)
    with c2:
        ui.metric_card("Est. Crack Width", f"{r['estimated_crack_width_mm']:.2f} mm",
                       width_band(r["estimated_crack_width_mm"]), sev_tone)
    with c3:
        ui.metric_card_html("Severity", ui.pill(r["severity"], sev_tone), f"Orientation: {r['orientation']}", sev_tone)
    with c4:
        u_tone = ui.URGENCY_TONE[r["urgency"]]
        ui.metric_card_html("Urgency", ui.pill(r["urgency"], u_tone), "Action window", u_tone)

    if r["estimated_crack_width_mm"] > 0.3:
        st.warning("Estimated width exceeds the IS 456:2000 Cl. 35.3.2 surface crack-width limit of 0.3 mm.", icon="⚠️")
    if r["defect_type"] == "Structural Shear" or r["severity"] == "Critical":
        st.error("Possible structural distress. Restrict loading and get an on-site inspection by a licensed "
                 "structural engineer before any repair.", icon="🚧")

    if r["summary"]:
        st.markdown(f"**Diagnosis.** {r['summary']}")
    if r["structural_risk"]:
        st.markdown(f"**Risk if untreated.** {r['structural_risk']}")

    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("##### Probable root causes")
        st.markdown("\n".join(f"{i}. {c}" for i, c in enumerate(r["root_causes"], 1)) or "—")
        if r["monitoring_advice"]:
            st.markdown("##### Monitoring")
            st.markdown(r["monitoring_advice"])
        if r["code_reference"]:
            st.caption(f"Code reference: {r['code_reference']}")
    with b:
        st.markdown("##### Recommended engineering repairs")
        for rep in r["recommended_repairs"]:
            ui.info_card(rep["method"], rep["description"], f"Materials: {rep['materials']}" if rep["materials"] else "")

    st.download_button(
        "⬇ Download JSON report",
        data=_report_bytes("crack_diagnostics", state["file"], mode, model, r),
        file_name=f"crack_diagnostics_{datetime.now():%Y%m%d_%H%M}.json",
        mime="application/json",
        key="crack_dl",
    )
    with st.expander("View raw JSON"):
        st.json(r)
    st.caption("AI visual assessment for screening only. It does not replace NDT or an engineer's site inspection.")


# --------------------------------------------------------------------------- #
# Tab 3 – Planning & Valuation
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False, ttl=3600, max_entries=30)
def _fetch_render(url: str) -> bytes:
    resp = requests.get(url, timeout=90)
    resp.raise_for_status()
    if not resp.headers.get("content-type", "").startswith("image"):
        raise ValueError("Render service did not return an image.")
    return resp.content


def render_planning_tab() -> None:
    ui.section(
        "Planning & Real Estate Valuation", "EPIC 3",
        "Estimate the project budget, capital spent to date, current asset value and bulk material needs, "
        "then generate a conceptual 3D render.",
    )

    i1, i2, i3 = st.columns(3)
    with i1:
        structure = st.selectbox("Structure type", list(STRUCTURES), key="v_structure")
        sqft = st.number_input("Built-up area (sq ft)", min_value=200, max_value=5_000_000, value=12_000,
                               step=500, key="v_sqft")
    with i2:
        tier = st.selectbox("Location tier", list(TIERS), index=1, key="v_tier", help="\n".join(f"{k}: {v}" for k, v in TIERS.items()))
        st.caption(TIERS[tier])
        contingency = st.slider("Contingency (%)", 0, 20, 8, key="v_cont")
    with i3:
        completion = st.slider("Construction completion (%)", 0, 100, 45, key="v_completion")

    try:
        v = compute_valuation(structure, float(sqft), tier, float(completion), float(contingency))
    except ValueError as exc:
        st.error(str(exc))
        return

    with i3:
        st.progress(int(v.completion_pct), text=f"Current stage: {v.current_milestone}")
        if v.next_milestone:
            st.caption(f"Next milestone: {v.next_milestone}")

    st.markdown("##### Financial summary")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        ui.metric_card("Total Project Budget", format_inr(v.total_budget),
                       f"₹{format_indian_number(v.cost_rate)}/sq ft + {contingency}% contingency", "info")
    with m2:
        ui.metric_card("Capex Incurred", format_inr(v.capex_incurred),
                       f"Remaining {format_inr(v.remaining_capex)}", "warn")
    with m3:
        ui.metric_card("Current Asset Valuation", format_inr(v.current_value),
                       f"At {v.completion_pct:.0f}% completion", "good")
    with m4:
        ui.metric_card("Value on Completion", format_inr(v.completed_value),
                       f"₹{format_indian_number(v.market_rate)}/sq ft · margin {v.roi_on_completion_pct:.0f}%",
                       "good" if v.roi_on_completion_pct > 0 else "bad")

    vc = v.value_created
    st.caption(
        f"Value created over capital spent to date: **{format_inr(vc)}**. The valuation assumes land and approvals make up "
        f"30% of completed value from day one, with the remainder accruing with physical progress."
    )

    st.markdown("##### Milestone progress")
    ui.milestone_tracker(v.milestones)

    st.markdown("##### Bulk material requirements")
    t, c = v.materials_total, v.materials_consumed
    mm1, mm2, mm3, mm4 = st.columns(4)
    with mm1:
        ui.metric_card("Steel (Fe500)", f"{t.steel_tonnes:,.1f} t", f"Consumed {c.steel_tonnes:,.1f} t", "neutral")
    with mm2:
        ui.metric_card("Cement (50 kg bags)", format_indian_number(t.cement_bags),
                       f"Consumed {format_indian_number(c.cement_bags)}", "neutral")
    with mm3:
        ui.metric_card("Sand", f"{format_indian_number(t.sand_cft)} cft", f"Consumed {format_indian_number(c.sand_cft)} cft", "neutral")
    with mm4:
        ui.metric_card("Aggregate", f"{format_indian_number(t.aggregate_cft)} cft",
                       f"Consumed {format_indian_number(c.aggregate_cft)} cft", "neutral")
    st.caption("Thumb-rule quantities per sq ft of built-up area for preliminary planning. Use BOQ from structural drawings for procurement.")

    st.divider()
    st.markdown("##### Conceptual 3D architectural rendering")
    r1, r2 = st.columns([1, 1.6], gap="large")
    with r1:
        style = st.selectbox("Render style", list(RENDER_STYLES), key="r_style")
        extra = st.text_input("Extra design notes (optional)", placeholder="e.g. rooftop solar, green facade", key="r_extra")
        prompt = build_render_prompt(structure, float(sqft), tier, style, extra)
        prompt = st.text_area("Generated prompt (editable)", prompt, height=120, key=f"r_prompt_{hash(prompt)}")
        go = st.button("Generate render", type="primary", key="r_go")
        if go:
            st.session_state["render_seed"] = random.randint(1, 999_999)
            st.session_state["render_prompt"] = prompt
    with r2:
        if "render_prompt" in st.session_state:
            url = pollinations_url(st.session_state["render_prompt"], st.session_state["render_seed"])
            try:
                with st.spinner("Rendering concept (this can take up to a minute)…"):
                    img_bytes = _fetch_render(url)
                st.image(img_bytes, caption="AI conceptual render via Pollinations AI. Not a design drawing.")
                st.download_button("⬇ Download render", img_bytes, file_name="concept_render.jpg", mime="image/jpeg", key="r_dl")
            except (requests.RequestException, ValueError) as exc:
                st.warning(f"Render service unavailable right now ({exc.__class__.__name__}). Open it directly instead:")
                st.markdown(f"[Open render in a new tab]({url})")
        else:
            st.markdown(
                '<div class="card"><div class="card-title">Concept render</div><div class="body">'
                "The prompt is built from your project inputs. Adjust the style or notes, then click "
                "<b>Generate render</b>. Each click produces a new variation.</div></div>",
                unsafe_allow_html=True,
            )


# --------------------------------------------------------------------------- #
# Tab 4 – Daily Site Assistant & Weather Advisory
# --------------------------------------------------------------------------- #
QUICK_PROMPTS = [
    "Curing period for M25 slab in summer?",
    "How many cement bags for a 1,500 sq ft house?",
    "How do I repair a 2 mm wall crack?",
    "Checklist before a concrete pour",
]


def render_assistant_tab(client: GeminiClient | None) -> None:
    ui.section(
        "Daily Site Assistant & Weather Advisory", "EPIC 5",
        "Pick today's weather to get go/no-go decisions and safety alerts, then ask the site engineering assistant anything.",
    )

    weather = st.radio("Today's site weather", WEATHER_CONDITIONS, horizontal=True, key="weather")
    adv = ADVISORIES[weather]
    ui.banner(adv["icon"], f"{adv['level']} · {weather}", f"{adv['headline']}  Trigger: {adv['trigger']}", adv["tone"])

    a, b = st.columns([1.25, 1], gap="large")
    with a:
        st.markdown("##### Safety alerts")
        for level, text in adv["alerts"]:
            ui.issue_card(text, level, "", "")
        st.markdown("##### Concrete curing protocol")
        ui.info_card(f"Curing under {weather.lower()} conditions", adv["curing"], "Ref: IS 456 Cl. 13.5 · IS 7861")
    with b:
        st.markdown("##### Activity go / no-go")
        ui.activity_table([(act, *ACTIVITY_MATRIX[act][weather]) for act in ACTIVITY_MATRIX])

    st.divider()
    _render_chat(client, weather)


def _render_chat(client: GeminiClient | None, weather: str) -> None:
    head, clear = st.columns([5, 1])
    with head:
        st.markdown("##### 💬 SiteMate · construction engineering assistant")
        if client is None:
            st.caption("Demo mode: answers a few common topics. Add an API key for full answers.")
    with clear:
        if st.button("Clear chat", key="chat_clear"):
            st.session_state["chat"] = []
            st.rerun()

    st.session_state.setdefault("chat", [])

    qcols = st.columns(len(QUICK_PROMPTS))
    for col, q in zip(qcols, QUICK_PROMPTS):
        if col.button(q, key=f"qp_{q}"):
            st.session_state["pending_prompt"] = q

    box = st.container(height=460, border=True)
    typed = st.chat_input("Ask about materials, methods, safety, quantities…", key="chat_input")
    message = typed or st.session_state.pop("pending_prompt", None)

    if message:
        st.session_state["chat"].append({"role": "user", "content": message})
        if client is None:
            reply = demo_chat_reply(message)
        else:
            try:
                with box, st.spinner("SiteMate is thinking…"):
                    reply = client.chat(st.session_state["chat"], chat_system_instruction(weather))
            except GeminiError as exc:
                reply = f"⚠️ {exc}"
        st.session_state["chat"].append({"role": "assistant", "content": reply})

    with box:
        if not st.session_state["chat"]:
            st.markdown(
                '<div class="small-muted" style="padding:1rem">Ask a question or tap a suggestion above. '
                f"SiteMate takes today's weather (<b>{ui.e(weather)}</b>) into account.</div>",
                unsafe_allow_html=True,
            )
        for msg in st.session_state["chat"]:
            with st.chat_message(msg["role"], avatar="👷" if msg["role"] == "user" else "🏗️"):
                st.markdown(msg["content"])
