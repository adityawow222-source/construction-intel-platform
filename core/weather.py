"""Rule-based weather-aware site advisory engine (Epic 5)."""
from __future__ import annotations

WEATHER_CONDITIONS = ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"]

ADVISORIES: dict[str, dict] = {
    "Normal": {
        "icon": "☀️",
        "tone": "good",
        "level": "All Clear",
        "headline": "Standard operating conditions. All planned activities may proceed.",
        "trigger": "Wind < 30 km/h · No precipitation · 15–35 °C",
        "alerts": [
            ("Routine", "Carry out the daily pre-start inspection of cranes, scaffolds and electrical boards."),
            ("Routine", "Confirm PPE compliance at the gate and hold a 10-minute toolbox talk."),
            ("Planning", "Good window for concreting, external plaster and waterproofing."),
        ],
        "curing": "Standard moist curing: minimum 7 days for OPC and 10 days for PPC/PSC (IS 456 Cl. 13.5.1).",
    },
    "High Wind": {
        "icon": "🌬️",
        "tone": "bad",
        "level": "Restricted Operations",
        "headline": "Suspend all crane and hoist lifting. Secure loose material and work at height.",
        "trigger": "Sustained wind > 45 km/h or gusts > 60 km/h",
        "alerts": [
            ("Critical", "Suspend tower crane, mobile crane and material hoist operations. Put the tower crane jib into free slew."),
            ("High", "Stop work on scaffolds, roof edges and facades. Clear workers from all open slab edges."),
            ("High", "Tie down or remove loose sheets, formwork panels, shuttering plywood and tarpaulins."),
            ("Medium", "Inspect scaffold ties and safety nets for damage after the wind subsides, before re-entry."),
            ("Medium", "Postpone spray painting and external plaster, since wind causes rapid drying and overspray."),
        ],
        "curing": "Wind accelerates surface evaporation. Cover fresh concrete immediately with wet hessian or polythene and erect windbreaks to prevent plastic shrinkage cracking.",
    },
    "Heavy Rain": {
        "icon": "🌧️",
        "tone": "bad",
        "level": "Restricted Operations",
        "headline": "Stop concreting and excavation work. Isolate temporary electrical installations.",
        "trigger": "Rainfall > 7.5 mm/h or IMD orange/red alert",
        "alerts": [
            ("Critical", "Electrical hazard: switch off and isolate outdoor distribution boards. Check that ELCB/RCCB devices trip correctly. Keep cables off waterlogged ground."),
            ("High", "Stop excavation work. Inspect trench sides for slumping and keep dewatering pumps running."),
            ("High", "Do not pour concrete. Cover fresh pours with polythene sheets and plan construction joints."),
            ("Medium", "Suspend work on scaffolds and ladders because surfaces become slippery. Re-inspect them before resuming."),
            ("Medium", "Protect cement bags and steel on raised, covered platforms to prevent setting and corrosion."),
        ],
        "curing": "Rain is not a substitute for controlled curing. Protect fresh concrete (less than 12 hours old) from washout of fines. Resume moist curing once the rain stops and check for surface scaling.",
    },
    "Extreme Heat": {
        "icon": "🔥",
        "tone": "warn",
        "level": "Modified Operations",
        "headline": "Reschedule heavy work to cooler hours. Apply hot-weather concreting controls.",
        "trigger": "Air temperature > 40 °C or heat index > 45 °C",
        "alerts": [
            ("Critical", "Heat stress: shift heavy manual work to 6–11 AM and after 4 PM. Provide shaded rest areas, ORS and drinking water every 20 minutes."),
            ("High", "Hot-weather concreting (IS 7861 Part 1): keep concrete temperature at placement below 35 °C. Use chilled water or ice and retarding admixtures, and pour at night."),
            ("Medium", "Wet subgrade, formwork and reinforcement before placing concrete to avoid rapid moisture loss."),
            ("Medium", "Run a buddy system for heat exhaustion symptoms such as dizziness, nausea and cramps. Keep a first-aid responder on standby."),
            ("Low", "Store admixtures, paints and adhesives in shade. Check the bitumen application temperature."),
        ],
        "curing": "Start curing as soon as the surface can take it. Extend moist curing to 10–14 days and use ponding or a curing compound (ASTM C309) to limit evaporation.",
    },
}

# activity -> condition -> (status, note)
ACTIVITY_MATRIX: dict[str, dict[str, tuple[str, str]]] = {
    "Crane / hoist lifting": {
        "Normal": ("Go", ""), "High Wind": ("No-Go", "Wind exceeds crane limits"),
        "Heavy Rain": ("Caution", "Reduced visibility, wet slings"), "Extreme Heat": ("Go", "Rotate operators"),
    },
    "Concrete pouring": {
        "Normal": ("Go", ""), "High Wind": ("Caution", "Windbreaks and immediate cover"),
        "Heavy Rain": ("No-Go", "Washout risk"), "Extreme Heat": ("Caution", "Pour at night, keep < 35 °C"),
    },
    "Work at height / scaffolds": {
        "Normal": ("Go", ""), "High Wind": ("No-Go", "Fall and blow-off risk"),
        "Heavy Rain": ("No-Go", "Slippery surfaces"), "Extreme Heat": ("Caution", "Limit exposure duration"),
    },
    "Excavation / earthwork": {
        "Normal": ("Go", ""), "High Wind": ("Go", "Dust control"),
        "Heavy Rain": ("No-Go", "Trench collapse risk"), "Extreme Heat": ("Caution", "Morning shifts only"),
    },
    "Electrical / welding": {
        "Normal": ("Go", ""), "High Wind": ("Caution", "Spark spread risk"),
        "Heavy Rain": ("No-Go", "Electrocution risk"), "Extreme Heat": ("Caution", "Hydration for welders"),
    },
    "Masonry & plastering": {
        "Normal": ("Go", ""), "High Wind": ("Caution", "Rapid drying"),
        "Heavy Rain": ("Caution", "Internal work only"), "Extreme Heat": ("Caution", "Pre-wet bricks, cure often"),
    },
}
