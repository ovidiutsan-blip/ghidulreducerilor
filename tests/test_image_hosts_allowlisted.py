# -*- coding: utf-8 -*-
"""
Guardrail: toate host-urile din imagine_url (data/deals.json) trebuie să fie
acoperite de allowlist-ul images.remotePatterns din next.config.js.

Context (14 iul 2026): casanewconcept și-a mutat imaginile pe ik.imagekit.io;
URL-urile noi erau valide (200), dar next/image refuza host-ul cu 400 pentru
că nu era în remotePatterns → carduri cu imagini sparte pe site, deși datele
păreau corecte. Testul pică IMEDIAT ce un CDN nou apare în date fără să fie
allowlisted, în loc să descoperim vizual pe site.

Ruleaza:
  Standalone:  py -3 tests/test_image_hosts_allowlisted.py
  Sau pytest:  pytest tests/test_image_hosts_allowlisted.py -v
"""
import json
import pathlib
import re
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _allowlisted_patterns() -> list[str]:
    cfg = (ROOT / "next.config.js").read_text(encoding="utf-8")
    return re.findall(r"hostname:\s*'([^']+)'", cfg)


def _host_matches(host: str, pattern: str) -> bool:
    """Aproximează matching-ul next/image remotePatterns pentru cazurile
    folosite în config: exact ('cdn.x.ro') sau wildcard ('**.x.ro')."""
    if pattern.startswith("**."):
        base = pattern[3:]
        return host == base or host.endswith("." + base)
    return host == pattern


def test_all_image_hosts_allowlisted():
    deals = json.loads((ROOT / "data" / "deals.json").read_text(encoding="utf-8"))
    patterns = _allowlisted_patterns()
    assert patterns, "nu am putut extrage remotePatterns din next.config.js"

    offenders: dict[str, int] = {}
    for d in deals:
        url = d.get("imagine_url") or ""
        if not url.startswith("http"):
            continue  # gol = FallbackImage, nu trece prin optimizer
        host = urlparse(url).hostname or ""
        if not any(_host_matches(host, p) for p in patterns):
            offenders[host] = offenders.get(host, 0) + 1

    assert not offenders, (
        "Host-uri de imagini NEACOPERITE de next.config.js images.remotePatterns "
        f"(next/image le va refuza cu 400 → carduri sparte): {offenders}. "
        "Adaugă host-ul în remotePatterns sau repară imagine_url în date."
    )


def _main():
    try:
        test_all_image_hosts_allowlisted()
        print("  [OK]   test_all_image_hosts_allowlisted")
        return 0
    except AssertionError as e:
        print(f"  [FAIL] test_all_image_hosts_allowlisted: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(_main())
