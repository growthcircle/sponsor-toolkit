#!/usr/bin/env python3
"""
generate_toolkit_v12.py
Sponsor‐grade deploy: preserves JSON, auto-shares, auto-creates tab, syncs URLs, and emits a polished, on-brand landing page.
"""

import shutil
import json
import time
import subprocess
import traceback
from pathlib import Path
from urllib.request import urlopen

import gspread
from zipfile import ZipFile, ZIP_DEFLATED
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

# try drive API for auto-share; skip if not installed
try:
    from googleapiclient.discovery import build
except ImportError:
    build = None

# ───── CONFIG ──────────────────────────────────────────────────────────────
ROOT       = Path(r"C:\Users\devuser\Sponsor_Toolkit")
SCRIPT     = "generate_toolkit_v12.py"
JSON_FILE  = ROOT / "service_account.json"
ZIP_NAME   = "GrowthCircle_Sponsor_Toolkit.zip"
PORT       = 8000

SHEET_ID   = "1Ru2M8-fm2Fd4ocdYCBPmwOjnX4EVZTE_LzhGwa9sXhc"
SHEET_TAB  = "sponsor_tracking"
SCOPES     = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CAMPAIGN   = "Growth Circle"
CONTACT    = "sponsor@growthcircle.io"
GLIDE      = "https://growthcircle.glide.page"

# Inline fallback key (only if service_account.json is missing)
KEY_DATA = {
    "type": "service_account",
    "project_id": "serembok-ai-g",
    "private_key_id": "c267248f4da2dbd0f393f184136efb7da80977c7",
    "private_key": (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDBAlXovLbolUhu\n"
        "lcvJRNbEBpveJY/UHh0LLRdA4cXeKyXUYOXk2rY9OES+57KUfloLAofdU3c/3Jvhh\n"
        "CunWOLo8QjZaBwNMQO2ORvZKGI9+PKEVBlXaW8AVKlg0DjTwnirCv+I92wbAnBLu\n"
        "xHOJiP9n53JNC6y8CSAsGbpR4Wv29WbJlcm5G5E1HvHImHrmdSuHYGGLPfj7LEA5\n"
        "0c5Z+UagZ6zjLIe0AgDJSSLoGV+5CIu+WUafD0IlTz8f4KHX7ravueI+7J2wuvTe\n"
        "vZkCcpM9xirQWeZg6gwtdaR0RxfWNOjMYpHV5EARhMrTs2z4DYvXD9xZXeRbKGtY\n"
        "jRG54g1AgMBAAECggEAFrtmcGCnn0mTzBh+9a/SpqhLm9SrNbWtQId5RWZB9np4/\n"
        "GREN1nOHHQ/3oct+IDQLJtJ8raVpTMfteYp+Q4GPZ7D5s00/pW/BOuBfOhdd8SWFa\n"
        "FNEcdEcFLIVzN2+fPd3/FN6u0PMbguDzFTdcb2trShshSgCmmvtutv13pZw74paJi\n"
        "sOSh0U8xbV5ABcv3ljujngLc7bHqXkh6qUH00H1MVnaHQsZgmt9HuvmOIHhZ+F0N5\n"
        "yZOF2tn7vy6SixX14lG2Kx7oD8vh+qWkaqaGEifh5ZAlDYccYxh6MIFw6bWETTXJ\n"
        "ybfnj4ECwlEV07xAb1lW9PKjV7Ni/PrEvwQ2MQKBgQDnv3QI8jlU6ZU81zmumzbAW\n"
        "b/NWhfK1DrKtGv0Byl40sNLo3s7QDiTdKGzkvJPMmR6PKpd84ANwdB94W8WsQ2fQD\n"
        "xLvPP7SkN7LnvpOehReukCBtX1ByUv4PbmC+pkECBBIvECVqmztRdU5N1lL/nUcjq\n"
        "5ffcz2xJ18I/fQMZuEQKBgQDVNRFfnX3rTixtg166woZMzzKQ54uyx5MvrgX8YzAd\n"
        "zv7s7eBZ7UfwEVtIkIeZBuNMHjOhkkiLGcSE9dMhnV/lyE8rJV5Y6un1xZYN19KyB\n"
        "IKmCYh9Iz/NczaNMQRQpOhcJqay7E2bgxCerHd9TLenTzWx0enQlPiqNDXuLu7j5Q\n"
        "KBgQCrJUG9JZ1fbw1unAeWQjxB+0XhkqpFeUxdzLZ4xh1DhGsD3hyw2jGt/BE6+8e\n"
        "E41M+zrSGo8Aq6LpfbG/M0z6bICYnTMjmCKcjPmX2DHTcT6fqfj/eL8OvwzSzGZOl\n"
        "CB+52uMf9f5nn9I2OLqj8rVOxnlF6Zf5LM1KWjj2B/FC8QKBgHYg1AJtCTJRes4mh\n"
        "lrlonF2L2cX00/3wbYeLlTbQ/KQGLB/T9mjXUNG6pO2+Fox9cfbx/GSUj03xqmAZj\n"
        "1uq45twGeAadjMN1qj4fLDjIpzc0u5ZnUnDZewaR4rdV+VLuS3yY7C3HD4WkH//qhe\n"
        "1DaP7Ykba/fUQj5TdToFqPh9AoGAeiGzZjbhvEitPAVmZZqHHsnsp6G72ds4DM5kn\n"
        "b/CqfmF0vcllItFPlOVBU+MhnsBUDYW5EvLE1VYwLlwtN3l09KVfFErcQiQ4MtIFg\n"
        "2HBoCsm2Jc9yd2r1Kej+G1+/JEfSp9BUUKvHItKiXgrwosnwaTzo7g8yk6KgjVUBu\n"
        "2aWg=\n"
        "-----END PRIVATE KEY-----\n"
    ),
    "client_email": "growthcircle-toolkit-sync@serembok-ai-g.iam.gserviceaccount.com",
    "client_id": "110324469165809136779",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": (
        "https://www.googleapis.com/robot/v1/metadata/x509/"
        "growthcircle-toolkit-sync@serembok-ai-g.iam.gserviceaccount.com"
    )
}

def get_tunnel(api="http://127.0.0.1:4040/api/tunnels", retries=15, delay=1):
    for _ in range(retries):
        try:
            data = json.load(urlopen(api))
            for t in data.get("tunnels", []):
                url = t.get("public_url", "")
                if url.startswith("https://"):
                    return url
        except:
            time.sleep(delay)
    return None

def write_file(path: Path, content: str=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"📝 Wrote: {path.relative_to(ROOT)}")

def main():
    # 1) Tunnel
    tunnel = get_tunnel()
    if not tunnel:
        print("❌ Start ngrok:\n    & ngrok.exe http 8000")
        return
    print(f"🔗 Tunnel: {tunnel}")

    # 2) Clean (preserve script & JSON)
    print("🧹 Cleaning up (preserve script + JSON)…")
    exclude = {SCRIPT, JSON_FILE.name}
    for item in ROOT.iterdir():
        if item.name in exclude:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    # 3) Generate placeholders
    for sub in [
        "Pitch_Deck",
        "Branded_Flyers/QR_Preview_PNGs",
        "Legal_Docs",
        "Communications",
        "Screenshots",
        "Branding"
    ]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)

    write_file(ROOT / "Pitch_Deck/Growth_Circle_Sponsor_Deck.pdf")
    write_file(ROOT / "Branded_Flyers/GC_QR_Flyer_Portrait.pdf")
    write_file(ROOT / "Branded_Flyers/GC_QR_Flyer_WhiteLabel.pdf")
    write_file(ROOT / "Branded_Flyers/QR_Preview_PNGs/qr_Portrait.png")
    write_file(ROOT / "Legal_Docs/Growth_Circle_Sponsorship_Agreement.docx")
    write_file(ROOT / "Legal_Docs/Growth_Circle_Sponsorship_Agreement.md")
    write_file(
        ROOT / "Communications/email_template.html",
        f"<a href='{tunnel}/{ZIP_NAME}'>Download Toolkit</a>"
    )
    write_file(
        ROOT / "Communications/email_template.txt",
        f"Download: {tunnel}/{ZIP_NAME}"
    )
    write_file(ROOT / "Screenshots/glide_admin_dashboard.png")
    write_file(ROOT / "Branding/logo.png")

    # 4) Polished landing HTML
    landing_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{CAMPAIGN} Toolkit</title>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet"/>
  <style>
    body {{ margin:0; font-family:'Montserrat',sans-serif; background:#f5f7fa; color:#333;
           display:flex; flex-direction:column; align-items:center; padding:2rem }}
    header {{ text-align:center; margin-bottom:2rem }}
    header img {{ max-width:120px }}
    header h1 {{ margin:.5rem 0; font-size:2rem; color:#0052cc }}
    .grid {{ display:grid; gap:1.5rem;
             grid-template-columns:repeat(auto-fill,minmax(240px,1fr));
             width:100%; max-width:800px }}
    .card {{ background:#fff; border-radius:8px;
             box-shadow:0 2px 8px rgba(0,0,0,0.1); padding:1rem;
             text-align:center }}
    .card h3 {{ margin:0 0 .5rem; font-weight:600; color:#0052cc }}
    .card a {{ display:inline-block; margin-top:.5rem;
               padding:.5rem 1rem; background:#0052cc; color:#fff;
               text-decoration:none; border-radius:4px; font-weight:600 }}
    footer {{ margin-top:3rem; font-size:.9rem; color:#666 }}
  </style>
</head>
<body>
  <header>
    <img src="{tunnel}/Branding/logo.png" alt="Growth Circle Logo"/>
    <h1>{CAMPAIGN} Toolkit</h1>
  </header>
  <div class="grid">
    <div class="card">
      <h3>Download Sponsor Deck</h3>
      <a href="{tunnel}/Pitch_Deck/Growth_Circle_Sponsor_Deck.pdf" target="_blank">Download</a>
    </div>
    <div class="card">
      <h3>View Flyers</h3>
      <a href="{tunnel}/Branded_Flyers/GC_QR_Flyer_Portrait.pdf" target="_blank">Portrait</a><br/>
      <a href="{tunnel}/Branded_Flyers/GC_QR_Flyer_WhiteLabel.pdf" target="_blank">White Label</a>
    </div>
    <div class="card">
      <h3>Full Toolkit ZIP</h3>
      <a href="{tunnel}/{ZIP_NAME}" target="_blank">Download All</a>
    </div>
    <div class="card">
      <h3>Open Dashboard</h3>
      <a href="{GLIDE}" target="_blank">Go to Glide</a>
    </div>
  </div>
  <footer>© 2025 Growth Circle • Contact: {CONTACT}</footer>
</body>
</html>"""
    write_file(ROOT / "Sponsor_Landing_Page.html", landing_html)

    # 5) README
    write_file(
        ROOT / "README.txt",
        f"{CAMPAIGN} Toolkit\nDownload: {tunnel}/{ZIP_NAME}\nContact: {CONTACT}"
    )

    # 6) ZIP & serve
    print("📦 Packaging ZIP…")
    with ZipFile(ROOT / ZIP_NAME, "w", ZIP_DEFLATED) as z:
        for f in ROOT.rglob("*"):
            if f.is_file() and f.name not in exclude:
                z.write(f, f.relative_to(ROOT))

    print(f"🖥 HTTP server on port {PORT}")
    subprocess.Popen(
        ["python", "-m", "http.server", str(PORT)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL
    )

    # 7) Asset map
    assets = {
        "Avatar_URL":            f"{tunnel}/Branding/logo.png",
        "Flyer_Preview_URL":     f"{tunnel}/Branded_Flyers/QR_Preview_PNGs/qr_Portrait.png",
        "Toolkit_ZIP_URL":       f"{tunnel}/{ZIP_NAME}",
        "Dashboard_Preview_URL": f"{tunnel}/Screenshots/glide_admin_dashboard.png",
        "Landing_Page_URL":      f"{tunnel}/Sponsor_Landing_Page.html"
    }
    print("🔗 Asset URLs:")
    for k, v in assets.items():
        print(f"  {k}: {v}")

    # 8) Authenticate
    print("🔐 Authenticating Sheets & Drive APIs…")
    try:
        if JSON_FILE.exists():
            creds = Credentials.from_service_account_file(str(JSON_FILE), scopes=SCOPES)
            print("✅ Using service_account.json")
        elif KEY_DATA:
            creds = Credentials.from_service_account_info(KEY_DATA, scopes=SCOPES)
            print("✅ Using inline KEY_DATA")
        else:
            raise FileNotFoundError("No credentials found")
    except Exception as e:
        print(f"❌ Auth error: {e}")
        traceback.print_exc()
        return

    # 9) Auto-share if possible
    if build:
        try:
            drive = build("drive", "v3", credentials=creds)
            drive.permissions().create(
                fileId=SHEET_ID,
                body={"role":"writer", "type":"user", "emailAddress": creds.service_account_email},
            ).execute()
            print("🔑 Shared sheet to SA")
        except Exception as e:
            print(f"⚠️ Share failed: {e}")
    else:
        print("⚠️ googleapiclient missing—skipping auto-share")

    # 10) Open/Create worksheet & sync
    client      = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        sheet = spreadsheet.worksheet(SHEET_TAB)
        print(f"✅ Found worksheet '{SHEET_TAB}'")
    except WorksheetNotFound:
        print(f"⚠️ Worksheet '{SHEET_TAB}' not found—creating it")
        sheet = spreadsheet.add_worksheet(title=SHEET_TAB, rows="100", cols=str(len(assets)))
        sheet.append_row(list(assets.keys()))
        print(f"✅ Created worksheet '{SHEET_TAB}' with headers")

    print("📤 Syncing to Glide sheet…")
    headers = sheet.row_values(1)
    for col in assets:
        if col not in headers:
            headers.append(col)
            sheet.update_cell(1, len(headers), col)
    for col, url in assets.items():
        idx = headers.index(col) + 1
        sheet.update_cell(2, idx, url)
        print(f"✅ Updated {col} → {url}")

    # 11) Debug dump
    print("\n🔍 Debug: Worksheets:")
    for ws in spreadsheet.worksheets():
        print(f"  • {ws.title}")
    try:
        print("🔍 Debug: Row2 →", spreadsheet.worksheet(SHEET_TAB).row_values(2))
    except:
        pass

    # 12) Finish
    print(f"\n🎉 Deploy complete! Landing page:\n  {tunnel}/Sponsor_Landing_Page.html")
    print(f"Refresh Glide → {GLIDE}/dl/d0a5f4\n")


if __name__ == "__main__":
    main()
