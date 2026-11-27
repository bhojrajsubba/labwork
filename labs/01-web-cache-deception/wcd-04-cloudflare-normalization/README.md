# Lab 04: Cloudflare CDN vs. Nginx Origin Normalization Discrepancy

## Scenario Overview
In this lab, **Nginx** operates purely as the Origin Reverse Proxy in front of a vanilla Python **Flask** application, designed to sit behind **real Cloudflare** as the external edge cache.

Because Cloudflare by default does **not** normalize percent-encoded slashes (`%2f` / `%2F`)—and does not normalize dot segments (`..`) when edge URL Normalization is disabled—a caching rule matching `/static/*` can be tricked when Origin Nginx uses `proxy_pass http://backend_app/;` **with a trailing slash (`/`)**.

---

## Architecture

```text
Client / Bot  --->  Cloudflare Edge (Cache Rule on /static/*, no %2F normalization)
                          |
                          | forwards raw: GET /static/token/..%2F..%2Fprofile
                          v
                    Nginx Origin (wcd04-origin:80)
                    `proxy_pass http://backend_app/;`  <-- trailing slash normalizes URI!
                          |
                          | forwards normalized: GET /profile
                          v
                    Flask App (wcd04-app:5000)
```

---

## Running & Testing Locally

1. Start Lab 04:
   ```bash
   make up LAB=wcd-04
   ```
2. Verify Origin normalization locally:
   ```bash
   make test LAB=wcd-04
   ```
   Check the diagnostic headers returned by Nginx:
   - `X-Origin-Raw-URI: /static/token/..%2F..%2Fprofile`
   - `X-Origin-Normalized-URI: /profile`

3. Test against your Cloudflare-fronted domain:
   ```bash
   python labs/01-web-cache-deception/wcd-04-cloudflare-normalization/exploit.py --url https://your-domain.com
   ```
