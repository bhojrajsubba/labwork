import os
import http.client
from urllib.parse import urlsplit
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TARGET_HOST = os.environ.get("TARGET_HOST", "wcd04-origin")
TARGET_PORT = int(os.environ.get("TARGET_PORT", "80"))
DEFAULT_BASE_URL = f"http://{TARGET_HOST}:{TARGET_PORT}"

VICTIM_USER = "victim"
VICTIM_PASS = "P@sswordVictim2026!"


def resolve_target(raw_target: str, explicit_base_url: str = None):
    """
    Resolves target connection details (scheme, host, port, raw_path) without normalizing
    dot segments or altering percent-encoding case (%2f vs %2F).

    Localhost/127.0.0.1 targets are automatically mapped to internal Docker Origin
    so local verification works inside Docker networks, while external Cloudflare
    domains are visited directly over the network so Cloudflare caches the response.
    """
    raw_target = (raw_target or "").strip()
    if not raw_target:
        return False, "Path or URL cannot be empty."

    if "://" in raw_target:
        parsed = urlsplit(raw_target)
        scheme = (parsed.scheme or "http").lower()
        hostname = (parsed.hostname or "").lower()
        port = parsed.port or (443 if scheme == "https" else 80)

        # Preserve exact raw path+query after scheme://netloc without canonicalizing
        after_scheme = raw_target.split("://", 1)[1]
        slash_idx = after_scheme.find("/")
        raw_path = after_scheme[slash_idx:] if slash_idx != -1 else "/"

        if hostname in ("127.0.0.1", "localhost", "0.0.0.0"):
            return True, ("http", TARGET_HOST, TARGET_PORT, raw_path)
        return True, (scheme, hostname, port, raw_path)

    # Relative path supplied
    raw_path = raw_target if raw_target.startswith("/") else "/" + raw_target

    if explicit_base_url:
        parsed_base = urlsplit(explicit_base_url)
        scheme = (parsed_base.scheme or "http").lower()
        hostname = (parsed_base.hostname or "").lower()
        port = parsed_base.port or (443 if scheme == "https" else 80)
        if hostname not in ("127.0.0.1", "localhost", "0.0.0.0", ""):
            return True, (scheme, hostname, port, raw_path)

    return True, ("http", TARGET_HOST, TARGET_PORT, raw_path)


def simulate_victim_visit(target_input: str, explicit_base_url: str = None):
    """Logs into the application as the victim and visits the raw target path."""
    valid, resolved = resolve_target(target_input, explicit_base_url)
    if not valid:
        return False, resolved

    scheme, host, port, raw_path = resolved
    default_port = 443 if scheme == "https" else 80
    host_header = host if port == default_port else f"{host}:{port}"
    base_url = f"{scheme}://{host_header}"

    session = requests.Session()
    session.headers.update({"User-Agent": "NovaCorp-CloudAuditBot/4.0 (Director-Reviewer)"})

    # Step 1: Authenticate as the victim at the target origin/CDN
    login_url = f"{base_url}/login"
    login_payload = {"username": VICTIM_USER, "password": VICTIM_PASS}

    try:
        login_resp = session.post(login_url, data=login_payload, timeout=10, allow_redirects=True)
        if login_resp.status_code not in (200, 302):
            return False, f"Login failed with status {login_resp.status_code}"
    except Exception as e:
        return False, f"Connection to target login failed ({login_url}): {str(e)}"

    cookie_header = "; ".join([f"{c.name}={c.value}" for c in session.cookies])

    # Step 2: Visit target URL using raw http.client to preserve ../ and %2f/%2F verbatim
    try:
        if scheme == "https":
            conn = http.client.HTTPSConnection(host, port, timeout=15)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=15)

        headers = {
            "Host": host_header,
            "User-Agent": "NovaCorp-CloudAuditBot/4.0 (Director-Reviewer)",
        }
        if cookie_header:
            headers["Cookie"] = cookie_header

        conn.request("GET", raw_path, headers=headers)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        cf_cache = resp.getheader("CF-Cache-Status", "N/A")
        origin_raw = resp.getheader("X-Origin-Raw-URI", "N/A")
        origin_norm = resp.getheader("X-Origin-Normalized-URI", "N/A")
        conn.close()

        return True, {
            "target": f"{base_url}{raw_path}",
            "status_code": resp.status,
            "cf_cache_status": cf_cache,
            "origin_raw_uri": origin_raw,
            "origin_normalized_uri": origin_norm,
            "content_length": len(body),
        }
    except Exception as e:
        return False, f"Failed visiting target URL ({base_url}{raw_path}): {str(e)}"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "victim-bot-04"})


@app.route("/visit", methods=["POST"])
def visit():
    data = request.get_json(force=True, silent=True) or {}
    path = data.get("path") or request.form.get("path")
    base_url = data.get("base_url")

    if not path:
        return jsonify({"error": "Path parameter is required"}), 400

    print(f"[*] Victim bot received visit request for: {path} (base_url={base_url})", flush=True)
    success, result = simulate_victim_visit(path, base_url)

    if success:
        print(f"[+] Successfully visited: {result}", flush=True)
        return jsonify({"status": "success", "result": result}), 200
    else:
        print(f"[-] Visit error: {result}", flush=True)
        return jsonify({"status": "error", "message": result}), 400


if __name__ == "__main__":
    print(f"[*] Victim Bot listening on port 5001 (Default target {DEFAULT_BASE_URL})", flush=True)
    app.run(host="0.0.0.0", port=5001)
