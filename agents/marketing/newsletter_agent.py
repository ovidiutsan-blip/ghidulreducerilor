"""
newsletter_agent.py — Compune și trimite newsletter săptămânal via Brevo.

Rulează automat vineri la 08:00 (Task Scheduler: GhidulReducerilor_Newsletter).
Conține top 6 deals ale săptămânii + coduri promo dacă există.

Utilizare:
    python newsletter_agent.py           # trimite direct
    python newsletter_agent.py --dry     # generează HTML fără trimitere
    python newsletter_agent.py test      # trimite test la BREVO_TEST_EMAIL
"""

import json
import os
import sys
import requests
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE       = Path(__file__).parent.parent.parent
DEALS_PATH = BASE / "data" / "deals.json"
CODES_PATH = BASE / "data" / "codes.json"

BREVO_API_KEY      = os.environ.get("BREVO_API_KEY", "")
BREVO_LIST_ID      = int(os.environ.get("BREVO_LIST_NEWSLETTER", os.environ.get("BREVO_LIST_ID", "3")))
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_REDUCERI", "reduceri@ghidulreducerilor.ro")
BREVO_TEST_EMAIL   = os.environ.get("BREVO_TEST_EMAIL", os.environ.get("USER_EMAIL", "ovidiutsan@gmail.com"))

SITE_BASE = "https://ghidulreducerilor.ro"
UTM       = "?utm_source=email&utm_medium=newsletter&utm_campaign=weekly"


def utm(url: str) -> str:
    """Adaugă UTM tracking la un URL."""
    if not url or url == "#":
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + "utm_source=email&utm_medium=newsletter&utm_campaign=weekly"


def load_top_deals(n: int = 6) -> list[dict]:
    """Top N deals pentru newsletter (diversitate magazine, reducere ≥40%)."""
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)

    active = [d for d in deals if d.get("activ", True) and
              (d.get("procent_reducere") or d.get("discount_percent") or 0) >= 40]
    active.sort(key=lambda d: (d.get("procent_reducere") or d.get("discount_percent") or 0), reverse=True)

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

    # Dacă nu avem suficiente cu ≥40%, completăm cu orice activ
    if len(selected) < n:
        for d in deals:
            if d.get("activ", True) and d not in selected:
                store = d.get("magazin") or d.get("store", "")
                if store not in seen_stores:
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
    """Generează HTML-ul emailului cu UTM tracking pe toate link-urile."""
    today_str = datetime.now().strftime("%d %B %Y")

    deals_html = ""
    for d in deals:
        titlu   = (d.get("titlu") or d.get("title", "Ofertă specială"))[:70]
        pct     = d.get("procent_reducere") or d.get("discount_percent") or 0
        pret    = d.get("pret_redus") or d.get("price") or ""
        orig    = d.get("pret_original") or d.get("originalPrice") or ""
        store   = (d.get("magazin") or d.get("store", "")).capitalize()
        slug    = d.get("slug", "")
        raw_link = (
            f"{SITE_BASE}/deals/{slug}" if slug
            else (d.get("link_afiliat") or d.get("affiliate_url") or SITE_BASE)
        )
        link    = utm(raw_link)
        imagine = d.get("imagine_url") or d.get("image") or ""

        pret_html = ""
        if pret:
            pret_html += f'<span style="font-size:20px;font-weight:bold;color:#E63946;">{pret} lei</span>'
        if orig:
            pret_html += f'<span style="font-size:13px;color:#aaa;text-decoration:line-through;margin-left:8px;">{orig} lei</span>'
        if pct:
            pret_html += f'<span style="background:#E63946;color:white;font-size:12px;padding:2px 6px;border-radius:4px;margin-left:8px;">-{pct}%</span>'

        img_html = ""
        if imagine:
            img_html = f'<img src="{imagine}" width="72" height="72" style="border-radius:8px;object-fit:cover;display:block;" />'

        deals_html += f"""
        <tr>
          <td style="padding:16px 0;border-bottom:1px solid #f0f0f0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="80" style="vertical-align:top;">{img_html}</td>
                <td style="padding-left:12px;vertical-align:top;">
                  <p style="margin:0;font-weight:bold;color:#1D3557;font-size:15px;line-height:1.3;">{titlu}</p>
                  <p style="margin:4px 0;color:#888;font-size:13px;">{store}</p>
                  <p style="margin:6px 0;">{pret_html}</p>
                  <a href="{link}" style="display:inline-block;margin-top:8px;background:#F4A261;color:white;padding:7px 18px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:bold;">
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
        store_cod = c.get('magazin', '') or c.get('store', '')
        codes_html = f"""
        <tr>
          <td style="padding:20px;background:#FFF8F0;border-radius:12px;margin-top:24px;border:1px solid #FFE0B2;">
            <p style="margin:0;font-size:11px;color:#F4A261;text-transform:uppercase;letter-spacing:1.5px;font-weight:bold;">✨ Cod promo{' — ' + store_cod if store_cod else ''}</p>
            <p style="margin:8px 0 4px;font-size:24px;font-weight:bold;color:#1D3557;letter-spacing:4px;background:#fff;padding:8px 16px;border-radius:8px;display:inline-block;border:2px dashed #F4A261;">
              {c.get('cod', '')}
            </p>
            <p style="margin:8px 0 0;color:#555;font-size:14px;">{c.get('descriere', '')}</p>
          </td>
        </tr>"""

    site_link = utm(SITE_BASE)
    return f"""<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Top reduceri ale săptămânii — GhidulReducerilor.ro</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:24px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#1D3557;padding:28px 32px;">
            <a href="{utm(SITE_BASE)}" style="text-decoration:none;">
              <span style="color:#F4A261;font-size:24px;font-weight:bold;letter-spacing:-0.5px;">GhidulReducerilor.ro</span>
            </a>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.65);font-size:13px;">
              Cele mai bune reduceri din România · {today_str}
            </p>
          </td>
        </tr>

        <!-- Intro -->
        <tr>
          <td style="padding:28px 32px 0;">
            <h2 style="color:#1D3557;margin:0 0 6px;font-size:22px;">🔥 Top reduceri ale săptămânii</h2>
            <p style="color:#666;margin:0 0 20px;font-size:14px;line-height:1.5;">
              Am selectat manual cele mai bune oferte active din România. Stocuri limitate!
            </p>
          </td>
        </tr>

        <!-- Deals -->
        <tr>
          <td style="padding:0 32px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              {deals_html}
            </table>
          </td>
        </tr>

        <!-- Cod promo (dacă există) -->
        {(f'<tr><td style="padding:16px 32px 0;">' + codes_html + '</td></tr>') if codes_html else ''}

        <!-- CTA -->
        <tr>
          <td style="padding:28px 32px;text-align:center;">
            <a href="{site_link}" style="background:#1D3557;color:white;padding:13px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;display:inline-block;">
              Vezi toate reducerile →
            </a>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f9f9f9;padding:18px 32px;border-top:1px solid #eee;">
            <p style="margin:0;font-size:12px;color:#aaa;text-align:center;line-height:1.6;">
              Ai primit acest email pentru că ești abonat la
              <a href="{SITE_BASE}" style="color:#F4A261;text-decoration:none;">ghidulreducerilor.ro</a><br/>
              <a href="{{{{ unsubscribe }}}}" style="color:#ccc;font-size:11px;">Dezabonare</a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_newsletter(subject: str, html: str, dry_run: bool = False,
                    test_email: str = "") -> bool:
    """Trimite newsletter via Brevo API."""
    if not BREVO_API_KEY:
        print("[newsletter] BREVO_API_KEY lipsă — adaugă în .env")
        return False
    if dry_run:
        print("[newsletter] DRY-RUN — nu trimitem")
        return True

    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Trimitere test la o adresă specifică
    if test_email:
        payload = {
            "sender":      {"name": "GhidulReducerilor.ro", "email": BREVO_SENDER_EMAIL},
            "to":          [{"email": test_email}],
            "replyTo":     {"email": "contact@ghidulreducerilor.ro"},
            "subject":     f"[TEST] {subject}",
            "htmlContent": html,
        }
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers=headers,
            json=payload,
            timeout=15,
        )
        if resp.status_code in (200, 201):
            print(f"[newsletter] Email test trimis la {test_email} ✓")
            return True
        else:
            print(f"[newsletter] Eroare test: {resp.status_code} — {resp.text[:300]}")
            return False

    # Campanie normală → create + sendNow
    payload = {
        "sender":      {"name": "GhidulReducerilor.ro", "email": BREVO_SENDER_EMAIL},
        "replyTo":     {"email": "contact@ghidulreducerilor.ro"},
        "subject":     subject,
        "htmlContent": html,
        "recipients":  {"listIds": [BREVO_LIST_ID]},
    }
    resp = requests.post(
        "https://api.brevo.com/v3/emailCampaigns",
        headers=headers,
        json=payload,
        timeout=15,
    )
    if resp.status_code in (200, 201):
        campaign_id = resp.json().get("id")
        print(f"[newsletter] Campanie creată ID={campaign_id}")
        send_resp = requests.post(
            f"https://api.brevo.com/v3/emailCampaigns/{campaign_id}/sendNow",
            headers={"api-key": BREVO_API_KEY},
            timeout=15,
        )
        ok = send_resp.status_code == 204
        if ok:
            print(f"[newsletter] ✓ Campanie trimisă — ID {campaign_id}")
        else:
            print(f"[newsletter] Eroare sendNow: {send_resp.status_code} — {send_resp.text[:200]}")
        return ok
    else:
        print(f"[newsletter] Eroare Brevo: {resp.status_code} — {resp.text[:300]}")
        return False


def run(dry_run: bool = False, test_email: str = "") -> dict:
    """Rulare completă: selectare deals → generare HTML → trimitere."""
    print("[newsletter] Selectez deals...")
    deals = load_top_deals(6)
    codes = load_active_codes()
    print(f"[newsletter] {len(deals)} deals + {len(codes)} coduri promo")

    today_str = datetime.now().strftime("%d %B %Y")
    pct_max   = max((d.get("procent_reducere") or d.get("discount_percent") or 0 for d in deals), default=50)
    subject   = f"🔥 Top {len(deals)} reduceri {today_str} — până la -{pct_max}%"

    html = build_html_email(deals, codes)

    out_dir  = BASE / "data" / "marketing"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"newsletter_{datetime.now().strftime('%Y-%m-%d')}.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"[newsletter] HTML salvat: {out_file}")

    sent = send_newsletter(subject, html, dry_run=dry_run, test_email=test_email)
    return {
        "deals":    len(deals),
        "codes":    len(codes),
        "sent":     sent,
        "subject":  subject,
        "html_out": str(out_file),
    }


if __name__ == "__main__":
    dry  = "--dry" in sys.argv
    test = "test" in sys.argv
    result = run(
        dry_run=dry,
        test_email=BREVO_TEST_EMAIL if test else "",
    )
    print(f"\n[newsletter] Rezultat: {result}")
