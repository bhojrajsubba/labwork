# 🛡️ Dual-Perspective Vulnerability Lab

A modular, plug-and-play laboratory platform for understanding web vulnerabilities from **both the attacker's mindset (exploitation) and the developer's mindset (root cause & defense)**.

Every lab in this repository is built with:
1. **`MODE=vulnerable`**: Exploitable architecture demonstrating real-world software flaws.
2. **`MODE=secure`**: The production-ready patched version demonstrating secure coding & defense-in-depth.
3. **`exploit.py`**: Automated verification test that proves the exploit succeeds in vulnerable mode and fails in secure mode.
4. **Comprehensive Documentation**: Root-cause analysis, step-by-step reproduction, and code-level remediation.

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Docker & Docker Compose v2+
- Python 3.9+ (for running exploit scripts)

### 1. Launch a Lab
Run any lab using Docker Compose profiles or the `Makefile`:
```bash
# Start Lab 01: Web Cache Deception
docker compose --profile wcd-01 up --build -d

# Or with Make:
make up LAB=wcd-01
```
Access the application in your browser at `http://localhost:8080`.

### 2. Verify with the Automated Exploit
```bash
python labs/01-web-cache-deception/wcd-01-path-mapping/exploit.py
```

### 3. Switch to Secure Mode (Test the Fix)
Edit `.env`:
```ini
WCD_MODE=secure
```
Restart the lab:
```bash
docker compose --profile wcd-01 up --build -d
python labs/01-web-cache-deception/wcd-01-path-mapping/exploit.py --expected-mode secure
```

---

## 🌐 Production & VPS Hosting Guide ($5 Cloud Plan)

This platform was built from the ground up to be **hostable on a cheap $5/mo VPS** (e.g., AWS Lightsail 1-2 GB RAM, Hetzner, or DigitalOcean) while remaining safe and realistic.

### Hardening Guidelines for Remote Hosting:
1. **Never run with public exposure without access control**:
   Place an authenticating reverse proxy (like Caddy or Nginx with HTTP Basic Auth) in front of the lab port:
   ```caddy
   lab.yourdomain.com {
       basicauth {
           student $2a$14$...
       }
       reverse_proxy 127.0.0.1:8080
   }
   ```
2. **Protect Cloud Metadata (SSRF)**:
   If hosting on AWS EC2 or Lightsail:
   - Enforce **IMDSv2** with hop limit 1:
     ```bash
     aws ec2 modify-instance-metadata-options --instance-id <id> --http-tokens required --http-put-response-hop-limit 1
     ```
   - Attach **no IAM roles** to the instance.
3. **Ephemeral Lifecycle**:
   Spin the VPS up for your study/workshop session, and terminate it when finished to eliminate lingering risk and cost.

---

## 🗺️ Lab Roadmap (14 Core Categories)

| # | Vulnerability Class | Lab Name | Stack | Status |
|---|---|---|---|---|
| **01** | **Web Cache Deception** | `wcd-01-path-mapping` | Nginx + Flask + Bot | ✅ Complete |
| | | `wcd-02-delimiter-discrepancy` | Nginx + Express + Bot | 🗓️ Planned |
| **02** | **SQL Injection** | `sqli-01-login-bypass` | PHP 8 + MySQL | 🗓️ Planned |
| | | `sqli-02-union-extraction` | PHP 8 + MySQL | 🗓️ Planned |
| | | `sqli-03-blind-time-based` | Python FastAPI + Postgres | 🗓️ Planned |
| **03** | **Authentication** | `auth-01-username-enum` | Python Flask + SQLite | 🗓️ Planned |
| | | `auth-02-jwt-key-confusion` | Node.js Express | 🗓️ Planned |
| **04** | **Path Traversal** | `path-01-filter-bypass` | PHP 8 (Apache) | 🗓️ Planned |
| **05** | **Command Injection** | `cmd-01-blind-oob` | PHP 8 + Netcat | 🗓️ Planned |
| **06** | **Business Logic** | `logic-01-coupon-stacking` | Python Flask | 🗓️ Planned |
| **07** | **Information Disclosure** | `info-01-git-leak-heap` | Nginx + Python | 🗓️ Planned |
| **08** | **Access Control (IDOR)** | `idor-01-horizontal-privesc` | Python FastAPI | 🗓️ Planned |
| **09** | **File Upload** | `upload-01-polyglot-bypass` | PHP 8 + Apache | 🗓️ Planned |
| **10** | **Race Conditions** | `race-01-limit-overrun` | Python Flask + Postgres | 🗓️ Planned |
| **11** | **SSRF** | `ssrf-01-internal-admin-bypass` | Python Flask + Internal Admin | 🗓️ Planned |
| **12** | **XXE Injection** | `xxe-01-file-retrieval` | PHP 8 / Java Spring | 🗓️ Planned |
| **13** | **NoSQL Injection** | `nosql-01-operator-injection` | Node.js Express + MongoDB | 🗓️ Planned |
| **14** | **API Security** | `api-01-mass-assignment` | Node.js Express + Swagger | 🗓️ Planned |

---

## 📁 Repository Layout
```text
vuln-labs/
├── .env.example            # Sample configuration
├── docker-compose.yml      # Root orchestrator using compose profiles
├── Makefile                # Lifecycle commands (up, down, test, reset)
├── labs/
│   └── 01-web-cache-deception/
│       └── wcd-01-path-mapping/
│           ├── README.md   # Dual-perspective lab guide
│           ├── exploit.py  # Automated exploit verifier
│           ├── app/        # Flask backend with MODE switch
│           ├── cache/      # Nginx proxy with caching rules
│           └── bot/        # Lightweight victim crawler
└── shared/                 # Shared base templates and helper utilities
```
