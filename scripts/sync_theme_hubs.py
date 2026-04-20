#!/usr/bin/env python3
"""
Sync Theme Hubs Script
Reads data/deals.json and data/stores.json, then auto-updates lib/theme-hubs.ts
to populate storeSlugs arrays for each hub based on which stores have active deals
in that hub's dealCategories.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

# Base directory
BASE_DIR = Path(__file__).parent.parent

def load_json_file(filepath: str):
    """Load JSON file with UTF-8 BOM handling."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def main():
    print("[*] Loading data files...")
    
    # Load stores and deals
    stores = load_json_file(str(BASE_DIR / 'data' / 'stores.json'))
    deals = load_json_file(str(BASE_DIR / 'data' / 'deals.json'))
    
    print(f"[*] Loaded {len(stores)} stores and {len(deals)} deals")
    
    # Create store slug -> categorie mapping
    store_categories: Dict[str, str] = {}
    for store in stores:
        store_categories[store['slug']] = store['categorie_principala']
    
    # Create hub categorie -> stores mapping
    # Group active deals by categorie, then map stores to hubs
    deals_by_category: Dict[str, Set[str]] = {}
    for deal in deals:
        if deal.get('activ') or deal.get('is_active'):
            category = deal.get('categorie') or deal.get('categories', [None])[0]
            if category:
                if category not in deals_by_category:
                    deals_by_category[category] = set()
                store_slug = deal.get('magazin') or deal.get('store')
                if store_slug:
                    deals_by_category[category].add(store_slug)
    
    print(f"[*] Found {len(deals_by_category)} deal categories")
    for cat, stores_in_cat in sorted(deals_by_category.items()):
        print(f"    - {cat}: {', '.join(sorted(stores_in_cat))}")
    
    # Read existing lib/theme-hubs.ts
    theme_hubs_path = BASE_DIR / 'lib' / 'theme-hubs.ts'
    with open(str(theme_hubs_path), 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n[*] Reading {theme_hubs_path}")
    
    # Parse THEME_HUBS array - find each hub object and update storeSlugs
    # Pattern: matches entire hub object { ... }, then updates storeSlugs: [...]
    
    # First, extract all hub objects to understand structure
    # We'll use regex to find each hub and its dealCategories, then compute storeSlugs
    
    # Find all hub entries: looking for pattern like:
    # { slug: 'fashion', ... dealCategories: [...], storeSlugs: [...], ... }
    
    def extract_hub_config(match_text: str) -> tuple:
        """Extract slug and dealCategories from hub object text."""
        slug_match = re.search(r"slug:\s*['\"]([^'\"]+)['\"]", match_text)
        slug = slug_match.group(1) if slug_match else None
        
        # Extract dealCategories array
        categories_match = re.search(r"dealCategories:\s*\[([^\]]*)\]", match_text)
        categories = []
        if categories_match:
            cat_str = categories_match.group(1)
            categories = re.findall(r"['\"]([^'\"]+)['\"]", cat_str)
        
        return slug, categories
    
    # Find all hub objects
    hub_pattern = r"\{[^{}]*?slug:\s*['\"][^'\"]+['\"][^{}]*?tips:\s*\[[^\]]*\][^{}]*?\}"
    
    # Strategy: Process the file by finding each hub and updating its storeSlugs
    # We'll do multiple passes to ensure we catch all hubs correctly
    
    updated_content = content
    
    # Process each existing hub
    hubs_to_update = []
    hub_objects = re.finditer(
        r"\{\s*slug:\s*['\"]([^'\"]+)['\"][^}]*?dealCategories:\s*\[([^\]]*)\][^}]*?\}",
        content,
        re.DOTALL
    )
    
    for hub_match in hub_objects:
        slug = hub_match.group(1)
        categories_str = hub_match.group(2)
        categories = re.findall(r"['\"]([^'\"]+)['\"]", categories_str)
        
        print(f"\n[*] Processing hub '{slug}' with dealCategories: {categories}")
        
        # Find which stores have deals in these categories
        hub_stores = set()
        for category in categories:
            if category in deals_by_category:
                hub_stores.update(deals_by_category[category])
        
        print(f"    -> Found stores with deals: {sorted(hub_stores)}")
        hubs_to_update.append((slug, categories, sorted(hub_stores)))
    
    # Now update storeSlugs for each hub
    for slug, categories, store_slugs in hubs_to_update:
        # Find the hub object and update its storeSlugs array
        # Pattern: find hub with this slug, locate storeSlugs: [...], replace it
        
        pattern = rf"(slug:\s*['\"]" + re.escape(slug) + r"['\"][^}}]*?storeSlugs:\s*\[)[^\]]*?(\])"
        
        new_slugs_array = ", ".join([f"'{s}'" for s in store_slugs])
        replacement = rf"\1{new_slugs_array}\2"
        
        updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL)
        print(f"    -> Updated storeSlugs to: [{new_slugs_array}]")
    
    # Write updated content
    with open(str(theme_hubs_path), 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"\n[+] Successfully updated {theme_hubs_path}")
    print("[+] Done!")

if __name__ == '__main__':
    main()
