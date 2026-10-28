"""Validation/normalisation of model output.

LLM JSON can drift: wrong casing, missing keys, numbers as strings. These
functions coerce any dict into a guaranteed shape so the UI never crashes.
"""
from __future__ import annotations

from typing import Any, Iterable

SEVERITIES = ["Low", "Medium", "High", "Critical"]
STATUSES = ["Compliant", "Partially Compliant", "Non-Compliant"]
PPE_STATUSES = ["Detected", "Partial", "Missing", "Not Visible", "Not Applicable"]
PPE_ITEMS = {
    "helmet": "Safety Helmet",
    "high_vis_vest": "High-Vis Vest",
    "steel_toe_boots": "Steel-Toe Boots",
    "safety_harness": "Safety Harness",
}
DEFECT_TYPES = ["Hairline", "Settlement", "Structural Shear", "Thermal Expansion", "Spalling", "No Defect"]
URGENCIES = [
    "Monitor",
    "Planned Repair (within 3 months)",
    "Priority Repair (within 2 weeks)",
    "Immediate Action",
]
ORIENTATIONS = ["Vertical", "Horizontal", "Diagonal", "Stepped", "Map / Random", "Not Applicable"]


def _clamp_int(value: Any, lo: int, hi: int, default: int) -> int:
    try:
        return max(lo, min(hi, int(round(float(value)))))
    except (TypeError, ValueError):
        return default


def _clamp_float(value: Any, lo: float, hi: float, default: float) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return default


def _pick(value: Any, allowed: Iterable[str], default: str | None) -> str | None:
    if isinstance(value, str):
        v = value.strip().lower()
        for option in allowed:
            if v == option.lower():
                return option
        # tolerate small variants, e.g. "non compliant" / "partially-compliant"
        compact = v.replace("-", " ").replace("_", " ")
        for option in allowed:
            if compact == option.lower().replace("-", " "):
                return option
    return default


def _str(value: Any, default: str = "") -> str:
    return str(value).strip() if value is not None else default


def _str_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return []


# --------------------------------------------------------------------------- #
def normalize_safety(raw: Any) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    score = _clamp_int(raw.get("safety_score"), 0, 100, 0)
    status = _pick(raw.get("overall_status"), STATUSES, None)
    if status is None:
        status = "Compliant" if score >= 80 else "Partially Compliant" if score >= 50 else "Non-Compliant"

    ppe_raw = raw.get("ppe_detection") if isinstance(raw.get("ppe_detection"), dict) else {}
    ppe: dict[str, dict[str, Any]] = {}
    for key in PPE_ITEMS:
        item = ppe_raw.get(key, {})
        if isinstance(item, str):
            item = {"status": item}
        if not isinstance(item, dict):
            item = {}
        ppe[key] = {
            "status": _pick(item.get("status"), PPE_STATUSES, "Not Visible"),
            "compliant_workers": _clamp_int(item.get("compliant_workers"), 0, 999, 0),
            "notes": _str(item.get("notes")),
        }

    hazards = []
    for h in raw.get("hazards") or []:
        if not isinstance(h, dict):
            continue
        hazards.append(
            {
                "hazard": _str(h.get("hazard"), "Unspecified hazard") or "Unspecified hazard",
                "category": _str(h.get("category"), "Other") or "Other",
                "severity": _pick(h.get("severity"), SEVERITIES, "Medium"),
                "location": _str(h.get("location")),
                "remedy": _str(h.get("remedy")),
                "standard_reference": _str(h.get("standard_reference")),
            }
        )
    hazards.sort(key=lambda h: SEVERITIES.index(h["severity"]), reverse=True)

    return {
        "image_valid": bool(raw.get("image_valid", True)),
        "safety_score": score,
        "overall_status": status,
        "workers_detected": _clamp_int(raw.get("workers_detected"), 0, 999, 0),
        "summary": _str(raw.get("summary")),
        "ppe_detection": ppe,
        "hazards": hazards,
        "recommendations": _str_list(raw.get("recommendations")),
    }


def normalize_crack(raw: Any) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    repairs = []
    for r in raw.get("recommended_repairs") or []:
        if isinstance(r, str):
            r = {"method": r}
        if not isinstance(r, dict):
            continue
        repairs.append(
            {
                "method": _str(r.get("method"), "Repair") or "Repair",
                "description": _str(r.get("description")),
                "materials": _str(r.get("materials")),
            }
        )

    return {
        "image_valid": bool(raw.get("image_valid", True)),
        "defect_type": _pick(raw.get("defect_type"), DEFECT_TYPES, "No Defect"),
        "confidence": round(_clamp_float(raw.get("confidence"), 0.0, 1.0, 0.0), 2),
        "estimated_crack_width_mm": round(_clamp_float(raw.get("estimated_crack_width_mm"), 0.0, 100.0, 0.0), 2),
        "orientation": _pick(raw.get("orientation"), ORIENTATIONS, "Not Applicable"),
        "severity": _pick(raw.get("severity"), SEVERITIES, "Low"),
        "urgency": _pick(raw.get("urgency"), URGENCIES, "Monitor"),
        "summary": _str(raw.get("summary")),
        "structural_risk": _str(raw.get("structural_risk")),
        "root_causes": _str_list(raw.get("root_causes")),
        "recommended_repairs": repairs,
        "monitoring_advice": _str(raw.get("monitoring_advice")),
        "code_reference": _str(raw.get("code_reference")),
    }


def width_band(width_mm: float) -> str:
    """Qualitative crack-width band (common practice, aligned with IS 456 Cl. 35.3.2)."""
    if width_mm <= 0:
        return "None"
    if width_mm < 0.1:
        return "Very fine (< 0.1 mm)"
    if width_mm <= 0.3:
        return "Fine (0.1 – 0.3 mm) · within IS 456 limit"
    if width_mm <= 1.0:
        return "Moderate (0.3 – 1 mm) · exceeds IS 456 limit"
    if width_mm <= 5.0:
        return "Wide (1 – 5 mm)"
    return "Severe (> 5 mm)"
