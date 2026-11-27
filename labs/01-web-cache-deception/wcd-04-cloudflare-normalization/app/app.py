import os
import json
import requests
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    make_response,
)

# Standard Flask application behind Nginx Origin (and external Cloudflare CDN).
# The vulnerability stems from Cloudflare not normalizing paths before cache lookup
# while Origin Nginx normalizes paths when proxy_pass uses a trailing slash (/).
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key_12345")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 86400

MODE = os.environ.get("MODE", "vulnerable").lower()
BOT_SERVICE_URL = os.environ.get("BOT_SERVICE_URL", "http://wcd04-bot:5001/visit")

USERS = {
    "victim": {
        "password": "P@sswordVictim2026!",
        "name": "Dr. Alex Mercer",
        "email": "alex.mercer@corp.internal",
        "role": "Director of Cloud Infrastructure",
        "api_key": "sk-live-vault-mercer-9938210948ab12e8",
        "flag": "FLAG{wcd_cl0udfl4r3_0r1g1n_n0rm4l1z4t10n}",
        "balance": "$2,450,000.00",
    },
    "attacker": {
        "password": "attacker123",
        "name": "Robin Vance",
        "email": "robin@external.org",
        "role": "Security Researcher",
        "api_key": "sk-test-attacker-key-3871",
        "flag": "FLAG{keep_trying_attacker}",
        "balance": "$25.00",
    },
}


def get_current_user():
    username = session.get("user")
    if username and username in USERS:
        return USERS[username], username
    return None, None


def detect_public_base_url():
    """Detects external domain (e.g. Cloudflare hostname) when accessed publicly."""
    host = request.host or ""
    hostname = host.split(":")[0].lower()
    if hostname in ("127.0.0.1", "localhost", "wcd04-origin", "wcd04-app", ""):
        return None

    proto = request.headers.get("X-Forwarded-Proto", "http").split(",")[0].strip().lower()
    cf_visitor = request.headers.get("CF-Visitor", "")
    if cf_visitor:
        try:
            visitor_data = json.loads(cf_visitor)
            if visitor_data.get("scheme") in ("http", "https"):
                proto = visitor_data["scheme"]
        except ValueError:
            pass

    return f"{proto}://{host}"


@app.context_processor
def inject_global_data():
    user_data, username = get_current_user()
    return {
        "mode": MODE,
        "current_user": user_data,
        "current_username": username,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username in USERS and USERS[username]["password"] == password:
            session["user"] = username
            flash(f"Welcome back, {USERS[username]['name']}!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    user_data, username = get_current_user()
    if not user_data:
        flash("Please sign in to access your profile.", "warning")
        return redirect(url_for("login"))

    if MODE == "vulnerable":
        return make_response(render_template("profile.html", user=user_data))
    else:
        # SECURE: Strict Cache-Control headers instruct Cloudflare / proxies never to cache
        resp = make_response(render_template("profile.html", user=user_data))
        resp.headers["Cache-Control"] = "no-store, no-cache, private, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp


@app.route("/report", methods=["GET", "POST"])
def report():
    """Simulates submitting a link to an infrastructure admin to inspect."""
    if request.method == "POST":
        target_path = request.form.get("url", "").strip()

        if not target_path:
            flash("Please enter a valid URL or path.", "danger")
            return render_template("report.html")

        payload = {"path": target_path}
        public_base = detect_public_base_url()
        if public_base:
            payload["base_url"] = public_base

        try:
            bot_resp = requests.post(
                BOT_SERVICE_URL,
                json=payload,
                timeout=15,
            )
            if bot_resp.status_code == 200:
                flash(
                    "Inspection request logged! Infrastructure Director (Dr. Alex Mercer) reviewed your link.",
                    "success",
                )
            else:
                flash(
                    f"Support bot encountered an error: {bot_resp.text}",
                    "warning",
                )
        except Exception as e:
            flash(f"Failed to reach support bot: {str(e)}", "danger")

    return render_template("report.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=(MODE == "vulnerable"))
