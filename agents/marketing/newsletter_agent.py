"""
newsletter_agent.py — Compune și trimite newsletter săptămânal via Brevo.

Trimite automat vineri la 10:00 (configurat în pipeline).
Conține top 6 deals ale săptămânii + 1 cod promo dacă există.
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime

BASE       = Path(__file__).parent.parent.parent
DEALS_PATH = BASE / "data" / "deals.json"
CODES_PATH = BASE / "data" / "codes.json"

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_LIST_ID = int(os.environ.get("BREVO_LIST_ID", "2"))
SITE_BASE     = "https://ghidulreducerilor.ro"


def load_top_deals(n: int = 6) -> list[dict]:
    """Top N deals pentru newsletter (diversitate magazine, reducere mare)."""
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)

    active = [d for d in deals if d.get("activ", True) and
              (d.get("procent_reducere") or d.get("discount_percent") or 0) >= 40]
    active.sort(key=lambda d: (d.get("procent_reducere") or d.get("discount_percent") or 0), reverse=True)

    # Diversitate magazine
    seen_stores: set = set()
    selected = []
    for d in active:
        store = d.get("magazin") or d.get("store", "")
        if store in seen_stores:
            continue
        seen_stores.add(store)
        selected.append(d)
        if len(selected) >= n:
            break
    return selected


def load_active_codes() -> list[dict]:
    """Coduri promo active."""
    if not CODES_PATH.exists():
        return []
    with open(CODES_PATH, encoding="utf-8") as f:
        codes = json.load(f)
    today = datetime.now().strftime("%Y-%m-%d")
    return [c for c in codes if c.get("data_expirare", "9999") >= today]


def build_html_email(deals: list[dict], codes: list[dict]) -> str:
    """Generează HTML-ul emailului."""
    today_str = datetime.now().strftime("%d %B %Y")

    deals_html = ""
    for d in deals:
        titlu = (d.get("titlu") or d.get("title", ""))[:60]
        pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
        pret  = d.get("pret_redus") or d.get("price") or 0
        orig  = d.get("pret_original") or d.get("originalPrice") or 0
        store = (d.get("magazin") or d.get("store", "")).capitalize()
        slug  = d.get("slug", "")
        link  = f"{SITE_BASE}/deals/{slug}" if slug else (d.get("link_afiliat") or d.get("affiliate_url", "#"))
        imagine = d.get("imagine_url") or d.get("image") or ""

        deals_html += f"""
        <tr>
          <td style="padding:16px 0; border-bottom:1px solid #f0f0f0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="80" style="vertical-align:top;">
                  {'<img src="' + imagine + '" width="72" style="border-radius:8px;" />' if imagine else ''}
                </td>
                <td style="padding-left:12px; vertical-align:top;">
                  <p style="margin:0; font-weight:bold; color:#1D3557; font-size:15px;">{titlu}</p>
                  <p style="margin:4px 0; color:#888; font-size:13px;">{store}</p>
                  <p style="margin:4px 0;">
                    <span style="font-size:20px; font-weight:bold; color:#E63946;">{pret} lei</span>
                    <span style="font-size:13px; color:#aaa; text-decoration:line-through; margin-left:8px;">{orig} lei</span>
                    <span style="background:#E63946; color:white; font-size:12px; padding:2px 6px; border-radius:4px; margin-left:8px;">-{pct}%</span>
                  </p>
                  <a href="{link}" style="display:inline-block; margin-top:8px; background:#F4A261; color:white; padding:6px 16px; border-radius:6px; text-decoration:none; font-size:13px; font-weight:bold;">
                    Vezi oferta →
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    codes_html = ""
    if codes:
        c = codes[0]
        codes_html = f"""
        <tr>
          <td style="padding:20px; background:#FFF8F0; border-radius:12px; margin-top:20px;">
            <p style="margin:0; font-size:13px; color:#888; text-transform:uppercase; letter-spacing:1px;">COD PROMO</p>
            <p style="margin:4px 0; font-size:22px; font-weight:bold; color:#1D3557; letter-spacing:3px; background:#fff; padding:8px 16px; border-radius:8px; display:inline-block; border:2px dashed #F4A261;">
              {c.get('cod', '')}
            </p>
            <p style="margin:8px 0 0; color:#555; font-size:14px;">{c.get('descriere', '')}</p>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width,initial-scale=1" /></head>
<body style="margin:0; padding:0; background:#f5f5f5; font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5; padding:20px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff; border-radius:16px; overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:#1D3557; padding:24px 32px;">
            <a href="{SITE_BASE}" style="text-decoration:none;">
              <span style="color:#F4A261; font-size:22px; font-weight:bold;">GhidulReducerilor.ro</span>
            </a>
            <p style="margin:4px 0 0; color:rgba(255,255,255,0.7); font-size:13px;">
              Cele mai bune reduceri din România — {today_str}
            </p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:24px 32px;">
            <h2 style="color:#1D3557; margin:0 0 4px; font-size:20px;">🔥 Top reduceri ale săptămânii</h2>
            <p style="color:#888; margin:0 0 20px; font-size:14px;">Am ales cele mai bune oferte pentru tine:</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              {deals_html}
              {codes_html}
            </table>
            <div style="text-align:center; margin-top:28px;">
              <a href="{SITE_BASE}" style="background:#1D3557; color:white; padding:12px 28px; border-radius:8px; text-decoration:none; font-weight:bold;">
                Vezi toate reducerile →
              </a>
            </div>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#f9f9f9; padding:16px 32px; border-top:1px solid #eee;">
            <p style="margin:0; font-size:12px; color:#aaa; text-align:center;">
              Ai primit acest email pentru că ești abonat la {SITE_BASE}<br/>
              <a href="{{{{ unsubscribe }}}}" style="color:#aaa;">Dezabonare</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_newsletter(subject: str, html: str, dry_run: bool = False) -> bool:
    """Trimite newsletter via Brevo API."""
    if not BREVO_API_KEY:
        print("[newsletter] BREVO_API_KEY lipsă — skip send")
        return False
    if dry_run:
        print("[newsletter] DRY-RUN — nu trimitem")
        return True

    payload = {
        "sender":     {"name": "GhidulReducerilor.ro", "email": "noreply@ghidulreducerilor.ro"},
        "replyTo":    {"email": "contact@ghidulreducerilor.ro"},
        "subject":    subject,
        "htmlContent": html,
        "recipients": {"listIds": [BREVO_LIST_ID]},
        "scheduledAt": None,  # trimite imediat
    }
    resp = requests.post(
        "https://api.brevo.com/v3/emailCampaigns",
        headers={
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    if resp.status_code in (200, 201):
        campaign_id = resp.json().get("id")
        # Trimite imediat campania
        send_resp = requests.post(
            f"https://api.brevo.com/v3/emailCampaigns/{campaign_id}/sendNow",
            headers={"api-key": BREVO_API_KEY},
            timeout=15,
        )
        print(f"[newsletter] Campanie trimisă — ID {campaign_id}, status {send_resp.status_code}")
        return send_resp.status_code == 204
    else:
        print(f"[newsletter] Eroare Brevo: {resp.status_code} — {resp.text[:200]}")
        return False


def run(dry_run: bool = False) -> dict:
    """Rulare completă: selectare deals → generare HTML → trimitere."""
    deals = load_top_deals(6)
    codes = load_active_codes()
    print(f"[newsletter] {len(deals)} deals + {len(codes)} coduri promo")

    today_str = datetime.now().strftime("%d %B %Y")
    subject = f"🔥 Top reduceri {today_str} — economisești până la 75%"
    html = build_html_email(deals, codes)

    # Salvare locală
    out_dir = BASE / "data" / "marketing"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"newsletter_{datetime.now().strftime('%Y-%m-%d')}.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"[newsletter] HTML salvat: {out_file}")

    sent = send_newsletter(subject, html, dry_run=dry_run)
    return {"deals": len(deals), "codes": len(codes), "sent": sent, "subject": subject}


if __name__ == "__main__":
    import sys
    dry = "--dry" in sys.argv
    result = run(dry_run=dry)
    print(f"\nRezultat: {result}")
