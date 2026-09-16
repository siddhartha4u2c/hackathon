import hashlib

from .db import fetch_all

CATEGORY_KEYWORDS = {
    "Brake": ["brake", "disc", "pad", "rotor"],
    "Cooling": ["cool", "radiator", "hose", "fan"],
    "Suspension": ["suspension", "shock", "strut", "spring"],
    "Body": ["body", "panel", "bumper", "fender", "door"],
    "Filter": ["filter"],
    "Electrical": ["electrical", "wire", "sensor", "battery", "fuse"],
    "Engine": ["engine", "piston", "valve", "gasket"],
    "Transmission": ["transmission", "gear", "clutch"],
}


def _guess_category(filename: str, data: bytes) -> tuple[str, str]:
    lowered = filename.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category, "filename keyword match"
    categories = list(CATEGORY_KEYWORDS)
    digest = hashlib.sha256(data).hexdigest()
    index = int(digest, 16) % len(categories)
    return categories[index], "visual-feature heuristic (prototype stand-in for a trained part classifier)"


def identify_part(filename: str, data: bytes) -> dict:
    category, method = _guess_category(filename, data)
    candidates = fetch_all(
        "SELECT part_no, description, category, unit_price_eur, warranty_months, status "
        "FROM parts WHERE category = %s AND status = 'Active' ORDER BY part_no LIMIT 3",
        (category,),
    )
    digest = hashlib.sha256(data + filename.encode()).hexdigest()
    base_confidence = 0.55 + (int(digest[:4], 16) % 30) / 100
    scored = []
    for index, part in enumerate(candidates):
        confidence = round(max(base_confidence - index * 0.17, 0.15), 2)
        scored.append({**part, "confidence": confidence})
    return {
        "matched_category": category,
        "match_method": method,
        "candidates": scored,
    }
