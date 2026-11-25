# Lab 01: Web Cache Deception (Path Mapping Discrepancy)

- **Vulnerability Category**: Web Cache Deception (WCD)
- **Difficulty**: Beginner / Intermediate
- **Tech Stack**: Nginx (Reverse Proxy & Cache) + Python Flask (Backend) + Victim Bot (Simulated User)
- **Docker Profile**: `wcd-01`

---

## 📖 Scenario Overview

**NovaCorp** operates an internal employee portal. To reduce load on backend servers, infrastructure engineers placed an **Nginx caching reverse proxy** in front of the application.

- The backend serves private employee account pages at `/profile`.
- The cache was configured to store static resources (`.css`, `.js`, `.png`) to optimize frontend delivery.
- Your target is senior engineer **Dr. Alex Mercer** (`victim`). You want to steal their private API token and security flag.

---

## 🧠 The Root Cause (Developer Mindset)

Web Cache Deception occurs when two architectural components (the **Cache** and the **Origin Application**) interpret the exact same HTTP request path differently.

### 1. The Cache's Assumption
In `nginx.vulnerable.conf`, the caching rule checks only the file extension using a regular expression:
```nginx
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    proxy_pass http://backend_app;
    proxy_cache lab_cache;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    proxy_cache_valid 200 302 10m;
    proxy_ignore_headers Cache-Control Expires Set-Cookie;
}
```
Because the URL path ends with `.css`, Nginx assumes this is a public static stylesheet and caches the response under the key:
`http://localhost/profile/avatar.css`.

### 2. The Backend's Assumption
In `app/app.py`, the backend routing was designed to accept optional subpaths or virtual paths:
```python
@app.route("/profile", defaults={"subpath": ""})
@app.route("/profile/<path:subpath>")
def profile(subpath):
    # Renders the private account page regardless of what subpath was appended!
    return render_template("profile.html", user=current_user)
```
When Dr. Alex Mercer loads `/profile/avatar.css`:
- Flask discards `/avatar.css` and renders Mercer's private profile.
- Flask fails to emit `Cache-Control: private, no-store`.
- Nginx intercepts the `200 OK` HTML response, sees the `.css` extension, and stores the victim's private profile in the public cache!

---

## ⚡ Exploitation Walkthrough (Hacker Mindset)

### Step 1: Identify Caching Rules
Inspect normal static assets (e.g. `/static/style.css`). Look for response headers:
```http
X-Cache-Status: HIT
X-Cache-Status: MISS
```
Notice that requests with static extensions are routed through the caching engine.

### Step 2: Test Backend Path Tolerance
Visit `/profile` in your browser while logged in as `attacker` (`attacker123`).
Now append a dummy static extension:
```
http://localhost:8080/profile/test.css
```
Notice that the page still renders your profile! The backend ignores the extra path segment.

### Step 3: Trigger the Victim Visit
Craft a unique path so you don't collide with previous tests:
```
/profile/stealer_1337.css
```
Submit `/profile/stealer_1337.css` to the **Support Bot** at `/report`.
The victim bot (logged in as `victim`) visits that link.
- Nginx experiences a cache `MISS`.
- Flask returns Dr. Alex Mercer's private profile.
- Nginx saves the response under key `/profile/stealer_1337.css`.

### Step 4: Exfiltrate the Data
Open a private/incognito window (or use `curl` without cookies):
```bash
curl -i http://localhost:8080/profile/stealer_1337.css
```
You will receive:
- `X-Cache-Status: HIT`
- The victim's full HTML page, revealing:
  - **API Key**: `sk-live-9481a82f0bc84d12a99182390f72ba18`
  - **Flag**: `FLAG{wcd_p4th_m4pp1ng_c4ch3_p01s0n}`

---

## 🛡️ How to Fix (The Secure Solution)

Defense-in-depth requires fixes on both the backend and the caching proxy:

### 1. Fix the Backend Application (`app.py`)
1. Enforce strict routing: `/profile` must only match `/profile`. Any subpath `/profile/*` must return `404 Not Found`.
2. Explicitly send restrictive caching headers on all authenticated responses:
```python
resp = make_response(render_template("profile.html", user=user_data))
resp.headers["Cache-Control"] = "no-store, no-cache, private, must-revalidate"
resp.headers["Pragma"] = "no-cache"
return resp
```

### 2. Fix the Cache Configuration (`nginx.conf`)
1. Only cache paths explicitly located under known static directories:
```nginx
location /static/ {
    proxy_pass http://backend_app;
    proxy_cache lab_cache;
}
```
2. Do **not** use `proxy_ignore_headers Cache-Control`. Always honor upstream directives.
3. Bypass caching when session cookies are present:
```nginx
proxy_cache_bypass $cookie_session;
```

---

## 🚀 Running and Testing the Lab

### 1. Start the Lab in Vulnerable Mode
```bash
# From workspace root:
docker compose --profile wcd-01 up --build -d

# Or using Makefile:
make up LAB=wcd-01
```
Open your browser at `http://localhost:8080`.

### 2. Run the Automated Exploit Verification
```bash
python labs/01-web-cache-deception/wcd-01-path-mapping/exploit.py
```

### 3. Switch to Secure Mode
In `.env` set:
```ini
WCD_MODE=secure
```
Rebuild and restart:
```bash
docker compose --profile wcd-01 up --build -d
python labs/01-web-cache-deception/wcd-01-path-mapping/exploit.py --expected-mode secure
```
The exploit will now report that the cache was prevented from storing private user data!
