# 🏗️ Multimodal Construction Intelligence Platform

**Skill Wallet Capstone Project 1.** This is an AI-powered decision-support app for construction professionals, built with Streamlit and Google Gemini (multimodal vision + language).

## Modules

| Tab | Epic | What it does |
|---|---|---|
| 🦺 Site Safety & PPE Audit | 2 | Analyses a site photo for helmets, high-vis vests, steel-toe boots and harnesses (OSHA 1926, BOCW Act, IS 2925/3521). Returns a safety score from 0 to 100, a status, a PPE checklist, and hazards with severity and remedies. You can download the result as a JSON report. |
| 🧱 Crack Diagnostics | 2 | Classifies the defect as Hairline, Settlement, Structural Shear, Thermal Expansion or Spalling. Estimates crack width in mm against the IS 456 0.3 mm limit, and lists root causes, repairs (epoxy injection, stitching, re-grouting) and urgency. |
| 📐 Planning & Valuation | 3 | Computes the budget, capex incurred, current and completed asset value in ₹ Lakhs/Crores, and steel, cement, sand and aggregate quantities. Includes a milestone tracker and a Pollinations AI concept render. |
| 🌦️ Site Assistant & Weather | 5 | Gives weather-driven alerts (crane suspension, electrical isolation, hot-weather concreting), a go/no-go activity matrix and a curing protocol. Also includes SiteMate, a multi-turn engineering chatbot. |

If no API key is supplied, the app runs in **demonstration mode** with realistic sample outputs, so every screen still works.

## Architecture

```
app.py                 # entry point: page config, sidebar, tabs
core/
  gemini_client.py     # google-genai wrapper, JSON extraction, friendly errors
  prompts.py           # vision prompts with strict JSON contracts + chat system prompt
  schemas.py           # validates/normalises model JSON so the UI never breaks
  valuation.py         # cost, valuation, materials, milestones, render prompt
  weather.py           # rule-based advisories and activity matrix
  demo_data.py         # sample outputs for demonstration mode
ui/
  components.py        # CSS + escaped HTML components (cards, pills, banners)
  tabs.py              # one render function per tab
```

There is no database. All state lives in `st.session_state`.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Paste your Gemini API key in the sidebar (get one free at https://aistudio.google.com/apikey), or create `.streamlit/secrets.toml` from the example file.

## Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repo. `secrets.toml` is already in `.gitignore`.
2. Go to share.streamlit.io, choose **New app**, pick the repo, and set the main file to `app.py`.
3. Optional: under **Advanced settings → Secrets**, add `GEMINI_API_KEY = "..."` so the app starts in live mode.
4. Deploy.

## Notes and limitations

- Valuation rates are indicative 2025–26 averages. Edit the `STRUCTURES` table in `core/valuation.py` to tune them.
- Crack widths from a photo are estimates. Put a coin or scale in the frame for better results.
- AI outputs support engineering judgement and do not replace it. Structural and safety decisions need a licensed engineer.

## Android app (APK)

A Streamlit app runs on a Python server, so the APK is a native WebView wrapper around your **deployed** app URL. It supports photo uploads from the gallery, the back button, and an offline/retry screen.

1. Deploy the app on Streamlit Community Cloud first and copy its URL (e.g. `https://my-app.streamlit.app`).
2. Push this repo to GitHub, including the `android-app/` and `.github/` folders.
3. On GitHub, open **Actions → Build Android APK → Run workflow**, paste the URL, and run it. The build takes about 3–5 minutes.
4. Open the finished run and download **ConstructionIntel-apk** under *Artifacts*. Unzip it to get `app-debug.apk`.
5. Copy the APK to your phone, allow **Install unknown apps** for your file manager, and install it.

To build locally instead, install Android Studio, open `android-app/`, set `appUrl=https://...` in `android-app/gradle.properties`, and run **Build → Build APK(s)**.
