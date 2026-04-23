"""2Performant Token Expiry Monitor.

Makes a lightweight API call (1 product feed, per_page=1) to verify the
DeviseTokenAuth token is still valid. DeviseTokenAuth expires after ~14 days.

Returns exit code 0 if valid, 1 if expired/invalid (credentials need refresh).

Usage:
  python scripts/check_token_expiry.py       # check + print status
  python scripts/check_token_expiry.py -q    # quiet mode (only print on failure)

When to refresh credentials (~14 days):
  1. Go to businessleague.2performant.com (logged in)
  2. DevTools > Application > Cookies > auth_headers value
  3. Update GitHub Secrets:
       gh secret set TWO_PERFORMANT_ACCESS_TOKEN --body "<value>"
       gh secret set TWO_PERFORMANT_CLIENT_ID --body "<value>"
"""
import os, sys
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.2performant.com"


def _clean_env(key: str, default: str = "") -> str:
    return os.getenv(key, default).lstrip("\ufeff").strip()


ACCESS_TOKEN = _clean_env("TWO_PERFORMANT_ACCESS_TOKEN")
CLIENT_ID    = _clean_env("TWO_PERFORMANT_CLIENT_ID")
UID          = _clean_env("TWO_PERFORMANT_UID", "ovidiutsan@yahoo.com")


def check_token(quiet: bool = False) -> bool:
    """Returns True if token is valid, False if expired/invalid.
    Logs a clear WARNING on failure so it's visible in GHA logs.
    """
    if not ACCESS_TOKEN or not CLIENT_ID:
        print("⚠️  WARN: TWO_PERFORMANT_ACCESS_TOKEN / CLIENT_ID not set — token check skipped")
        return True  # Don't block pipeline if secrets are simply missing

    headers = {
        "access-token": ACCESS_TOKEN,
        "token-type":   "Bearer",
        "client":       CLIENT_ID,
        "uid":          UID,
        "Accept":       "application/json",
    }

    try:
        r = requests.get(
            f"{API_BASE}/affiliate/product_feeds",
            headers=headers,
            params={"per_page": 1},
            timeout=10,
        )
    except Exception as e:
        print(f"⚠️  WARN: 2P token check — network error: {e} (not blocking)")
        return True  # Network error ≠ token expiry

    if r.status_code == 200:
        if not quiet:
            print("✅  2P token: VALID")
        return True

    if r.status_code == 401:
        print("=" * 60)
        print("🔴  CRITICAL: 2Performant token EXPIRED or INVALID (HTTP 401)")
        print("    The weekly import will return 0 deals until credentials are refreshed.")
        print()
        print("    HOW TO REFRESH:")
        print("    1. Login → businessleague.2performant.com")
        print("    2. DevTools > Application > Cookies > auth_headers")
        print("    3. Run:")
        print('       gh secret set TWO_PERFORMANT_ACCESS_TOKEN --body "<access-token>"')
        print('       gh secret set TWO_PERFORMANT_CLIENT_ID --body "<client>"')
        print("=" * 60)
        return False

    # Other HTTP errors (403, 429, 5xx) — don't alarm, log and continue
    print(f"⚠️  WARN: 2P token check returned HTTP {r.status_code} (not blocking)")
    return True


def main():
    quiet = "-q" in sys.argv or "--quiet" in sys.argv
    valid = check_token(quiet=quiet)
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
