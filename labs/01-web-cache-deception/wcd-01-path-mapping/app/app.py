import os
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
    abort,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key_12345")
# Allow genuine static files to be publicly cached for 1 day (86400 seconds)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 86400
MODE = os.environ.get("MODE", "vulnerable").lower()
BOT_SERVICE_URL = os.environ.get("BOT_SERVICE_URL", "http://wcd-bot:5001/visit")

# Mock database of users
USERS = {
    "victim": {
        "password": "P@sswordVictim2026!",
        "name": "Dr. Alex Mercer",
        "email": "alex.mercer@corp.internal",
        "role": "Lead Systems Engineer",
        "api_key": "sk-live-9481a82f0bc84d12a99182390f72ba18",
        "flag": "FLAG{wcd_p4th_m4pp1ng_c4ch3_p01s0n}",
        "balance": "$14,250.00",
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


# ==============================================================================
# PROFILE ROUTING (VULNERABLE VS SECURE)
# ==============================================================================
if MODE == "vulnerable":
    # VULNERABLE IMPLEMENTATION:
    # 1. Routing discrepancy: matches `/profile` AND any subpath like `/profile/avatar.css`
    # 2. Missing strict Cache-Control headers on sensitive dynamic user data
    @app.route("/profile", defaults={"subpath": ""})
    @app.route("/profile/<path:subpath>")
    def profile(subpath):
        user_data, username = get_current_user()
        if not user_data:
            flash("Please sign in to access your profile.", "warning")
            return redirect(url_for("login"))

        # In vulnerable mode, Flask returns standard response without cache restrictions
        resp = make_response(render_template("profile.html", user=user_data, subpath=subpath))
        # Note: No Cache-Control header is set, allowing intermediate proxy caches to do whatever they want!
        return resp

else:
    # SECURE IMPLEMENTATION:
    # 1. Strict route matching: only `/profile` is matched. Any subpath triggers 404 Not Found.
    # 2. Explicit Cache-Control headers preventing any caching of authenticated dynamic content.
    @app.route("/profile")
    def profile():
        user_data, username = get_current_user()
        if not user_data:
            flash("Please sign in to access your profile.", "warning")
            return redirect(url_for("login"))

        resp = make_response(render_template("profile.html", user=user_data))
        # Defense-in-depth: Never allow caches to store personalized user profiles
        resp.headers["Cache-Control"] = "no-store, no-cache, private, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp


@app.route("/report", methods=["GET", "POST"])
def report():
    """Simulates submitting a link to an admin/support user to inspect."""
    if request.method == "POST":
        target_path = request.form.get("url", "").strip()

        if not target_path:
            flash("Please enter a valid URL or path.", "danger")
            return render_template("report.html")

        # Forward request to victim bot service
        try:
            bot_resp = requests.post(
                BOT_SERVICE_URL,
                json={"path": target_path},
                timeout=10,
            )
            if bot_resp.status_code == 200:
                flash(
                    "Support ticket logged! Administrator (Dr. Alex Mercer) reviewed your link.",
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
