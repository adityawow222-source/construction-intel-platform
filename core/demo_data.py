"""Canned responses used when no Gemini API key is configured (demonstration mode)."""
from __future__ import annotations

DEMO_SAFETY = {
    "image_valid": True,
    "safety_score": 62,
    "overall_status": "Partially Compliant",
    "workers_detected": 6,
    "summary": (
        "Six workers are active on a G+4 RCC frame under construction. Helmets are mostly worn, "
        "but vests are inconsistent and one worker on the slab edge has no fall protection."
    ),
    "ppe_detection": {
        "helmet": {"status": "Partial", "compliant_workers": 5, "notes": "One worker near the mixer is bareheaded."},
        "high_vis_vest": {"status": "Partial", "compliant_workers": 3, "notes": "Three workers in plain clothing."},
        "steel_toe_boots": {"status": "Not Visible", "compliant_workers": 0, "notes": "Feet obscured by rebar and debris."},
        "safety_harness": {"status": "Missing", "compliant_workers": 0, "notes": "Worker at 4th-floor slab edge without harness or lifeline."},
    },
    "hazards": [
        {
            "hazard": "Unprotected slab edge at height",
            "category": "Fall",
            "severity": "Critical",
            "location": "Top-right, 4th floor slab",
            "remedy": "Stop work at edge; install 1 m guardrail with toe board or safety net; issue IS 3521 full-body harness anchored to a rated lifeline.",
            "standard_reference": "OSHA 1926.501(b)(1); BOCW Central Rules 1998, Rule 40",
        },
        {
            "hazard": "Protruding rebar without caps",
            "category": "Struck-by",
            "severity": "High",
            "location": "Foreground column starters",
            "remedy": "Fit mushroom caps or bend over exposed bar ends; barricade the zone.",
            "standard_reference": "OSHA 1926.701(b)",
        },
        {
            "hazard": "Loose cables across walkway",
            "category": "Electrical",
            "severity": "Medium",
            "location": "Centre, near concrete mixer",
            "remedy": "Route cables overhead or in protective conduit; use ELCB/RCCB-protected distribution board.",
            "standard_reference": "OSHA 1926.405; IS 3043",
        },
        {
            "hazard": "Cement bags stacked above 10 high",
            "category": "Material Handling",
            "severity": "Low",
            "location": "Left side, storage area",
            "remedy": "Restack to max 10 bags high on raised platform, 150 mm off the ground.",
            "standard_reference": "IS 7969; IS 4082",
        },
    ],
    "recommendations": [
        "Halt edge work immediately until fall protection is in place.",
        "Enforce PPE at site entry gate with a sign-in checklist.",
        "Conduct a 15-minute toolbox talk on fall hazards today.",
        "Cap all rebar and re-route temporary electrical lines.",
    ],
}

DEMO_CRACK = {
    "image_valid": True,
    "defect_type": "Settlement",
    "confidence": 0.78,
    "estimated_crack_width_mm": 1.5,
    "orientation": "Stepped",
    "severity": "High",
    "urgency": "Priority Repair (within 2 weeks)",
    "summary": (
        "A stepped diagonal crack runs from the window corner through the mortar joints of a brick infill wall. "
        "The pattern and taper indicate differential settlement of the supporting foundation."
    ),
    "structural_risk": (
        "Progressive widening may distort door/window frames, allow water ingress into the wall, and indicate "
        "ongoing foundation movement that could affect the plinth beam."
    ),
    "root_causes": [
        "Differential settlement from uneven soil bearing or poor compaction under one footing",
        "Moisture variation in expansive (black cotton) soil",
        "Absence of lintel-level band and corner reinforcement around the opening",
    ],
    "recommended_repairs": [
        {
            "method": "Monitor before repair",
            "description": "Fix glass tell-tales or a crack-width gauge for 4–6 weeks to confirm whether movement has stabilised.",
            "materials": "Glass tell-tales, crack-width comparator card, dated photos",
        },
        {
            "method": "Low-pressure epoxy injection",
            "description": "Once stable, seal the surface and inject low-viscosity epoxy to restore monolithic behaviour.",
            "materials": "Low-viscosity epoxy resin, injection ports, epoxy paste sealer",
        },
        {
            "method": "Stitching with helical ties",
            "description": "Insert stainless-steel helical bars across the crack in bed joints at 450 mm c/c and re-point.",
            "materials": "6 mm SS helical ties, polymer-modified grout",
        },
        {
            "method": "Foundation investigation and re-grouting",
            "description": "If movement continues, carry out soil investigation and pressure-grout or underpin the affected footing.",
            "materials": "Cement-bentonite grout, micro-piles if required",
        },
    ],
    "monitoring_advice": "Record crack width weekly with a comparator card for 6 weeks; escalate if width grows by more than 0.5 mm.",
    "code_reference": "IS 456:2000 Cl. 35.3.2 (crack width limits); IS 1904 (foundations); IS 15988 (repair & retrofit)",
}

_DEMO_CHAT_RULES = [
    (("crack", "fissure"),
     "For cracks, first classify them by width and pattern:\n\n"
     "- **< 0.3 mm**: usually shrinkage. Seal with a polymer-modified cementitious slurry.\n"
     "- **0.3 – 5 mm, stable**: low-pressure epoxy injection (structural) or PU injection (if leaking).\n"
     "- **Diagonal at 45° in beams/columns**: possible shear distress. Get a structural engineer to inspect before repairing.\n\n"
     "Always monitor with tell-tales for a few weeks to confirm the crack is not still moving."),
    (("curing", "cure"),
     "IS 456 Cl. 13.5.1 requires moist curing for at least **7 days** with OPC and **10 days** with "
     "blended cements (PPC/PSC), extended to 10–14 days in hot, dry weather. Use wet hessian, ponding on slabs "
     "(25 mm water dams), or a curing compound conforming to ASTM C309 where water is scarce."),
    (("mix", "m20", "m25", "ratio", "concrete"),
     "Nominal mix ratios (cement : sand : aggregate):\n\n"
     "- **M15**: 1 : 2 : 4\n- **M20**: 1 : 1.5 : 3 (about 8 bags cement per m³)\n- **M25 and above**: design mix per IS 10262.\n\n"
     "Keep the water–cement ratio at or below 0.50 for M20 in moderate exposure (IS 456 Table 5)."),
    (("steel", "rebar", "reinforcement"),
     "Thumb-rule steel consumption for RCC framed buildings: **3.5 – 4.5 kg per sq ft** of built-up area. "
     "Typical split: footings ~0.8%, columns 1–4%, beams ~2%, slabs ~1% of concrete volume. Use Fe500/Fe500D "
     "bars to IS 1786 and keep lap lengths at 50d in tension zones."),
    (("cement", "bag"),
     "A useful thumb rule is **0.4 – 0.45 bags of cement per sq ft** of built-up area for a residential RCC "
     "building, covering structure, masonry and plaster. Store bags 150 mm off the floor, no more than 10 high, "
     "and use first-in-first-out within 90 days."),
    (("rain", "monsoon", "wind", "heat", "weather"),
     "Weather rules of thumb:\n\n"
     "- **Wind > 45 km/h**: suspend crane and hoist lifts.\n"
     "- **Heavy rain**: stop concreting, cover fresh pours, isolate temporary electrical boards.\n"
     "- **Above 40 °C**: pour early morning or at night, chill mixing water, and keep fresh concrete below 35 °C."),
    (("ppe", "helmet", "harness", "safety"),
     "Minimum PPE on an Indian site: an IS 2925 helmet, high-vis vest, safety shoes (IS 15298), and gloves. "
     "Anyone working above 1.8 m needs an IS 3521 full-body harness anchored to a rated point. Run a daily "
     "toolbox talk and keep a PPE issue register."),
]

DEMO_CHAT_FALLBACK = (
    "I'm running in **demonstration mode**, so I can only answer a handful of common topics: cracks, curing, "
    "concrete mix ratios, steel and cement quantities, weather precautions, and PPE. Add a Gemini API key in "
    "the sidebar to ask me anything about construction."
)


def demo_chat_reply(message: str) -> str:
    text = message.lower()
    for keywords, reply in _DEMO_CHAT_RULES:
        if any(k in text for k in keywords):
            return reply + "\n\n_Demo mode reply. Add an API key for full answers._"
    return DEMO_CHAT_FALLBACK
