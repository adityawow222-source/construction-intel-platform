"""Reusable, HTML-escaped UI building blocks and the global stylesheet."""
from __future__ import annotations

import html

import streamlit as st

TONES = {"good", "warn", "bad", "crit", "info", "neutral"}

SEVERITY_TONE = {"Low": "good", "Medium": "warn", "High": "bad", "Critical": "crit"}
STATUS_TONE = {"Compliant": "good", "Partially Compliant": "warn", "Non-Compliant": "bad"}
PPE_TONE = {"Detected": "good", "Partial": "warn", "Missing": "bad", "Not Visible": "neutral", "Not Applicable": "neutral"}
URGENCY_TONE = {
    "Monitor": "good",
    "Planned Repair (within 3 months)": "warn",
    "Priority Repair (within 2 weeks)": "bad",
    "Immediate Action": "crit",
}
GO_TONE = {"Go": "good", "Caution": "warn", "No-Go": "bad"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

:root {
  --ink: #0f172a; --ink-2: #334155; --muted: #64748b; --line: #e2e8f0;
  --card: #ffffff; --surface: #f8fafc; --accent: #f59e0b; --accent-ink: #92400e;
  --good: #15803d; --good-bg: #dcfce7; --warn: #a16207; --warn-bg: #fef9c3;
  --bad: #c2410c; --bad-bg: #ffedd5; --crit: #b91c1c; --crit-bg: #fee2e2;
  --info: #1d4ed8; --info-bg: #dbeafe; --neutral: #475569; --neutral-bg: #f1f5f9;
}
html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox { font-family: 'Inter', system-ui, sans-serif; }
.block-container { padding-top: 1.6rem; max-width: 1280px; }

/* Hero */
.hero { position: relative; overflow: hidden; border-radius: 20px; padding: 1.7rem 2rem; margin-bottom: 1.3rem;
  background: radial-gradient(1200px 300px at 110% -40%, rgba(245,158,11,.45), transparent 60%),
              linear-gradient(135deg, #0b1220 0%, #111c33 55%, #1e293b 100%); color: #f8fafc; }
.hero::after { content: ""; position: absolute; inset: auto 0 0 0; height: 6px;
  background: repeating-linear-gradient(-45deg, #f59e0b 0 14px, #111827 14px 28px); opacity: .9; }
.hero .eyebrow { font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; color: #fbbf24; font-weight: 700; }
.hero h1 { margin: .25rem 0 .35rem; font-size: 2rem; font-weight: 800; color: #fff; line-height: 1.15; }
.hero p { margin: 0; color: #cbd5e1; font-size: .98rem; max-width: 820px; }
.hero .chips { margin-top: .9rem; display: flex; gap: .45rem; flex-wrap: wrap; }
.hero .chip { font-size: .75rem; padding: .25rem .65rem; border-radius: 999px; border: 1px solid rgba(255,255,255,.18);
  color: #e2e8f0; background: rgba(255,255,255,.06); }

/* Section heading */
.section-title { display: flex; align-items: baseline; gap: .6rem; margin: .4rem 0 .2rem; }
.section-title h3 { margin: 0; font-size: 1.25rem; font-weight: 750; color: var(--ink); }
.section-title .tag { font-size: .7rem; font-weight: 700; color: var(--accent-ink); background: #fef3c7;
  padding: .15rem .5rem; border-radius: 6px; letter-spacing: .04em; }
.section-sub { color: var(--muted); font-size: .92rem; margin-bottom: .9rem; }

/* Metric cards */
.metric-card { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: .95rem 1.1rem;
  box-shadow: 0 1px 2px rgba(15,23,42,.04); height: 100%; border-top: 4px solid var(--line); }
.metric-card .label { font-size: .72rem; text-transform: uppercase; letter-spacing: .07em; color: var(--muted); font-weight: 600; }
.metric-card .value { font-size: 1.55rem; font-weight: 800; color: var(--ink); margin-top: .2rem; line-height: 1.2; }
.metric-card .sub { font-size: .8rem; color: var(--muted); margin-top: .25rem; }
.metric-card.tone-good { border-top-color: var(--good); } .metric-card.tone-warn { border-top-color: #eab308; }
.metric-card.tone-bad { border-top-color: #f97316; } .metric-card.tone-crit { border-top-color: var(--crit); }
.metric-card.tone-info { border-top-color: #3b82f6; } .metric-card.tone-neutral { border-top-color: #94a3b8; }

/* Pills */
.pill { display: inline-block; padding: .2rem .65rem; border-radius: 999px; font-size: .74rem; font-weight: 700;
  letter-spacing: .02em; white-space: nowrap; }
.metric-card .pill { white-space: normal; line-height: 1.3; }
.pill-good { background: var(--good-bg); color: var(--good); } .pill-warn { background: var(--warn-bg); color: var(--warn); }
.pill-bad { background: var(--bad-bg); color: var(--bad); } .pill-crit { background: var(--crit-bg); color: var(--crit); }
.pill-info { background: var(--info-bg); color: var(--info); } .pill-neutral { background: var(--neutral-bg); color: var(--neutral); }

/* Generic cards */
.card { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: .7rem; }
.card .card-head { display: flex; justify-content: space-between; align-items: center; gap: .6rem; margin-bottom: .35rem; }
.card .card-title { font-weight: 700; color: var(--ink); font-size: .98rem; }
.card .meta { font-size: .78rem; color: var(--muted); }
.card .body { font-size: .9rem; color: var(--ink-2); margin-top: .35rem; line-height: 1.5; }
.card .ref { font-family: 'JetBrains Mono', monospace; font-size: .72rem; color: var(--accent-ink); margin-top: .45rem; }
.card.sev-crit { border-left: 5px solid var(--crit); } .card.sev-bad { border-left: 5px solid #f97316; }
.card.sev-warn { border-left: 5px solid #eab308; } .card.sev-good { border-left: 5px solid var(--good); }

/* PPE tile */
.ppe { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: .9rem 1rem; height: 100%; }
.ppe .name { font-weight: 700; color: var(--ink); margin-bottom: .45rem; font-size: .92rem; }
.ppe .notes { font-size: .8rem; color: var(--muted); margin-top: .5rem; line-height: 1.4; }

/* Alert banner */
.banner { border-radius: 14px; padding: 1rem 1.2rem; margin: .4rem 0 1rem; display: flex; gap: .9rem; align-items: flex-start; }
.banner .ic { font-size: 1.8rem; line-height: 1; }
.banner .t { font-weight: 800; font-size: 1.02rem; }
.banner .d { font-size: .9rem; margin-top: .15rem; }
.banner.tone-good { background: var(--good-bg); color: #14532d; } .banner.tone-warn { background: var(--warn-bg); color: #713f12; }
.banner.tone-bad { background: var(--bad-bg); color: #7c2d12; } .banner.tone-crit { background: var(--crit-bg); color: #7f1d1d; }
.banner.tone-info { background: var(--info-bg); color: #1e3a8a; }

/* Milestone tracker */
.mtrack { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: .5rem; margin-top: .6rem; }
.mstep { border-radius: 12px; padding: .6rem .7rem; border: 1px solid var(--line); background: var(--card); font-size: .8rem; }
.mstep .pct { font-family: 'JetBrains Mono', monospace; font-size: .7rem; color: var(--muted); }
.mstep .nm { font-weight: 650; color: var(--ink-2); margin-top: .15rem; line-height: 1.25; }
.mstep.done { background: var(--good-bg); border-color: #86efac; } .mstep.done .nm { color: #14532d; }
.mstep.current { background: #fffbeb; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(245,158,11,.25); }
.mstep.current .nm { color: var(--accent-ink); }

/* Activity table */
.atable { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .88rem; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.atable th { text-align: left; background: var(--surface); color: var(--muted); font-weight: 600; font-size: .74rem;
  text-transform: uppercase; letter-spacing: .06em; padding: .6rem .8rem; }
.atable td { padding: .6rem .8rem; border-top: 1px solid var(--line); color: var(--ink-2); background: var(--card); }

/* Score bar */
.scorebar { height: 12px; border-radius: 999px; background: #e2e8f0; overflow: hidden; margin: .5rem 0 1rem; }
.scorebar > div { height: 100%; border-radius: 999px; }

.small-muted { color: var(--muted); font-size: .82rem; }
section[data-testid="stSidebar"] .arch { font-family: 'JetBrains Mono', monospace; font-size: .72rem; line-height: 1.45;
  white-space: pre; background: #0f172a; color: #e2e8f0; padding: .8rem; border-radius: 10px; overflow-x: auto; }
div[data-testid="stTabs"] button[role="tab"] p { font-weight: 650; }
</style>
"""


def e(text: object) -> str:
    """Escape any value for safe HTML embedding (model output is untrusted)."""
    return html.escape(str(text), quote=True)


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(mode_label: str, mode_tone: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">Skill Wallet · Capstone Project 1</div>
          <h1>Multimodal Construction Intelligence Platform</h1>
          <p>AI-assisted decision support for site safety, structural diagnostics, project valuation and
          weather-aware daily operations, powered by Google Gemini.</p>
          <div class="chips">
            <span class="pill pill-{mode_tone}">{e(mode_label)}</span>
            <span class="chip">Vision + Language</span><span class="chip">Strict JSON contracts</span>
            <span class="chip">OSHA · BOCW · IS 456</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, tag: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="section-title"><h3>{e(title)}</h3><span class="tag">{e(tag)}</span></div>'
        f'<div class="section-sub">{e(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def pill(text: str, tone: str) -> str:
    tone = tone if tone in TONES else "neutral"
    return f'<span class="pill pill-{tone}">{e(text)}</span>'


def metric_card(label: str, value: str, sub: str = "", tone: str = "neutral") -> None:
    tone = tone if tone in TONES else "neutral"
    sub_html = f'<div class="sub">{e(sub)}</div>' if sub else ""
    st.markdown(
        f'<div class="metric-card tone-{tone}"><div class="label">{e(label)}</div>'
        f'<div class="value">{e(value)}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def metric_card_html(label: str, value_html: str, sub: str = "", tone: str = "neutral") -> None:
    """Like metric_card but ``value_html`` is trusted markup (e.g. a pill)."""
    tone = tone if tone in TONES else "neutral"
    sub_html = f'<div class="sub">{e(sub)}</div>' if sub else ""
    st.markdown(
        f'<div class="metric-card tone-{tone}"><div class="label">{e(label)}</div>'
        f'<div class="value" style="font-size:1rem;margin-top:.55rem">{value_html}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def score_bar(score: int) -> None:
    color = "#16a34a" if score >= 80 else "#eab308" if score >= 50 else "#dc2626"
    st.markdown(
        f'<div class="scorebar"><div style="width:{max(0, min(100, score))}%;background:{color}"></div></div>',
        unsafe_allow_html=True,
    )


def ppe_tile(name: str, status: str, compliant: int, total: int, notes: str) -> None:
    count = f"{compliant}/{total} workers" if total and status not in ("Not Visible", "Not Applicable") else ""
    st.markdown(
        f'<div class="ppe"><div class="name">{e(name)}</div>{pill(status, PPE_TONE.get(status, "neutral"))}'
        f'<span class="small-muted" style="margin-left:.5rem">{e(count)}</span>'
        f'<div class="notes">{e(notes) if notes else "&nbsp;"}</div></div>',
        unsafe_allow_html=True,
    )


def issue_card(title: str, severity: str, meta: str, body: str, ref: str = "", body_label: str = "Remedy") -> None:
    tone = SEVERITY_TONE.get(severity, "neutral")
    ref_html = f'<div class="ref">{e(ref)}</div>' if ref else ""
    body_html = f'<div class="body"><b>{e(body_label)}:</b> {e(body)}</div>' if body else ""
    st.markdown(
        f'<div class="card sev-{tone}"><div class="card-head"><div class="card-title">{e(title)}</div>'
        f'{pill(severity, tone)}</div><div class="meta">{e(meta)}</div>{body_html}{ref_html}</div>',
        unsafe_allow_html=True,
    )


def info_card(title: str, body: str, meta: str = "") -> None:
    meta_html = f'<div class="meta">{e(meta)}</div>' if meta else ""
    st.markdown(
        f'<div class="card"><div class="card-title">{e(title)}</div>{meta_html}<div class="body">{e(body)}</div></div>',
        unsafe_allow_html=True,
    )


def banner(icon: str, title: str, detail: str, tone: str) -> None:
    st.markdown(
        f'<div class="banner tone-{tone}"><div class="ic">{e(icon)}</div>'
        f'<div><div class="t">{e(title)}</div><div class="d">{e(detail)}</div></div></div>',
        unsafe_allow_html=True,
    )


def milestone_tracker(states: list[tuple[int, str, str]]) -> None:
    steps = "".join(
        f'<div class="mstep {state}"><div class="pct">{"✓ " if state == "done" else "● " if state == "current" else ""}{pct}%</div>'
        f'<div class="nm">{e(name)}</div></div>'
        for pct, name, state in states
    )
    st.markdown(f'<div class="mtrack">{steps}</div>', unsafe_allow_html=True)


def activity_table(rows: list[tuple[str, str, str]]) -> None:
    body = "".join(
        f"<tr><td><b>{e(a)}</b></td><td>{pill(s, GO_TONE.get(s, 'neutral'))}</td><td>{e(n) or '—'}</td></tr>"
        for a, s, n in rows
    )
    st.markdown(
        f'<table class="atable"><thead><tr><th>Activity</th><th>Status</th><th>Note</th></tr></thead>'
        f"<tbody>{body}</tbody></table>",
        unsafe_allow_html=True,
    )
