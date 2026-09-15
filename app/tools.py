from datetime import date
from .db import fetch_all, fetch_one


def _json_value(value):
    return value.isoformat() if isinstance(value, (date,)) else value


def investigate_claim(claim_id: str) -> dict:
    claim = fetch_one("SELECT * FROM claims WHERE claim_id = %s", (claim_id,))
    if not claim:
        return {"found": False, "message": f"No claim was found for {claim_id}."}

    po = fetch_one(
        "SELECT * FROM purchase_orders WHERE po_no = %s ORDER BY po_line_no LIMIT 1",
        (claim["po_no"],),
    )
    shipment = fetch_one("SELECT * FROM shipments WHERE po_no = %s", (claim["po_no"],))
    part = fetch_one("SELECT * FROM parts WHERE part_no = %s", (claim["part_no"],))
    knowledge = fetch_all(
        """SELECT * FROM knowledge
           WHERE module ILIKE %s OR error_code = %s OR title ILIKE %s
           ORDER BY last_updated DESC LIMIT 5""",
        (f"%{claim['claim_type']}%", claim["resolution_code"], f"%{claim['reason']}%"),
    )
    issues = []
    if not po:
        issues.append("The claim references a purchase order that does not exist.")
    if claim["reason"] == "Not Received" and shipment and shipment["actual_delivery_date"]:
        issues.append("The claim says Not Received, but the linked shipment has an actual delivery date.")
    if part and claim["claim_date"] and claim["purchase_date"]:
        months = (claim["claim_date"].year - claim["purchase_date"].year) * 12
        months += claim["claim_date"].month - claim["purchase_date"].month
        if months > part["warranty_months"]:
            issues.append(f"The claim is {months} months after purchase, beyond the {part['warranty_months']}-month warranty.")
    if po and claim["claim_qty"] > po["order_qty"]:
        issues.append("The claim quantity exceeds the ordered quantity.")
    return {
        "found": True,
        "claim": {k: _json_value(v) for k, v in claim.items()},
        "purchase_order": {k: _json_value(v) for k, v in po.items()} if po else None,
        "shipment": {k: _json_value(v) for k, v in shipment.items()} if shipment else None,
        "part": {k: _json_value(v) for k, v in part.items()} if part else None,
        "knowledge": [{k: _json_value(v) for k, v in row.items()} for row in knowledge],
        "issues": issues,
    }


def get_purchase_order(po_no: str) -> dict:
    lines = fetch_all("SELECT * FROM purchase_orders WHERE po_no = %s ORDER BY po_line_no", (po_no,))
    shipment = fetch_one("SELECT * FROM shipments WHERE po_no = %s", (po_no,))
    return {
        "found": bool(lines),
        "po_no": po_no,
        "lines": [{k: _json_value(v) for k, v in row.items()} for row in lines],
        "shipment": {k: _json_value(v) for k, v in shipment.items()} if shipment else None,
    }


def search_knowledge(query: str) -> list[dict]:
    rows = fetch_all(
        """SELECT * FROM knowledge
           WHERE title ILIKE %s OR summary ILIKE %s OR module ILIKE %s
           ORDER BY last_updated DESC LIMIT 10""",
        (f"%{query}%", f"%{query}%", f"%{query}%"),
    )
    return [{k: _json_value(v) for k, v in row.items()} for row in rows]
