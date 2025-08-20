#!/usr/bin/env python3
# update_server.py - Secure endpoint for dynamic latest.yml and bootstrap config
import os
import subprocess
import yaml
from flask import Flask, request, Response, abort, jsonify

app = Flask(__name__)

B2_KEY_ID = os.environ.get("B2_KEY_ID")
B2_APP_KEY = os.environ.get("B2_APP_KEY")
B2_BUCKET = os.environ.get("B2_BUCKET")
SIGNED_URL_TTL = int(os.environ.get("SIGNED_URL_TTL", "600"))
UPDATES_API_KEY = os.environ.get("UPDATES_API_KEY")
BOOTSTRAP_URL = os.environ.get("BOOTSTRAP_URL", "https://your-bootstrap-url.example.com")

if not (B2_KEY_ID and B2_APP_KEY and B2_BUCKET):
    raise SystemExit("Set B2_KEY_ID, B2_APP_KEY, and B2_BUCKET environment variables")

def authorize_b2():
    cmd = ["b2", "authorize-account", B2_KEY_ID, B2_APP_KEY]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_signed_url(bucket, filename, ttl=SIGNED_URL_TTL):
    cmd = ["b2", "get-download-url-with-auth", bucket, filename]
    p = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.stdout.strip()

@app.route("/latest.yml")
def latest_yml():
    api_key = request.headers.get("X-API-KEY") or request.args.get("api_key")
    if UPDATES_API_KEY and api_key != UPDATES_API_KEY:
        abort(401)
    version = os.environ.get("APP_VERSION", "1.0.0")
    release_date = os.environ.get("RELEASE_DATE")
    filenames = os.environ.get("RELEASE_FILES", "Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-1.4.0.exe")
    filenames = [f.strip() for f in filenames.split(",") if f.strip()]
    authorize_b2()
    files_entries = []
    for fname in filenames:
        try:
            signed = get_signed_url(B2_BUCKET, fname)
        except subprocess.CalledProcessError as e:
            return Response(f"Error generating signed URL for {fname}: {e.stderr}", status=500)
        files_entries.append({"url": signed})
    y = {"version": version, "files": files_entries}
    if release_date:
        y["releaseDate"] = release_date
    body = yaml.safe_dump(y, sort_keys=False)
    return Response(body, mimetype="text/yaml")

@app.route("/bootstrap-config")
def bootstrap_config():
    api_key = request.headers.get("X-API-KEY") or request.args.get("api_key")
    if UPDATES_API_KEY and api_key != UPDATES_API_KEY:
        abort(401)
    config = {
        "bootstrap_url": BOOTSTRAP_URL,
        "update_server_url": request.url_root,
        "venv_packages": os.environ.get("VENV_PACKAGES", ""),
        "b2_key_id": os.environ.get("B2_KEY_ID", ""),
        "b2_bucket": os.environ.get("B2_BUCKET", ""),
        "app_version": os.environ.get("APP_VERSION", ""),
        "release_file": os.environ.get("RELEASE_FILE", "")
    }
    return jsonify(config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
