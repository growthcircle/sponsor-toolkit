#!/usr/bin/env python3
"""
fetch_and_serve.py

1) Reads your local ngrok API to find the public HTTPS tunnel.
2) Fetches /Sponsor_Landing_Page.html with the skip-warning header.
3) Writes it to landing.html and serves it at http://127.0.0.1:9000/landing.html.
"""

import json
import requests
import http.server
import socketserver
import time
from pathlib import Path
from urllib.request import urlopen

NGROK_API = "http://127.0.0.1:4040/api/tunnels"
LOCAL_FILE = "landing.html"
PORT = 9000

def get_tunnel():
    for _ in range(15):
        try:
            data = json.load(urlopen(NGROK_API))
            for t in data.get("tunnels", []):
                url = t.get("public_url", "")
                if url.startswith("https://"):
                    return url
        except:
            time.sleep(1)
    return None

def main():
    tunnel = get_tunnel()
    if not tunnel:
        print("❌ Could not find ngrok tunnel. Make sure ngrok is running on port 8000.")
        return

    landing_url = f"{tunnel}/Sponsor_Landing_Page.html"
    headers = {"ngrok-skip-browser-warning": "1"}
    print(f"⏳ Fetching landing page from:\n  {landing_url}\n(with header skip-warning)")

    resp = requests.get(landing_url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Got {resp.status_code} for {landing_url}")
        return

    Path(LOCAL_FILE).write_text(resp.text, encoding="utf-8")
    print(f"✅ Wrote local copy → ./{LOCAL_FILE}")

    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    print(f"🚀 Serving at http://127.0.0.1:{PORT}/{LOCAL_FILE}\nPress Ctrl+C to stop.")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
