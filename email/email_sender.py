"""
Email Sender — Modul central de trimitere email via Brevo API
Folosit de agentii Python si de orchestrator.

Utilizare:
  python email/email_sender.py --test --to your@email.com
  python email/email_sender.py --test-all-templates --to your@email.com
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Adauga directorul parinte la path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from renderer import (
    render_confirmare,
    render_newsletter,
    render_flash_alert,
    render_digest,
    render_reengagement,
)

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SENDERS = {
    "reduceri": {
        "email": os.getenv("BREVO_SENDER_REDUCERI", "reduceri@ghidulreducerilor.ro"),
        "name": "GhidulReducerilor.ro",
    },
    "alerte": {
        "email": os.getenv("BREVO_SENDER_ALERTE", "alerte@ghidulreducerilor.ro"),
        "name": "Alerte Reduceri",
    },
    "noreply": {
        "email": os.getenv("BREVO_SENDER_NOREPLY", "noreply@ghidulreducerilor.ro"),
        "name": "GhidulReducerilor.ro",
    },
    "hello": {
        "email": os.getenv("BREVO_SENDER_HELLO", "hello@ghidulreducerilor.ro"),
        "name": "GhidulReducerilor.ro",
    },
}

LIST_IDS = {
    "newsletter": int(os.getenv("BREVO_LIST_NEWSLETTER", "1")),
    "alerte_flash": int(os.getenv("BREVO_LIST_ALERTE_FLASH", "2")),
    "digest_zilnic": int(os.getenv("BREVO_LIST_DIGEST_ZILNIC", "3")),
}


def _log(msg):
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"email_{today}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _get_api():
    """Returneaza instanta Brevo API configurata."""
    if not BREVO_API_KEY or BREVO_API_KEY.startswith("xkeysib-your"):
        return None

    try:
        import sib_api_v3_sdk

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = BREVO_API_KEY
        return sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
    except ImportError:
        _log("[EMAIL] sib-api-v3-sdk neinstalat")
        return None


def send_email(to_email, subject, html_content, sender_key="reduceri"):
    """Trimite un email individual via Brevo API."""
    api = _get_api()
    if not api:
        _log(f"[EMAIL] Brevo neconfigurat — skip: {subject} -> {to_email}")
        return False

    try:
        import sib_api_v3_sdk

        sender = SENDERS.get(sender_key, SENDERS["reduceri"])
        email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={"email": sender["email"], "name": sender["name"]},
            subject=subject,
            html_content=html_content,
        )
        api.send_transac_email(email)
        _log(f"[EMAIL] Trimis: {subject} -> {to_email}")
        return True
    except Exception as e:
        _log(f"[EMAIL] Eroare trimitere: {e}")
        return False


def send_to_list(list_id, subject, html_content, sender_key="reduceri"):
    """Trimite o campanie email la o lista Brevo."""
    if not BREVO_API_KEY or BREVO_API_KEY.startswith("xkeysib-your"):
        _log(f"[EMAIL] Brevo neconfigurat — skip campanie: {subject}")
        return False

    try:
        import sib_api_v3_sdk

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = BREVO_API_KEY
        api = sib_api_v3_sdk.EmailCampaignsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        sender = SENDERS.get(sender_key, SENDERS["reduceri"])
        campaign = sib_api_v3_sdk.CreateEmailCampaign(
            name=f"{subject} — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            subject=subject,
            sender={"email": sender["email"], "name": sender["name"]},
            html_content=html_content,
            recipients={"listIds": [list_id]},
        )
        result = api.create_email_campaign(campaign)
        campaign_id = result.id

        # Trimite campania imediat
        api.send_email_campaign_now(campaign_id)
        _log(f"[EMAIL] Campanie trimisa: {subject} (ID: {campaign_id})")
        return True
    except Exception as e:
        _log(f"[EMAIL] Eroare campanie: {e}")
        return False


def send_flash_alert(offers):
    """Trimite alerta flash pentru oferte cu reducere >50%."""
    if not offers:
        return False

    for offer in offers[:3]:
        html = render_flash_alert(offer, ore_ramase=24)
        subject = f"ALERTA: {offer['titlu']} cu -{offer['procent_reducere']}%"
        send_to_list(LIST_IDS["alerte_flash"], subject, html, sender_key="alerte")

    _log(f"[EMAIL] Flash alert trimis pentru {min(len(offers), 3)} oferte")
    return True


def send_weekly_newsletter(offers, coduri_promo=None):
    """Trimite newsletter-ul saptamanal."""
    data = datetime.now().strftime("%d %B %Y")
    html = render_newsletter(offers, coduri_promo=coduri_promo, data=data)
    subject = f"Top reduceri saptamana asta | {data}"
    return send_to_list(LIST_IDS["newsletter"], subject, html, sender_key="reduceri")


def send_daily_digest(offers):
    """Trimite digest-ul zilnic."""
    data = datetime.now().strftime("%d.%m.%Y")
    html = render_digest(offers, data=data)
    subject = f"Ofertele de azi, {data}"
    return send_to_list(LIST_IDS["digest_zilnic"], subject, html, sender_key="reduceri")


def send_confirmation(to_email, prenume="", categorii=None):
    """Trimite email de confirmare la abonare noua."""
    html = render_confirmare(prenume=prenume, categorii=categorii)
    subject = "Esti abonat! Primele reduceri te asteapta"
    return send_email(to_email, subject, html, sender_key="noreply")


def _load_sample_offers():
    """Incarca oferte sample din deals.json pentru testare."""
    deals_file = BASE_DIR / "data" / "deals.json"
    if deals_file.exists():
        with open(deals_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def main():
    parser = argparse.ArgumentParser(description="Email Sender — GhidulReducerilor.ro")
    parser.add_argument("--test", action="store_true", help="Trimite email de test")
    parser.add_argument("--test-all-templates", action="store_true", help="Trimite toate template-urile ca test")
    parser.add_argument("--test-subscribe", action="store_true", help="Simuleaza abonare noua")
    parser.add_argument("--to", type=str, default="", help="Email destinatar test")
    parser.add_argument("--email", type=str, default="", help="Email pentru test-subscribe")
    parser.add_argument("--prenume", type=str, default="Test", help="Prenume pentru test")
    args = parser.parse_args()

    to = args.to or os.getenv("ADMIN_EMAIL", "")
    if not to and (args.test or args.test_all_templates):
        print("Specifica --to email@example.com")
        sys.exit(1)

    offers = _load_sample_offers()

    if args.test:
        html = render_newsletter(offers[:6], data=datetime.now().strftime("%d %B %Y"))
        send_email(to, "[TEST] Newsletter GhidulReducerilor.ro", html)

    elif args.test_all_templates:
        print(f"Trimit toate 5 template-urile la {to}...")

        send_email(to, "[TEST 1/5] Confirmare Abonare",
                   render_confirmare(prenume="Catalin", categorii=["fashion", "electronice"]),
                   sender_key="noreply")

        send_email(to, "[TEST 2/5] Newsletter Saptamanal",
                   render_newsletter(offers[:6], data=datetime.now().strftime("%d %B %Y")),
                   sender_key="reduceri")

        if offers:
            send_email(to, "[TEST 3/5] Alerta Flash",
                       render_flash_alert(offers[0], ore_ramase=12),
                       sender_key="alerte")

        send_email(to, "[TEST 4/5] Digest Zilnic",
                   render_digest(offers[:3], prenume="Catalin", data=datetime.now().strftime("%d.%m.%Y")),
                   sender_key="reduceri")

        send_email(to, "[TEST 5/5] Re-engagement",
                   render_reengagement(offers[:5], prenume="Catalin"),
                   sender_key="hello")

        print("Toate 5 template-urile trimise!")

    elif args.test_subscribe:
        email = args.email or "test@example.com"
        send_confirmation(email, prenume=args.prenume, categorii=["fashion"])

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
