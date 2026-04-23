"""CLI to run one or more merchant agents.

Usage:
  python agents/merchants/run.py streamstore --fix-images
  python agents/merchants/run.py all --fix-images

Writes changes to data/deals.json and a run summary to logs/agents-{date}.log.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent.parent
DEALS = BASE / "data" / "deals.json"
LOGS = BASE / "logs"
LOGS.mkdir(exist_ok=True)

# Registry of agents (add new ones here)
def get_registry():
    from . import streamstore
    return {
        "streamstore": streamstore.StreamStoreAgent(),
        # placeholders for next agents:
        # "vegis": vegis.VegisAgent(),
        # "hiris": hiris.HirisAgent(),
        # "alecoair": alecoair.AlecoAirAgent(),
        # "hotpick": hotpick.HotpickAgent(),
        # "mathaus": mathaus.MathausAgent(),   # Playwright
    }


def run_agent(agent, deals: list[dict], mode: str) -> dict:
    start = time.time()
    result = {
        "magazin": agent.slug,
        "deals_added": 0, "images_fixed": 0,
        "deals_disabled": 0, "errors": []
    }
    if mode == "fix-images":
        # Find broken: image is HTTP 404 or empty or on un-whitelisted host
        # For streamstore, "broken" = current image is profitsmart.ro or gomagcdn 404
        broken = [d for d in deals if d.get("magazin") == agent.slug
                  and ("profitsmart.ro" in (d.get("image") or "")
                       or not d.get("image"))]
        if not broken:
            result["note"] = "no broken images for this merchant"
        else:
            fixes = agent.fix_broken_images(broken)
            now = now_iso_fn()
            for d in deals:
                if d.get("id") in fixes:
                    new_img = fixes[d["id"]]
                    d["image"] = new_img
                    d["imagine_url"] = new_img
                    d["image_fixed_at"] = now
                    d["image_fix_source"] = f"agent:{agent.slug}"
                    result["images_fixed"] += 1
    result["duration_s"] = round(time.time() - start, 1)
    return result


def now_iso_fn() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    args = sys.argv[1:] or ["--help"]
    if args[0] in ("--help", "-h"):
        print(__doc__); return
    target = args[0]
    mode = "fix-images" if "--fix-images" in args else "fetch"

    with open(DEALS, encoding="utf-8") as f:
        deals = json.load(f)

    registry = get_registry()
    if target == "all":
        to_run = list(registry.values())
    elif target in registry:
        to_run = [registry[target]]
    else:
        print(f"Unknown agent: {target}. Available: {', '.join(registry)}")
        sys.exit(1)

    print(f"running {len(to_run)} agent(s) in mode={mode}")
    results = []
    for ag in to_run:
        r = run_agent(ag, deals, mode)
        results.append(r)
        print(f"  [{r['magazin']}] img_fixed={r['images_fixed']} err={len(r['errors'])} ({r['duration_s']}s)")

    with open(DEALS, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)

    log_file = LOGS / f"agents-{datetime.utcnow().strftime('%Y-%m-%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps({"ts": now_iso_fn(), **r}, ensure_ascii=False) + "\n")
    print(f"log: {log_file}")


if __name__ == "__main__":
    main()
