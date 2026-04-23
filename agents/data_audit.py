"""Data quality audit for ghidulreducerilor.ro.

Runs a battery of checks on data/deals.json and next.config.js to catch:
- Images pointing to placeholder/lazy-loader GIFs
- Image hosts not whitelisted in next.config.js (would break Next/Image)
- Deals with empty or suspect prices (price_vat <= 0, price_disc >= price_vat)
- Deals flagged with broken link_status
- Titles that look scraped (too long, still in Caps-Lock original format)
- Missing required fields (id, product_url, image, magazin)

Exit code: 0 = clean, 1 = warnings, 2 = errors (block deploy).
"""
import json, re, sys
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
DEALS = BASE / "data" / "deals.json"
CONFIG = BASE / "next.config.js"

# Parse whitelist hosts from next.config.js
def parse_whitelist():
    text = CONFIG.read_text(encoding="utf-8")
    hosts = []
    for m in re.finditer(r"hostname:\s*['\"]([^'\"]+)['\"]", text):
        hosts.append(m.group(1))
    return hosts

def host_matches(host: str, whitelist: list[str]) -> bool:
    for pat in whitelist:
        if pat.startswith("**."):
            if host.endswith(pat[2:]) or host == pat[3:]:
                return True
        elif host == pat:
            return True
    return False

def main():
    errors = []
    warnings = []
    stats = defaultdict(int)

    with open(DEALS, encoding="utf-8") as f:
        deals = json.load(f)
    stats["total_deals"] = len(deals)

    whitelist = parse_whitelist()
    stats["whitelisted_hosts"] = len(whitelist)

    # Placeholder patterns that should never appear in image URLs
    bad_img_patterns = ["lazy-loader", "placeholder", "no-image", "noimage", "coming-soon", "default.jpg", "default.png"]

    image_hosts = defaultdict(int)
    issues_by_type = defaultdict(list)

    required_fields = ["id", "magazin", "titlu", "product_url"]
    img_keys = ["image", "imagine_url", "image_url"]

    for d in deals:
        did = d.get("id", "<no-id>")
        magazin = d.get("magazin") or d.get("store") or "?"

        # Required fields
        for f in required_fields:
            if not d.get(f):
                issues_by_type[f"missing:{f}"].append(did)

        # Image URL
        img = ""
        for k in img_keys:
            if d.get(k):
                img = d[k]; break
        if not img:
            issues_by_type["missing:image"].append(did)
        else:
            # Bad pattern?
            low = img.lower()
            for bad in bad_img_patterns:
                if bad in low:
                    issues_by_type[f"img_placeholder:{bad}"].append(did)
                    break
            # Whitelist?
            m = re.match(r"https?://([^/]+)/", img)
            if m:
                host = m.group(1)
                image_hosts[host] += 1
                if not host_matches(host, whitelist):
                    issues_by_type[f"img_host_not_whitelisted:{host}"].append(did)

        # Prices
        p_vat = d.get("pret_original")
        p_disc = d.get("pret_redus")
        try:
            pv = float(p_vat) if p_vat is not None else 0
            pd = float(p_disc) if p_disc is not None else 0
        except (TypeError, ValueError):
            pv = pd = 0
        if pv <= 0:
            issues_by_type["price_zero"].append(did)
        elif pd > 0 and pd >= pv:
            issues_by_type["price_no_discount"].append(did)

        # Link status
        ls = d.get("link_status")
        if ls and ls not in ("ok", "unchecked", None, ""):
            issues_by_type[f"link_status:{ls}"].append(did)

        # Title sanity: all-caps (likely raw scrape)
        t = d.get("titlu") or d.get("title") or ""
        if t and len(t) >= 5 and t == t.upper() and sum(c.isalpha() for c in t) > 3:
            issues_by_type["title_all_caps"].append(did)

        # In-stock flag but fake discount
        if d.get("is_fake_discount") and d.get("activ"):
            issues_by_type["fake_discount_active"].append(did)

    # Classify severity
    for k, items in issues_by_type.items():
        n = len(items)
        if n == 0: continue
        if k.startswith("img_host_not_whitelisted") or k.startswith("img_placeholder"):
            errors.append((k, n, items[:5]))
        elif k.startswith("missing:") or k in ("price_zero", "title_all_caps"):
            errors.append((k, n, items[:5]))
        else:
            warnings.append((k, n, items[:5]))

    # Report
    print("=" * 60)
    print("DATA AUDIT — ghidulreducerilor.ro")
    print("=" * 60)
    print(f"total deals:          {stats['total_deals']}")
    print(f"whitelisted hosts:    {stats['whitelisted_hosts']}")
    print(f"unique image hosts:   {len(image_hosts)}")
    print()

    if errors:
        print(f"[ERR] ERRORS ({sum(n for _,n,_ in errors)} issues, {len(errors)} types):")
        for k, n, samples in sorted(errors, key=lambda x: -x[1]):
            print(f"  [{n:>4}] {k}")
            for s in samples: print(f"        -> {s}")
    else:
        print("[OK] no errors")

    print()
    if warnings:
        print(f"[WARN] WARNINGS ({sum(n for _,n,_ in warnings)} issues, {len(warnings)} types):")
        for k, n, samples in sorted(warnings, key=lambda x: -x[1]):
            print(f"  [{n:>4}] {k}")
            for s in samples: print(f"        -> {s}")
    else:
        print("[OK] no warnings")

    print()
    print("image hosts summary:")
    for h, c in sorted(image_hosts.items(), key=lambda x: -x[1]):
        ok = "[ok]" if host_matches(h, whitelist) else "[NO]"
        print(f"  {ok} {c:>4}  {h}")

    # Exit code
    if errors:
        print("\n=> exit 2 (ERRORS, deploy should be blocked)"); sys.exit(2)
    if warnings:
        print("\n=> exit 1 (WARNINGS, non-blocking)"); sys.exit(1)
    print("\n=> exit 0 (CLEAN)"); sys.exit(0)

if __name__ == "__main__":
    main()
