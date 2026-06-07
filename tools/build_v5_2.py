#!/usr/bin/env python3
"""build_v5_2.py — v5.2: FTC affiliate disclosure
Source: daddy-duty-v5_1.html -> daddy-duty-v5_2.html
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
SUPABASE_URL     = env.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = env.get('SUPABASE_ANON_KEY', '')

src = open('daddy-duty-v5_1.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials (always regex) ─────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version: v5.1 → v5.2 ──────────────────────────────────────────────────
OLD2a = "v5.1 \xb7 cloud sync"
NEW2a = "v5.2 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:\x27v5.1\x27"
NEW2b = "appVersion:\x27v5.2\x27"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.1 → v5.2')

# ── 3. Disclosure banner inside Product Ideas modal ──────────────────────────
OLD3 = (
    "<div style=\"overflow-y:auto;flex-grow:1;padding:0 20px 20px;\">\n"
    "    <div id=\"ideas-content\"></div>"
)
NEW3 = (
    "<div style=\"overflow-y:auto;flex-grow:1;padding:0 20px 20px;\">\n"
    "    <div style=\"font-size:11px;color:var(--ink-muted);padding:10px 12px;background:var(--cream-deep);border-radius:var(--r-sm);margin-bottom:14px;line-height:1.5;\">\n"
    "      Some links in this section may be affiliate links. As an Amazon Associate, we earn from qualifying purchases — at no extra cost to you. This never influences our recommendations.\n"
    "    </div>\n"
    "    <div id=\"ideas-content\"></div>"
)
assert OLD3 in src, "ideas-modal anchor not found"
src = src.replace(OLD3, NEW3, 1)
print('  - Affiliate disclosure banner added to Product Ideas modal')

# ── 4. Disclosure note in Budget module header ───────────────────────────────
OLD4 = "<p>25 categories. Real 2026 pricing. Your journey costs first, then baby gear by category. Tier ballparks for every item — enter your own price or tap one to set it.</p>"
NEW4 = (
    OLD4 + "\n"
    "        <p style=\"font-size:11px;color:var(--ink-muted);margin-top:6px;\">Product recommendations may include affiliate links. As an Amazon Associate, we earn from qualifying purchases at no extra cost to you.</p>"
)
assert OLD4 in src, "budget header anchor not found"
src = src.replace(OLD4, NEW4, 1)
print('  - Affiliate disclosure note added to Budget module header')

# ── 5. Disclosure note in Shopping List module header ────────────────────────
OLD5 = "<p>Essential \xb7 Helpful \xb7 Luxury. Tap a filter to narrow by what matters to you.</p>"
NEW5 = (
    OLD5 + "\n"
    "        <p style=\"font-size:11px;color:var(--ink-muted);margin-top:6px;\">Some product links may be affiliate links. As an Amazon Associate, we earn from qualifying purchases at no extra cost to you.</p>"
)
assert OLD5 in src, "shopping header anchor not found"
src = src.replace(OLD5, NEW5, 1)
print('  - Affiliate disclosure note added to Shopping List module header')

# ── 6. Affiliate Links section in Privacy Policy modal ───────────────────────
OLD6 = (
    "<p style=\"font-size:12px;color:var(--ink-muted);\">Questions? <strong>granthansell@gmail.com</strong></p>\n"
    "    </div>\n"
    "  </div>"
)
NEW6 = (
    "<p style=\"font-size:12px;color:var(--ink-muted);\">Questions? <strong>granthansell@gmail.com</strong></p>\n"
    "    </div>\n"
    "    <div class=\"privacy-section\" style=\"border-top:1px solid var(--rule);padding-top:20px;\">\n"
    "      <h4>Affiliate Links</h4>\n"
    "      <ul>\n"
    "        <li><strong>What this means.</strong> Some product links in the Budget and Shopping modules are affiliate links. If you click a link and make a purchase, we may earn a small commission at no additional cost to you.</li>\n"
    "        <li><strong>Amazon.</strong> As an Amazon Associate, we earn from qualifying purchases.</li>\n"
    "        <li><strong>Our recommendations are independent.</strong> Affiliate relationships do not influence which products appear or how they are described. Recommendations reflect genuine research and editorial judgment.</li>\n"
    "        <li><strong>You can opt out.</strong> You are never required to use affiliate links. You can search for any recommended product directly.</li>\n"
    "      </ul>\n"
    "    </div>\n"
    "  </div>\n"
    "</div>"
)
assert OLD6 in src, "privacy policy anchor not found"
src = src.replace(OLD6, NEW6, 1)
print('  - Affiliate Links section added to Privacy Policy modal')

# ── Write output ──────────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_2.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"const CACHE_NAME = 'daddy-duty-[^']*'",
                "const CACHE_NAME = 'daddy-duty-v5-2'", sw_src)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── JS syntax check ───────────────────────────────────────────────────────────
node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_2.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_2.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── Sanity assertions ─────────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.2 \xb7 cloud sync" in content, "version string missing"
assert "appVersion:\x27v5.2\x27" in content, "appVersion missing"
assert "As an Amazon Associate, we earn from qualifying purchases" in content, "Amazon Associate phrase missing"
assert content.count("As an Amazon Associate") == 4, "expected 4 Amazon Associate disclosures"
assert "Affiliate Links" in content, "Affiliate Links privacy section missing"
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_2.html')
