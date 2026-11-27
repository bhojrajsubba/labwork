# Lab 05: Ruby on Rails Dot Format Delimiter + Nginx + Default Cloudflare

## Scenario Overview
This lab demonstrates a real-world **Web Cache Deception (WCD)** vulnerability using **Ruby on Rails**, **Nginx Origin**, and **Cloudflare's Default Cache Behavior** (zero custom Cloudflare Cache Rules required).

### The Discrepancy
1. **Cloudflare (Edge Cache):** By default, Cloudflare caches responses for static file extensions (`.ejs`, `.pict`, `.pls`, `.woff2`, `.avif`, `.css`, `.js`, etc.) as long as `Set-Cookie`, `Vary: Cookie`, and `Cache-Control: private/no-store` are absent.
2. **Nginx Origin (`proxy_pass http://backend_app/;`):** Normalizes dot-segment traversals (`..` / `%2f`) via trailing-slash `proxy_pass`, and strips `Vary`.
3. **Ruby on Rails (`wcd05-app`):** Standard Rails routes implicitly match `/<route>(.:format)`. When an extension is **not** registered in Rails' `Mime::SET` (e.g., `.ejs`, `.pict`, `.pls`), Rails ignores the unknown extension and renders the default HTML view (`200 OK`) for `/profile`.

Because Cloudflare treats `/profile.ejs` (or `/static/<token>/..%2F..%2Fprofile.ejs`) as a cacheable static asset while Rails executes `/profile`, the victim's confidential vault dashboard gets cached by Cloudflare!

---

## Quick Start

1. Start Lab 05:
   ```bash
   make up LAB=wcd-05
   ```
2. Verify Origin locally:
   ```bash
   make test LAB=wcd-05
   ```
3. Verify against your Cloudflare domain:
   ```bash
   python labs/01-web-cache-deception/wcd-05-rails-format-delimiter/exploit.py --url https://your-domain.com
   ```

---

## Remediation (Secure Mode)
1. **Disable implicit format routing in Rails (`config/routes.rb`):**
   ```ruby
   get "/profile", to: "vault#profile", format: false
   ```
2. **Enforce strict `Cache-Control` headers (`VaultController#profile`):**
   ```ruby
   response.headers["Cache-Control"] = "no-store, no-cache, private, must-revalidate"
   ```
3. **Harden Origin Nginx (`nginx.secure.conf`):** Remove trailing slash from `proxy_pass` and reject `..` / `%2f` traversal sequences.
