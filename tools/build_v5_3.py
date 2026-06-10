#!/usr/bin/env python3
"""build_v5_3.py — v5.3: Connect shopping list to product discovery
Source: daddy-duty-v5_2.html -> daddy-duty-v5_3.html

Changes:
  1. getBudgetCatForShopItem() helper — reverse lookup from shopping item ID to budget category
  2. Shopping item cards show "↗ Product options" link + "budgeted $X" badge for items with budget data
  3. Product Ideas modal gains a "Mark bought / Unmark" toggle tied to shopping state
  4. "Product ideas" renamed "Product options" in budget expand footer for label parity
"""

import os, re, shutil, subprocess, sys
sys.stdout.reconfigure(line_buffering=True)

def load_env(path='.env'):
    env = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env

env = load_env()
SUPABASE_URL      = env.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = env.get('SUPABASE_ANON_KEY', '')

src = open('daddy-duty-v5_2.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials (always regex) ─────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version: v5.2 → v5.3 ──────────────────────────────────────────────────
OLD2a = "v5.2 \xb7 cloud sync"
NEW2a = "v5.3 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:'v5.2'"
NEW2b = "appVersion:'v5.3'"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.2 → v5.3')

# ── 3. Add getBudgetCatForShopItem helper after getShoppingStatus ─────────────
OLD3 = "function getShoppingStatus(cat){if(!cat.shoppingMatch)return null;return(state.shopping[cat.shoppingMatch]||{}).bought||false;}"
NEW3 = (OLD3 + "\n"
        "function getBudgetCatForShopItem(shId){return BUDGET_CATS.find(c=>c.shoppingMatch===shId)||null;}")
assert OLD3 in src, "getShoppingStatus not found"
src = src.replace(OLD3, NEW3, 1)
print('  - getBudgetCatForShopItem helper added')

# ── 4a. Shopping item render: add computed vars after linkHtml ────────────────
# Inserts the budget lookup + optionsHtml + budgetHint variables right after
# the existing linkHtml declaration, before the return template literal.
OLD4a = "    const linkHtml=item.link?`<a class=\"shop-item-link\" href=\"${item.link}\" target=\"_blank\" rel=\"noopener\">↗ View</a>`:'';"
NEW4a = (OLD4a + "\n"
         "    const _bc=!item.custom?getBudgetCatForShopItem(item.id):null;\n"
         "    const _bs=_bc?(state.budget[_bc.id]||{}):{};")
assert OLD4a in src, "linkHtml line not found"
src = src.replace(OLD4a, NEW4a, 1)
print('  - Shopping item: budget lookup vars added')

# ── 4b. Shopping item render: inject optionsHtml + budgetHint into meta div ──
# The meta div currently ends: ${tagHtml}\n          ${linkHtml}\n        </div>
OLD4b = "          ${tagHtml}\n          ${linkHtml}\n        </div>"
NEW4b = (
    "          ${tagHtml}\n"
    "          ${_bc&&_bs.price!=null?`<span class=\"shop-item-tag\" style=\"background:var(--sage-soft);color:var(--sage-deep);\">budgeted ${fmtMoney(_bs.price)}</span>`:''}\n"
    "          ${linkHtml}\n"
    "          ${_bc?`<button class=\"shop-item-link\" onclick=\"event.stopPropagation();openProductIdeas('${_bc.id}')\" style=\"background:none;border:none;padding:0;cursor:pointer;font:inherit;\">↗ Product options</button>`:''}\n"
    "        </div>"
)
assert OLD4b in src, "meta div tagHtml/linkHtml block not found"
src = src.replace(OLD4b, NEW4b, 1)
print('  - Shopping items: Product options link + budget hint badge added')

# ── 5. openProductIdeas: add shopping status footer inside modal ──────────────
OLD5 = ("  document.getElementById('ideas-content').innerHTML=html;\n"
        "  document.getElementById('ideas-backdrop').classList.add('open');\n"
        "  document.getElementById('ideas-modal').classList.add('open');")
NEW5 = (
    "  const _sm=cat.shoppingMatch;\n"
    "  const _shopBought=_sm?((state.shopping[_sm]||{}).bought||false):false;\n"
    "  const _shopFooter=_sm?`<div style=\"margin-top:16px;padding:12px 14px;border-top:1px solid var(--rule);display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:13px;\">"
    "<span style=\"color:var(--ink-muted);\">${_shopBought?`<span style=\"color:var(--sage-deep);\">\\u2713 Marked bought in shopping list</span>`:'Not yet marked bought in shopping list'}</span>"
    "<button onclick=\"toggleShoppingItem('${_sm}');openProductIdeas('${catId}')\" style=\"padding:5px 12px;border-radius:var(--r-sm);border:1px solid var(--cream-deeper);background:${_shopBought?'var(--sage-soft)':'transparent'};color:${_shopBought?'var(--sage-deep)':'var(--ink)'};font-size:12px;cursor:pointer;font-family:inherit;\">${_shopBought?'Unmark bought':'Mark bought'}</button>"
    "</div>`:''\n;"
    "  document.getElementById('ideas-content').innerHTML=html+_shopFooter;\n"
    "  document.getElementById('ideas-backdrop').classList.add('open');\n"
    "  document.getElementById('ideas-modal').classList.add('open');"
)
assert OLD5 in src, "openProductIdeas innerHTML line not found"
src = src.replace(OLD5, NEW5, 1)
print('  - Product Ideas modal: shopping status footer added')

# ── 6. Budget expand footer: "Product ideas" → "Product options" ─────────────
OLD6 = "↗ Product ideas</span>`"
NEW6 = "↗ Product options</span>`"
assert OLD6 in src, "Product ideas link in budget not found"
src = src.replace(OLD6, NEW6, 1)
print('  - Budget: "Product ideas" renamed to "Product options"')

# ── Write output ──────────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_3.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"const CACHE_NAME = 'daddy-duty-[^']*'",
                "const CACHE_NAME = 'daddy-duty-v5-3'", sw_src)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── JS syntax check ───────────────────────────────────────────────────────────
node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_3.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_3.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── Sanity assertions ─────────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.3 \xb7 cloud sync" in content, "version string missing"
assert "appVersion:'v5.3'" in content, "appVersion missing"
assert "getBudgetCatForShopItem" in content, "helper function missing"
assert "Product options" in content, "Product options label missing"
assert content.count("Product options") >= 2, "expected Product options in both shopping and budget"
assert "_sm" in content, "shopping status footer code missing"
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_3.html')
