"""
Brevo Setup & Verification — Verifica conexiunea si configureaza sender-ii

Utilizare:
  python email/brevo_setup.py --verify
  python email/brevo_setup.py --senders
  python email/brevo_setup.py --add-sender hello@ghidulreducerilor.ro "GhidulReducerilor.ro"
"""

import os
import sys
import argparse

from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")


def _get_client():
    if not BREVO_API_KEY or BREVO_API_KEY.startswith("xkeysib-your"):
        print("[BREVO] API key lipsa sau placeholder. Seteaza BREVO_API_KEY in .env")
        return None
    try:
        import sib_api_v3_sdk
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = BREVO_API_KEY
        return sib_api_v3_sdk.ApiClient(configuration)
    except ImportError:
        print("[BREVO] sib-api-v3-sdk neinstalat. Ruleaza: pip install sib-api-v3-sdk")
        return None


def verify_connection():
    """Testeaza ca API key-ul e valid."""
    client = _get_client()
    if not client:
        return False
    try:
        import sib_api_v3_sdk
        api = sib_api_v3_sdk.AccountApi(client)
        account = api.get_account()
        print(f"[BREVO] Conectat cu succes!")
        print(f"  Companie: {account.company_name}")
        print(f"  Email: {account.email}")
        plan = account.plan[0] if account.plan else None
        if plan:
            print(f"  Plan: {plan.type} ({plan.credits} credite)")
        return True
    except Exception as e:
        print(f"[BREVO] Eroare conexiune: {e}")
        return False


def list_senders():
    """Listeaza sender-ii configurati in Brevo."""
    client = _get_client()
    if not client:
        return
    try:
        import sib_api_v3_sdk
        api = sib_api_v3_sdk.SendersApi(client)
        result = api.get_senders()
        print(f"\n[BREVO] Sender-i configurati ({len(result.senders)}):")
        for s in result.senders:
            status = "VERIFICAT" if s.active else "NEVERIFICAT"
            print(f"  {s.email} ({s.name}) — {status}")
    except Exception as e:
        print(f"[BREVO] Eroare listare sender-i: {e}")


def add_sender(email, name):
    """Adauga un sender nou in Brevo."""
    client = _get_client()
    if not client:
        return
    try:
        import sib_api_v3_sdk
        api = sib_api_v3_sdk.SendersApi(client)
        sender = sib_api_v3_sdk.CreateSender(name=name, email=email)
        result = api.create_sender(sender)
        print(f"[BREVO] Sender adaugat: {email} ({name}) — ID: {result.id}")
        print(f"  Verifica emailul {email} pentru confirmare.")
    except Exception as e:
        print(f"[BREVO] Eroare adaugare sender: {e}")


def list_contacts_lists():
    """Listeaza listele de contacte din Brevo."""
    client = _get_client()
    if not client:
        return
    try:
        import sib_api_v3_sdk
        api = sib_api_v3_sdk.ContactsApi(client)
        result = api.get_lists()
        print(f"\n[BREVO] Liste de contacte ({result.count}):")
        for lst in result.lists:
            print(f"  ID {lst.id}: {lst.name} — {lst.total_subscribers} abonati")
    except Exception as e:
        print(f"[BREVO] Eroare listare: {e}")


def get_smtp_config():
    """Afiseaza configuratia SMTP pentru referinta."""
    print("\n[BREVO] Configuratie SMTP:")
    print(f"  Host: smtp-relay.brevo.com")
    print(f"  Port: 587 (TLS)")
    print(f"  User: {os.getenv('SMTP_USER', '<seteaza in .env>')}")
    print(f"  Pass: {os.getenv('SMTP_PASS', '<seteaza in .env>')}")


def main():
    parser = argparse.ArgumentParser(description="Brevo Setup — GhidulReducerilor.ro")
    parser.add_argument("--verify", action="store_true", help="Verifica conexiunea Brevo")
    parser.add_argument("--senders", action="store_true", help="Listeaza sender-ii")
    parser.add_argument("--lists", action="store_true", help="Listeaza listele de contacte")
    parser.add_argument("--add-sender", nargs=2, metavar=("EMAIL", "NAME"), help="Adauga sender")
    parser.add_argument("--smtp", action="store_true", help="Afiseaza config SMTP")
    parser.add_argument("--all", action="store_true", help="Ruleaza toate verificarile")
    args = parser.parse_args()

    if args.all or args.verify:
        verify_connection()
    if args.all or args.senders:
        list_senders()
    if args.all or args.lists:
        list_contacts_lists()
    if args.add_sender:
        add_sender(args.add_sender[0], args.add_sender[1])
    if args.all or args.smtp:
        get_smtp_config()
    if not any(vars(args).values()):
        parser.print_help()


if __name__ == "__main__":
    main()
