import os
import sys
import time
import http.client
from urllib.parse import urlsplit
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TARGET_HOST = os.environ.get("TARGET_HOST", "wcd03-cache")
TARGET_PORT = int(os.environ.get("TARGET_PORT", "80"))
BASE_URL = f"http://{TARGET_HOST}:{TARGET_PORT}"

VICTIM_USER = "victim"
VICTIM_PASS = "P@sswordVictim2026!"


def extract_safe_path(raw_target: str) -> tuple[bool, str]:
    """Safely extracts path and query string from relative paths or full URLs."""
    raw_target = raw_target.strip()
    if not raw_target:
        return False, "Path or URL cannot be empty."

    if "://" in raw_target or raw_target.startswith("//"):
        try:
            parsed = urlsplit(raw_target)
            path = parsed.path if parsed.path else "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
            return True, path
        except Exception as e:
            return False, f"Malformed URL provided: {str(e)}"
    else:
        if not raw_target.startswith("/"):
            raw_target = "/" + raw_target
        return True, raw_target


def simulate_victim_visit(target_input: str):
    """Logs into the application as the victim and visits the target path."""
    valid, path = extract_safe_path(target_input)
    if not valid:
        return False, path

    session = requests.Session()
    session.headers.update({"User-Agent": "NovaCorp-CloudAuditBot/3.0 (Director-Reviewer)"})

    # Step 1: Authenticate as the victim
    login_url = f"{BASE_URL}/login"
    login_payload = {"username": VICTIM_USER, "password": VICTIM_PASS}

    try:
        login_resp = session.post(login_url, data=login_payload, timeout=5, allow_redirects=True)
        if login_resp.status_code not in (200, 302):
            return False, f"Login failed with status {login_resp.status_code}"
    except Exception as e:
        return False, f"Connection to target login failed: {str(e)}"

    cookie_header = "; ".join([f"{c.name}={c.value}" for c in session.cookies])

    # Step 2: Visit target URL using low-level http.client to preserve raw path exactly
    # (Prevents requests/urllib3 from normalizing ../ or changing %2f to %2F)
    try:
        conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=10)
        headers = {
            "User-Agent": "NovaCorp-CloudAuditBot/3.0 (Director-Reviewer)",
        }
        if cookie_header:
            headers["Cookie"] = cookie_header

        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        cache_status = resp.getheader("X-Cache-Status", "N/A")
        conn.close()

        return True, {
            "target": f"{BASE_URL}{path}",
            "status_code": resp.status,
            "cache_status": cache_status,
            "content_length": len(body),
        }
    except Exception as e:
        return False, f"Failed visiting target URL: {str(e)}"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "victim-bot-03"})


@app.route("/visit", methods=["POST"])
def visit():
    data = request.get_json(force=True, silent=True) or {}
    path = data.get("path") or request.form.get("path")

    if not path:
        return jsonify({"error": "Path parameter is required"}), 400

    print(f"[*] Victim bot received visit request for: {path}", flush=True)
    success, result = simulate_victim_visit(path)

    if success:
        print(f"[+] Successfully visited: {result}", flush=True)
        return jsonify({"status": "success", "result": result}), 200
    else:
        print(f"[-] Visit error: {result}", flush=True)
        return jsonify({"status": "error", "message": result}), 400


if __name__ == "__main__":
    print(f"[*] Victim Bot listening on port 5001 (Targeting {BASE_URL})", flush=True)
    app.run(host="0.0.0.0", port=5001)
