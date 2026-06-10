from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

# -----------------------------
# FRONTEND
# -----------------------------

BASE_DIR = Path(__file__).parent

templates_dir = BASE_DIR / "templates"
templates_dir.mkdir(exist_ok=True)

# -----------------------------
# HOME
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def home():

    html = """
    <html>
    <head>
        <title>Fingerprint System</title>
    </head>

    <body style="font-family:Arial; text-align:center; margin-top:80px;">

        <h1>Fingerprint Authentication System</h1>

        <br>

        <a href="/enroll">
            <button style="padding:15px; width:220px;">
                Enrollment
            </button>
        </a>

        <br><br>

        <a href="/verify">
            <button style="padding:15px; width:220px;">
                Verification
            </button>
        </a>

    </body>
    </html>
    """

    return html


# -----------------------------
# ENROLL PAGE
# -----------------------------

@app.get("/enroll", response_class=HTMLResponse)
def enroll_page():

    enroll_file = templates_dir / "enroll.html"

    if enroll_file.exists():
        return enroll_file.read_text()

    return "<h1>enroll.html not found</h1>"


# -----------------------------
# VERIFY PAGE
# -----------------------------

@app.get("/verify", response_class=HTMLResponse)
def verify_page():

    verify_file = templates_dir / "verify.html"

    if verify_file.exists():
        return verify_file.read_text()

    return "<h1>verify.html not found</h1>"