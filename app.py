"""Single-page Flask application. Start locally with: python app.py."""

import os
from flask import Flask, jsonify, render_template, request
from calculator import EXAMPLE, FACTORS, SECTIONS, SOURCE_URL, InputError, calculate

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024


@app.get("/")
def index():
    return render_template("index.html", sections=SECTIONS, factors=FACTORS,
                           example=EXAMPLE, source_url=SOURCE_URL)


@app.post("/api/calculate")
def calculate_footprint():
    if not request.is_json:
        return jsonify(error="Send the form using JSON.", errors={}), 415
    data = request.get_json(silent=True)
    try:
        return jsonify(calculate(data))
    except InputError as exc:
        return jsonify(error=str(exc), errors=exc.errors), 400


@app.get("/health")
def health():
    return {"status": "ok"}


@app.errorhandler(413)
def too_large(_error):
    return jsonify(error="That form is too large. Please shorten your entries.", errors={}), 413


@app.after_request
def response_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5057")), debug=False)
