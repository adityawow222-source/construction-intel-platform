"""Deterministic cost, valuation and material estimation engine (Epic 3).

Rates are indicative 2025-26 Indian market averages for planning purposes only.
They are kept in one table so they can be tuned without touching UI code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote

TIERS = {
    "Tier 1": "Mumbai, Delhi NCR, Bengaluru, Hyderabad, Chennai, Pune, Kolkata, Ahmedabad",
    "Tier 2": "Indore, Nagpur, Jaipur, Lucknow, Bhopal, Surat, Coimbatore, Kochi",
    "Tier 3": "Smaller cities and towns",
}

# cost  = construction cost, INR per sq ft (structure + finishes, excluding land)
# market = completed-property market rate, INR per sq ft (includes land share)
# steel = kg per sq ft, cement = 50 kg bags per sq ft,
# sand / aggregate = cubic feet per sq ft
STRUCTURES: dict[str, dict] = {
    "Residential Apartment": {
        "cost": {"Tier 1": 2800, "Tier 2": 2200, "Tier 3": 1800},
        "market": {"Tier 1": 11000, "Tier 2": 5500, "Tier 3": 3600},
        "steel": 4.0, "cement": 0.40, "sand": 1.8, "aggregate": 1.35,
    },
    "Independent House / Villa": {
        "cost": {"Tier 1": 3200, "Tier 2": 2500, "Tier 3": 2000},
        "market": {"Tier 1": 14000, "Tier 2": 6500, "Tier 3": 4200},
        "steel": 3.8, "cement": 0.42, "sand": 1.9, "aggregate": 1.40,
    },
    "Commercial Office": {
        "cost": {"Tier 1": 3800, "Tier 2": 3000, "Tier 3": 2400},
        "market": {"Tier 1": 16000, "Tier 2": 8000, "Tier 3": 5000},
        "steel": 5.0, "cement": 0.45, "sand": 1.9, "aggregate": 1.50,
    },
    "Retail / Shopping Complex": {
        "cost": {"Tier 1": 4200, "Tier 2": 3300, "Tier 3": 2600},
        "market": {"Tier 1": 18000, "Tier 2": 9000, "Tier 3": 5500},
        "steel": 5.5, "cement": 0.48, "sand": 2.0, "aggregate": 1.55,
    },
    "Industrial Warehouse (PEB)": {
        "cost": {"Tier 1": 2200, "Tier 2": 1800, "Tier 3": 1500},
        "market": {"Tier 1": 6000, "Tier 2": 3500, "Tier 3": 2500},
        "steel": 6.0, "cement": 0.30, "sand": 1.2, "aggregate": 1.10,
    },
}

# Under-construction properties carry the land + approvals value from day one,
# and the remaining value accrues with physical progress.
LAND_AND_APPROVAL_SHARE = 0.30

MILESTONES = [
    (0, "Site Mobilisation & Excavation"),
    (10, "Foundation & Plinth"),
    (25, "RCC Superstructure"),
    (50, "Masonry & Roofing"),
    (65, "MEP Rough-ins"),
    (80, "Plastering & Flooring"),
    (92, "Finishing & Fixtures"),
    (100, "Handover"),
]


def format_inr(amount: float) -> str:
    """Format rupees as Crores / Lakhs / plain with Indian grouping."""
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    if amount >= 1e7:
        return f"{sign}₹{amount / 1e7:,.2f} Cr"
    if amount >= 1e5:
        return f"{sign}₹{amount / 1e5:,.2f} L"
    return f"{sign}₹{amount:,.0f}"


def format_indian_number(n: float) -> str:
    """1234567 -> '12,34,567'."""
    s = f"{int(round(n))}"
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


@dataclass
class Materials:
    steel_tonnes: float
    cement_bags: float
    sand_cft: float
    aggregate_cft: float


@dataclass
class ValuationResult:
    structure: str
    sqft: float
    tier: str
    completion_pct: float
    cost_rate: float
    market_rate: float
    base_cost: float
    contingency: float
    total_budget: float
    capex_incurred: float
    remaining_capex: float
    completed_value: float
    current_value: float
    value_created: float
    roi_on_completion_pct: float
    materials_total: Materials
    materials_consumed: Materials
    current_milestone: str
    next_milestone: str | None
    milestones: list[tuple[int, str, str]] = field(default_factory=list)


def compute_valuation(
    structure: str,
    sqft: float,
    tier: str,
    completion_pct: float,
    contingency_pct: float = 8.0,
) -> ValuationResult:
    if structure not in STRUCTURES:
        raise ValueError(f"Unknown structure type: {structure}")
    if tier not in TIERS:
        raise ValueError(f"Unknown location tier: {tier}")
    if sqft <= 0:
        raise ValueError("Built-up area must be greater than zero.")

    spec = STRUCTURES[structure]
    progress = max(0.0, min(100.0, completion_pct)) / 100.0

    cost_rate = spec["cost"][tier]
    market_rate = spec["market"][tier]

    base_cost = sqft * cost_rate
    contingency = base_cost * contingency_pct / 100.0
    total_budget = base_cost + contingency
    capex_incurred = total_budget * progress

    completed_value = sqft * market_rate
    current_value = completed_value * (LAND_AND_APPROVAL_SHARE + (1 - LAND_AND_APPROVAL_SHARE) * progress)

    total = Materials(
        steel_tonnes=sqft * spec["steel"] / 1000.0,
        cement_bags=sqft * spec["cement"],
        sand_cft=sqft * spec["sand"],
        aggregate_cft=sqft * spec["aggregate"],
    )
    consumed = Materials(
        steel_tonnes=total.steel_tonnes * progress,
        cement_bags=total.cement_bags * progress,
        sand_cft=total.sand_cft * progress,
        aggregate_cft=total.aggregate_cft * progress,
    )

    pct = progress * 100
    current = MILESTONES[0][1]
    next_m = None
    states = []
    for i, (threshold, name) in enumerate(MILESTONES):
        nxt = MILESTONES[i + 1][0] if i + 1 < len(MILESTONES) else 101
        if pct >= nxt or (threshold == 100 and pct >= 100):
            states.append((threshold, name, "done"))
        elif pct >= threshold:
            states.append((threshold, name, "current"))
            current = name
        else:
            states.append((threshold, name, "upcoming"))
            if next_m is None:
                next_m = name
    if pct >= 100:
        current = "Handover"

    return ValuationResult(
        structure=structure,
        sqft=sqft,
        tier=tier,
        completion_pct=pct,
        cost_rate=cost_rate,
        market_rate=market_rate,
        base_cost=base_cost,
        contingency=contingency,
        total_budget=total_budget,
        capex_incurred=capex_incurred,
        remaining_capex=total_budget - capex_incurred,
        completed_value=completed_value,
        current_value=current_value,
        value_created=current_value - capex_incurred,
        roi_on_completion_pct=(completed_value - total_budget) / total_budget * 100.0,
        materials_total=total,
        materials_consumed=consumed,
        current_milestone=current,
        next_milestone=next_m,
        milestones=states,
    )


# --------------------------------------------------------------------------- #
RENDER_STYLES = {
    "Photorealistic": "photorealistic architectural visualization, ultra detailed, 8k, ray traced lighting",
    "Modern Minimalist": "modern minimalist architecture, clean lines, glass and concrete, soft daylight",
    "Indian Contemporary": "contemporary Indian architecture, jaali screens, terracotta and stone cladding, landscaped courtyard",
    "Night View": "architectural night render, warm interior lights, dramatic sky, reflections",
    "Isometric Concept": "isometric 3D architectural concept model, white clay render, soft shadows",
}


def build_render_prompt(structure: str, sqft: float, tier: str, style: str, extra: str = "") -> str:
    setting = {
        "Tier 1": "dense metropolitan Indian city skyline",
        "Tier 2": "growing Indian city with wide roads and greenery",
        "Tier 3": "calm Indian town with open surroundings",
    }[tier]
    size = "compact" if sqft < 3000 else "mid-size" if sqft < 25000 else "large-scale"
    parts = [
        f"{size} {structure.lower()}",
        f"approximately {int(sqft):,} sq ft",
        f"set in a {setting}",
        RENDER_STYLES.get(style, ""),
        "exterior perspective, eye-level view, architectural rendering",
    ]
    if extra.strip():
        parts.append(extra.strip())
    return ", ".join(p for p in parts if p)


def pollinations_url(prompt: str, seed: int, width: int = 1024, height: int = 640) -> str:
    return (
        f"https://image.pollinations.ai/prompt/{quote(prompt, safe='')}"
        f"?width={width}&height={height}&seed={seed}&nologo=true"
    )
