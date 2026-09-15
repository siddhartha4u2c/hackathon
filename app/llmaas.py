import json
import os
from urllib.request import Request, urlopen


def configured() -> bool:
    return bool(os.getenv("LLMAAS_BASE_URL") and os.getenv("LLMAAS_API_KEY") and os.getenv("LLMAAS_MODEL"))


def complete(system_prompt: str, user_prompt: str) -> str | None:
    if not configured():
        return None
    endpoint = os.environ["LLMAAS_BASE_URL"].rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": os.environ["LLMAAS_MODEL"],
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode()
    request = Request(endpoint, data=payload, headers={
        "Authorization": f"Bearer {os.environ['LLMAAS_API_KEY']}",
        "Content-Type": "application/json",
    }, method="POST")
    with urlopen(request, timeout=60) as response:
        body = json.loads(response.read().decode())
    return body["choices"][0]["message"]["content"]
