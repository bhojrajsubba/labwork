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
)

# ==============================================================================
# MATRIX PARAMETER WSGI MIDDLEWARE
# ==============================================================================
# In enterprise web services (Spring, Ruby, custom REST gateways), semicolons (;)
# are used to pass matrix parameters (e.g. /profile;view=summary or /profile;v=2).
# This WSGI middleware extracts matrix parameters and normalizes PATH_INFO so Flask
# can route to the base endpoint /profile.
#
# BUT Nginx does not recognize ';' as a path delimiter and treats the entire URL
# /profile;test.css as a static file ending in .css!
class MatrixParamMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if ";" in path:
            # Extract everything before the first semicolon as the base path
            base_path, matrix_part = path.split(";", 1)
            environ["PATH_INFO"] = base_path
            environ["MATRIX_PARAMS"] = matrix_part
            environ["ORIGINAL_PATH"] = path
        return self.wsgi_app(environ, start_response)


flask_app = Flask(__name__)
flask_app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key_12345")
# Allow genuine static assets to be cached for 1 day
flask_app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 86400

MODE = os.environ.get("MODE", "vulnerable").lower()
BOT_SERVICE_URL = os.environ.get("BOT_SERVICE_URL", "http://wcd02-bot:5001/visit")

# Apply matrix parameter middleware to Flask WSGI app
app = MatrixParamMiddleware(flask_app)

# Mock database of users
USERS = {
    "victim": {
        "password": "P@sswordVictim2026!",
        "name": "Dr. Alex Mercer",
        "email": "alex.mercer@corp.internal",
        "role": "Chief Financial Officer",
        "api_key": "sk-live-mercer-fin-849182390a18294c",
        "flag": "FLAG{wcd_s3m1c0l0n_m4tr1x_d3l1m1t3r_p0wn3d}",
        "balance": "$984,200.00",
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


@flask_app.context_processor
def inject_global_data():
    user_data, username = get_current_user()
    return {
        "mode": MODE,
        "current_user": user_data,
        "current_username": username,
    }


@flask_app.route("/")
def index():
    return render_template("index.html")


@flask_app.route("/login", methods=["GET", "POST"])
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


@flask_app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


# ==============================================================================
# PROFILE ROUTING (NOTICE: LAB 01 FIX IS PRESENT!)
# ==============================================================================
# Notice: Unlike Lab 01, there is NO subpath parameter like /profile/<path:subpath>!
# If an attacker tries /profile/test.css, Flask strictly returns 404 Not Found.
#
# HOWEVER, because MatrixParamMiddleware strips ';...', any request like
# /profile;avatar.css maps to /profile!
@flask_app.route("/profile")
def profile():
    user_data, username = get_current_user()
    if not user_data:
        flash("Please sign in to access your profile.", "warning")
        return redirect(url_for("login"))

    matrix_params = request.environ.get("MATRIX_PARAMS", "")

    if MODE == "vulnerable":
        # VULNERABLE:
        # Fails to emit Cache-Control headers on sensitive dynamic user data,
        # allowing Nginx to cache the response under the key /profile;avatar.css
        resp = make_response(
            render_template("profile.html", user=user_data, matrix_params=matrix_params)
        )
        return resp
    else:
        # SECURE:
        # 1. Enforces strict Cache-Control preventing intermediate proxies from storing private data
        # 2. Defense-in-depth: If matrix parameters are detected on sensitive endpoints, reject them
        if matrix_params:
            return make_response("Matrix parameters are forbidden on this endpoint.", 400)

        resp = make_response(render_template("profile.html", user=user_data))
        resp.headers["Cache-Control"] = "no-store, no-cache, private, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp


@flask_app.route("/report", methods=["GET", "POST"])
def report():
    """Simulates submitting a link to an administrator to inspect."""
    if request.method == "POST":
        target_path = request.form.get("url", "").strip()

        if not target_path:
            flash("Please enter a valid URL or path.", "danger")
            return render_template("report.html")

        try:
            bot_resp = requests.post(
                BOT_SERVICE_URL,
                json={"path": target_path},
                timeout=10,
            )
            if bot_resp.status_code == 200:
                flash(
                    "Report submitted! Lead Administrator (Dr. Alex Mercer) inspected your link.",
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
    flask_app.run(host="0.0.0.0", port=5000, debug=(MODE == "vulnerable"))
