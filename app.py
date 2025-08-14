import os
import json
import uuid
import time
from flask import Flask, request, jsonify, send_from_directory
import requests

# Project imports
from scanner import scan_text, load_rules

app = Flask(__name__, static_folder="static")

SCANS_FILE = os.path.join(os.path.dirname(__file__), "scans.json")
SAMPLE_EMAILS = os.path.join(os.path.dirname(__file__), "sample_data", "emails.json")


def load_scans():
    if os.path.exists(SCANS_FILE):
        with open(SCANS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_scans(scans):
    with open(SCANS_FILE, "w", encoding="utf-8") as f:
        json.dump(scans, f, indent=2)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/emails/<inbox>")
def get_emails(inbox):
    if not os.path.exists(SAMPLE_EMAILS):
        return jsonify([])
    with open(SAMPLE_EMAILS, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data.get(inbox, []))


# API SCAN ROUTE


@app.route("/scan", methods=["POST"])
def api_scan():
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text", "")
    url = payload.get("url")
    inbox = payload.get("inbox")

    # fetch a remote url if givenn
    if url:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                text += "\n\n" + resp.text
        except Exception:
            pass

    # fetch mock emails from our mock endpoint if inbox supplied
    if inbox:
        try:
            host = request.host_url.rstrip("/")
            resp = requests.get(f"{host}/emails/{inbox}", timeout=5)
            if resp.status_code == 200:
                emails = resp.json()
                for e in emails:
                    text += "\n\n" + e.get("subject", "") + "\n" + e.get("body", "")
        except Exception:
            pass

    if not text.strip():
        return jsonify({"error": "no text, url, or inbox content provided"}), 400

    flagged = scan_text(text)

    scan_id = str(uuid.uuid4())
    scans = load_scans()
    scans[scan_id] = {
        "id": scan_id,
        "timestamp": time.time(),
        "excerpt": "\n".join(text.splitlines()[:10]),
        "flags": flagged,
    }
    save_scans(scans)

    return jsonify(
        {"scanId": scan_id, "status": "completed", "flags_found": len(flagged)}
    )


@app.route("/reports/<scan_id>")
def get_report(scan_id):
    scans = load_scans()
    rec = scans.get(scan_id)
    if not rec:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify(rec)


@app.route("/scans")
def list_scans():
    scans = load_scans()
    out = []
    for s in scans.values():
        out.append(
            {
                "id": s["id"],
                "timestamp": s["timestamp"],
                "flags": len(s.get("flags", [])),
            }
        )
    out.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify(out)


@app.route("/rules")
def api_rules():
    return jsonify(load_rules())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
