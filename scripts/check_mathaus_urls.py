import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

data = json.loads((Path(r'C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO') / 'data' / 'deals.json').read_text(encoding='utf-8'))
cdn = [d for d in data if d.get('magazin')=='mathaus' and 'cdn.mathaus.ro' in d.get('imagine_url','')]
print(f'Ramas de reparat: {len(cdn)}')
print()
for d in cdn[:5]:
    print('ID:', d['id'][:60])
    print('  product_url:', (d.get('product_url') or 'N/A')[:80])
    print('  link_afiliat:', (d.get('link_afiliat') or 'N/A')[:80])
    print('  imagine_url:', (d.get('imagine_url') or 'N/A')[:80])
    print()
