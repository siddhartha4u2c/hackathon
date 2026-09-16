import json
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .dashboard import metrics as dashboard_metrics
from .dashboard import stock_positions, transfer_suggestions
from .db import fetch_one
from .llmaas import complete, configured
from .tools import get_purchase_order, investigate_claim, search_knowledge
from .vision import identify_part

app = FastAPI(title="PartsPilot Copilot", version="0.1.0")
STATIC = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    message: str


def extract_id(message: str, prefix: str) -> str | None:
    match = re.search(rf"\b{prefix}[-A-Z0-9]+\b", message, re.IGNORECASE)
    return match.group(0) if match else None


def deterministic_answer(message: str) -> tuple[str, dict]:
    claim_id = extract_id(message, "CLM")
    po_no = extract_id(message, "PO")
    if claim_id:
        evidence = investigate_claim(claim_id)
        if not evidence["found"]:
            return evidence["message"], evidence
        issues = evidence["issues"]
        if issues:
            answer = "I investigated the claim and found a data-quality issue:\n\n- " + "\n- ".join(issues)
        else:
            answer = "I investigated the claim. No contradiction was detected in the linked records."
        return answer, evidence
    if po_no:
        evidence = get_purchase_order(po_no)
        if not evidence["found"]:
            return f"No purchase order was found for {po_no}.", evidence
        shipment = evidence["shipment"]
        answer = f"{po_no} has {len(evidence['lines'])} line(s). "
        answer += f"Shipment status: {shipment['shipment_status']}." if shipment else "No linked shipment was found."
        return answer, evidence
    knowledge = search_knowledge(message)
    return (
        "Please provide a claim ID such as CLM-4021 or a purchase order such as PO-2026-1042. "
        "I can investigate claims, shipment status, and relevant SOP guidance.",
        {"knowledge": knowledge},
    )


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/dashboard")
def dashboard_page():
    return FileResponse(STATIC / "dashboard.html")


@app.get("/api/dashboard")
def dashboard_data():
    return dashboard_metrics()


@app.post("/api/vision/identify")
async def vision_identify(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file was empty.")
    result = identify_part(file.filename or "upload", data)
    if result["candidates"]:
        top_part_no = result["candidates"][0]["part_no"]
        result["stock_positions"] = stock_positions(top_part_no)
        result["transfer_suggestions"] = transfer_suggestions(top_part_no, limit=3)
    else:
        result["stock_positions"] = []
        result["transfer_suggestions"] = []
    return result


@app.get("/api/health")
def health():
    try:
        fetch_one("SELECT 1 AS ok")
        return {"status": "ok", "database": "connected", "llmaas_configured": configured()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@app.post("/api/chat")
def chat(request: ChatRequest):
    answer, evidence = deterministic_answer(request.message)
    if configured():
        prompt = (
            "You are PartsPilot. Answer only from the supplied evidence. Do not invent status, "
            "stock, prices, or claim outcomes. If records conflict, say the case needs human review. "
            "Cite the relevant entity IDs in your answer.\n\nEvidence:\n" + json.dumps(evidence, default=str)
        )
        llm_answer = complete(prompt, request.message)
        if llm_answer:
            answer = llm_answer
    return {"answer": answer, "evidence": evidence, "llmaas_used": configured()}
