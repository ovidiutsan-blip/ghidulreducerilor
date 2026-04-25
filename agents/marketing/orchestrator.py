"""
orchestrator.py — Agent principal de marketing.

Rulează zilnic din GitHub Actions și:
1. Selectează top deals de promovat
2. Verifică fiecare deal live (link valid)
3. Generează posturi Facebook gata de copiat
4. Vineri: trimite newsletter via Brevo
5. Generează raport de performanță
6. Trimite email zilnic cu drafturi + raport (via Brevo transactional)

Env vars necesare:
  BREVO_API_KEY         — obligatoriu
  BREVO_LIST_ID         — ID lista abonați (default: 2)
  MARKETING_EMAIL       — email unde se primesc draft-urile zilnice (default: contact@ghidulreducerilor.ro)
"""

import json
import os
import sys
import requests
from pathlib import Path
from datetime import datetime

# Adaugă agents/ în path
BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from deal_selector   import select_top_deals, mark_as_promoted, format_deal_summary
from facebook_agent  import generate_posts, save_posts
from performance_agent import analyze, save_report, print_report

BREVO_API_KEY   = os.environ.get("BREVO_API_KEY", "")
MARKETING_EMAIL = os.environ.get("MARKETING_EMAIL", "contact@ghidulreducerilor.ro")
SITE_BASE       = "https://ghidulreducerilor.ro"
TODAY           = datetime.now()
TODAY_STR       = TODAY.strftime("%Y-%m-%d")
IS_FRIDAY       = TODAY.weekday() == 4


def send_daily_digest(posts_data: dict, perf_data: dict, deals: list[dict]) -> bool:
    """
    Trimite email zilnic cu:
    - Raportul de performanță
    - Posturile FB gata de copiat
    via Brevo transactional API.
    """
    if not BREVO_API_KEY:
        print("[orchestrator] BREVO_API_KEY lipsă — skip email digest")
        return False

    # Build HTML
    perf_section = f"""
    <div style="background:#f0f7ff; border-radius:12px; padding:16px 20px; margin-bottom:20px;">
      <h3 style="margin:0 0 8px; color:#1D3557;">📊 Performanță ieri</h3>
      <p style="margin:4px 0; color:#555;">Click-uri azi: <strong>{perf_data.get('clicks_today', 0)}</strong></p>
      <p style="margin:4px 0; color:#555;">Click-uri ieri: <strong>{perf_data.get('clicks_yesterday', 0)}</strong></p>
      <p style="margin:4px 0; color:#555; font-style:italic;">{perf_data.get('insight', '')}</p>
    </div>"""

    posts_section = ""
    for i, post in enumerate(posts_data.get("posts", []), 1):
        text_escaped = post["text"].replace("\n", "<br/>").replace("<", "&lt;").replace(">", "&gt;")
        posts_section += f"""
    <div style="background:#fff; border:1px solid #eee; border-radius:8px; padding:16px; margin-bottom:16px;">
      <p style="margin:0 0 8px; font-size:12px; color:#888; text-transform:uppercase;">POST {i} — {post['tip'].replace('_', ' ')}</p>
      <p style="margin:0 0 8px; font-size:13px; color:#555;">Grupuri: <strong>{', '.join(post.get('grupuri_recomandate', []))}</strong></p>
      <div style="background:#f9f9f9; border-radius:6px; padding:12px; font-size:14px; white-space:pre-wrap; line-height:1.6;">
        {text_escaped}
      </div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"/></head>
<body style="font-family:Arial,sans-serif; color:#333; max-width:640px; margin:0 auto; padding:20px;">
  <h2 style="color:#1D3557;">🤖 Raport zilnic GhidulReducerilor — {TODAY_STR}</h2>
  <p style="color:#888;">Deal-uri verificate: {posts_data.get('deals_verified', 0)} | Posturi generate: {len(posts_data.get('posts', []))}</p>

  {perf_section}

  <h3 style="color:#1D3557;">📱 Posturi Facebook — copiază și postează</h3>
  {posts_section}

  <div style="background:#fff8f0; border-radius:8px; padding:16px; margin-top:20px;">
    <p style="margin:0; font-size:13px; color:#888;">
      Grupuri principale: <strong>Oferte Romania</strong> | <strong>Reduceri Romania</strong> | <strong>Vânătoare de chilipiruri</strong><br/>
      Postează 1-2 posturi pe zi, în ore de vârf (ora 8-9, 12-13, 20-21).
    </p>
  </div>
</body></html>"""

    payload = {
        "sender":      {"name": "GhidulReducerilor Bot", "email": "noreply@ghidulreducerilor.ro"},
        "to":          [{"email": MARKETING_EMAIL}],
        "subject":     f"📱 Posturi FB + raport — {TODAY_STR}",
        "htmlContent": html,
    }
    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    ok = resp.status_code in (200, 201)
    print(f"[orchestrator] Email digest {'trimis' if ok else 'EROARE'}: {resp.status_code}")
    return ok


def run():
    print(f"\n{'='*60}")
    print(f"🚀 Marketing Orchestrator — {TODAY_STR}")
    print(f"{'='*60}\n")

    # ── 1. Selectare deals ────────────────────────────────────────────────────
    print("1️⃣  Selectare top deals...")
    deals = select_top_deals(8)
    print(f"   → {len(deals)} deals selectate")
    for d in deals:
        print(f"      {format_deal_summary(d)}")

    if not deals:
        print("   ⚠️  Niciun deal eligibil — exit")
        return {"status": "no_deals"}

    # ── 2. Generare posturi Facebook (cu verificare live) ─────────────────────
    print("\n2️⃣  Generare posturi Facebook (verificare live links)...")
    posts_data = generate_posts(deals, verify_live=True)
    posts_path = save_posts(posts_data)
    print(f"   → {len(posts_data['posts'])} posturi generate")
    print(f"   → {posts_data['deals_verified']} deal-uri cu linkuri valide")
    if posts_data['deals_skipped'] > 0:
        print(f"   ⚠️  {posts_data['deals_skipped']} deal-uri cu linkuri moarte — skip")
    print(f"   → Salvat: {posts_path}")

    # ── 3. Marchează deals ca promovate ──────────────────────────────────────
    promoted_ids = [p["deal_id"] for p in posts_data["posts"] if p.get("deal_id")]
    mark_as_promoted(list(set(promoted_ids)))
    print(f"\n3️⃣  {len(set(promoted_ids))} deal-uri marcate ca promovate")

    # ── 4. Raport performanță ─────────────────────────────────────────────────
    print("\n4️⃣  Generare raport performanță...")
    perf_data = analyze(days_back=7)
    perf_path = save_report(perf_data)
    print_report(perf_data)
    print(f"   Salvat: {perf_path}")

    # ── 5. Newsletter (doar vineri) ───────────────────────────────────────────
    newsletter_sent = False
    if IS_FRIDAY:
        print("\n5️⃣  Este vineri — trimit newsletter...")
        try:
            from newsletter_agent import run as send_newsletter
            nl_result = send_newsletter(dry_run=False)
            newsletter_sent = nl_result.get("sent", False)
            print(f"   → Newsletter {'trimis' if newsletter_sent else 'EROARE'}")
        except Exception as e:
            print(f"   ⚠️  Newsletter error: {e}")
    else:
        print(f"\n5️⃣  Newsletter skip (nu e vineri — e {TODAY.strftime('%A')})")

    # ── 6. Email zilnic cu draft-urile ────────────────────────────────────────
    print("\n6️⃣  Trimitere email zilnic cu posturi FB + raport...")
    digest_sent = send_daily_digest(posts_data, perf_data, deals)

    # ── Sumar final ──────────────────────────────────────────────────────────
    result = {
        "date":               TODAY_STR,
        "deals_selected":     len(deals),
        "posts_generated":    len(posts_data["posts"]),
        "deals_live_ok":      posts_data["deals_verified"],
        "deals_dead_skipped": posts_data["deals_skipped"],
        "performance_clicks": perf_data["clicks_today"],
        "newsletter_sent":    newsletter_sent,
        "digest_sent":        digest_sent,
    }

    print(f"\n{'='*60}")
    print("✅ Orchestrator terminat:")
    for k, v in result.items():
        print(f"   {k}: {v}")

    # Salvare sumar
    summary_path = BASE / "data" / "marketing" / f"summary_{TODAY_STR}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"   Sumar: {summary_path}")

    return result


if __name__ == "__main__":
    run()
