from .db import fetch_all, fetch_one


def _region(warehouse_loc: str) -> str:
    parts = warehouse_loc.split("-")
    return parts[1] if len(parts) > 1 else warehouse_loc


def stock_positions(part_no: str | None = None) -> list[dict]:
    query = (
        "SELECT i.part_no, i.warehouse_loc, i.available_qty, i.reorder_point, "
        "p.description, p.unit_price_eur FROM inventory i JOIN parts p ON p.part_no = i.part_no"
    )
    params: tuple = ()
    if part_no:
        query += " WHERE i.part_no = %s"
        params = (part_no,)
    return fetch_all(query, params)


def transfer_suggestions(part_no: str | None = None, limit: int = 10) -> list[dict]:
    positions_by_part: dict[str, list[dict]] = {}
    for row in stock_positions(part_no):
        positions_by_part.setdefault(row["part_no"], []).append(row)

    suggestions = []
    for pno, positions in positions_by_part.items():
        deficits = [row for row in positions if row["available_qty"] < row["reorder_point"]]
        surpluses = [row for row in positions if row["available_qty"] > row["reorder_point"]]
        for deficit in deficits:
            needed = deficit["reorder_point"] - deficit["available_qty"]
            best = None
            for surplus in surpluses:
                if surplus["warehouse_loc"] == deficit["warehouse_loc"]:
                    continue
                spare = surplus["available_qty"] - surplus["reorder_point"]
                if spare <= 0:
                    continue
                if best is None or spare > best["spare"]:
                    best = {"row": surplus, "spare": spare}
            if not best:
                continue
            transfer_qty = min(needed, best["spare"])
            unit_price = float(deficit["unit_price_eur"] or 0)
            suggestions.append({
                "part_no": pno,
                "description": deficit["description"],
                "from_warehouse": best["row"]["warehouse_loc"],
                "from_region": _region(best["row"]["warehouse_loc"]),
                "to_warehouse": deficit["warehouse_loc"],
                "to_region": _region(deficit["warehouse_loc"]),
                "transfer_qty": transfer_qty,
                "transfer_value_eur": round(unit_price * transfer_qty, 2),
            })
    suggestions.sort(key=lambda item: item["transfer_value_eur"], reverse=True)
    return suggestions[:limit]


def metrics() -> dict:
    claims_by_status = fetch_all("SELECT claim_status, COUNT(*) AS n FROM claims GROUP BY 1 ORDER BY 1")
    po_by_status = fetch_all("SELECT po_status, COUNT(*) AS n FROM purchase_orders GROUP BY 1 ORDER BY 1")
    shipment_by_status = fetch_all("SELECT shipment_status, COUNT(*) AS n FROM shipments GROUP BY 1 ORDER BY 1")

    total_claims = fetch_one("SELECT COUNT(*) AS n FROM claims")["n"]
    resolved_claims = fetch_one(
        "SELECT COUNT(*) AS n FROM claims WHERE claim_status IN ('Approved', 'Paid')"
    )["n"]
    open_exposure = fetch_one(
        "SELECT COALESCE(SUM(claim_amount_eur), 0) AS v FROM claims WHERE claim_status IN ('Open', 'Pending Info')"
    )["v"]
    backordered_pos = fetch_one("SELECT COUNT(*) AS n FROM purchase_orders WHERE po_status = 'Backordered'")["n"]
    deficit_lines = fetch_one(
        "SELECT COUNT(*) AS n FROM inventory WHERE available_qty < reorder_point"
    )["n"]

    suggestions = transfer_suggestions(limit=8)
    potential_transfer_value = round(sum(item["transfer_value_eur"] for item in suggestions), 2)
    self_service_rate = round(100 * resolved_claims / total_claims, 1) if total_claims else 0.0

    region_health: dict[str, dict] = {}
    for row in fetch_all("SELECT warehouse_loc, available_qty, reorder_point FROM inventory"):
        bucket = region_health.setdefault(
            _region(row["warehouse_loc"]), {"deficit_lines": 0, "surplus_lines": 0, "healthy_lines": 0}
        )
        if row["available_qty"] < row["reorder_point"]:
            bucket["deficit_lines"] += 1
        elif row["available_qty"] > row["reorder_point"]:
            bucket["surplus_lines"] += 1
        else:
            bucket["healthy_lines"] += 1

    return {
        "claims_by_status": claims_by_status,
        "po_by_status": po_by_status,
        "shipment_by_status": shipment_by_status,
        "roi": {
            "self_service_rate_pct": self_service_rate,
            "resolved_claims": resolved_claims,
            "total_claims": total_claims,
            "open_claim_exposure_eur": float(open_exposure),
            "backordered_pos": backordered_pos,
            "deficit_lines": deficit_lines,
            "potential_transfer_value_eur": potential_transfer_value,
        },
        "transfer_suggestions": suggestions,
        "region_health": region_health,
    }
