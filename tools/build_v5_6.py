#!/usr/bin/env python3
"""build_v5_6.py — v5.6: Remove My Stuff module tile, rename to Important Things
Source: daddy-duty-v5_5.html -> daddy-duty-v5_6.html

Changes:
  1. Remove My Stuff from the 7-module Parenthood Toolkit grid (→ 6 modules)
  2. Add "Important Things" icon button in topbar (before gear icon)
  3. Add "Important Things" nav row in Settings modal
  4. Rename all user-visible "My Stuff" labels → "Important Things"
  5. Add CSS for settings-nav-row
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

src = open('daddy-duty-v5_5.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials (always regex) ─────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version ─────────────────────────────────────────────────────────────────
OLD2a = "v5.5 \xb7 cloud sync"
NEW2a = "v5.6 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:'v5.5'"
NEW2b = "appVersion:'v5.6'"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.5 → v5.6')

# ── 3. Remove My Stuff module tile from Parenthood Toolkit grid ────────────────
OLD3 = """\n      <div class="module" data-mod="mystuff" onclick="go('mystuff')">
        <div class="module-icon"><svg viewBox="0 0 24 24" width="22" height="22"><use href="#dd-mod-mystuff"></use></svg></div>
        <h3>My Stuff</h3>
        <p>Every link, contact, and document in one place. Attachable to any task. One shelf for all of it.</p>
        <div class="module-footer">
          <span class="module-progress" id="mystuff-progress"><strong>0</strong> items</span>
          <span class="module-arrow">Open →</span>
        </div>
      </div>"""
NEW3 = ''
assert OLD3 in src, "My Stuff module tile not found"
src = src.replace(OLD3, NEW3, 1)
print('  - HTML: My Stuff module tile removed (7 → 6 modules)')

# ── 4. Add Important Things icon button in topbar (before gear button) ─────────
OLD4 = '    <button class="gear-btn" id="settingsBtn" onclick="openSettings()" title="Settings" aria-label="Settings"><svg class="icon md" aria-hidden="true"><use href="#dd-sliders"></use></svg></button>'
NEW4 = ('    <button class="gear-btn" onclick="go(\'mystuff\')" title="Important Things" aria-label="Important Things">'
        '<svg class="icon md" aria-hidden="true"><use href="#dd-mod-mystuff"></use></svg></button>\n'
        '    <button class="gear-btn" id="settingsBtn" onclick="openSettings()" title="Settings" aria-label="Settings">'
        '<svg class="icon md" aria-hidden="true"><use href="#dd-sliders"></use></svg></button>')
assert OLD4 in src, "gear-btn not found in topbar"
src = src.replace(OLD4, NEW4, 1)
print('  - HTML: Important Things topbar button added')

# ── 5. Add CSS for settings-nav-row + settings-nav-sub ────────────────────────
# Insert before the closing </style> of the main style block (before the link tag)
OLD5 = '</style>\n<link rel="icon"'
NEW5 = """.settings-nav-row{display:flex;align-items:center;gap:10px;width:100%;background:var(--cream-deep);border:1px solid var(--rule);border-radius:var(--r-md);padding:12px 14px;cursor:pointer;font-size:14px;font-family:inherit;color:var(--ink);transition:background var(--dur-fast);}
.settings-nav-row:hover{background:var(--cream-deeper);}
.settings-nav-sub{flex:1;text-align:left;font-size:12px;color:var(--ink-muted);}
</style>
<link rel="icon\""""
assert OLD5 in src, "CSS insertion anchor not found"
src = src.replace(OLD5, NEW5, 1)
print('  - CSS: settings-nav-row styles added')

# ── 6. Add Important Things nav row in Settings modal ─────────────────────────
# Insert as a new section between "Profile" section and "Journey" section
OLD6 = '    <div class="settings-section" id="settings-journey-section">'
NEW6 = """\
    <div class="settings-section">
      <div class="settings-section-label">Quick access</div>
      <button class="settings-nav-row" onclick="closeSettings(); go('mystuff')">
        <svg class="icon sm" aria-hidden="true"><use href="#dd-mod-mystuff"></use></svg>
        <span>Important Things</span>
        <span class="settings-nav-sub">Links, contacts &amp; documents</span>
        <svg class="icon sm" aria-hidden="true"><use href="#dd-arrow-right"></use></svg>
      </button>
    </div>

    <div class="settings-section" id="settings-journey-section">"""
assert OLD6 in src, "settings journey section anchor not found"
src = src.replace(OLD6, NEW6, 1)
print('  - HTML: Important Things nav row added to Settings modal')

# ── 7. Rename user-visible "My Stuff" labels → "Important Things" ──────────────

# 7a. Screen h1
OLD7a = '        <h1>My <em>Stuff</em></h1>'
NEW7a = '        <h1>Important <em>Things</em></h1>'
assert OLD7a in src, "mystuff screen h1 not found"
src = src.replace(OLD7a, NEW7a, 1)

# 7b. Screen tagline
OLD7b = '        <p>Your shelf. Every link, contact, and document in one place. Add them here or attach them to any task. Edits propagate everywhere they\'re referenced.</p>'
NEW7c = '        <p>Your key resources — links, contacts, and documents. Add them here or attach them to any task.</p>'
assert OLD7b in src, "mystuff screen tagline not found"
src = src.replace(OLD7b, NEW7c, 1)

# 7c. Static picker divider (HTML)
OLD7d = '  <div class="picker-divider" id="picker-divider-text">Or pick from My Stuff</div>'
NEW7d = '  <div class="picker-divider" id="picker-divider-text">Or pick from Important Things</div>'
assert OLD7d in src, "picker divider static HTML not found"
src = src.replace(OLD7d, NEW7d, 1)

# 7d. Task expanded section label
OLD7e = '<div class="task-expanded-label">My Stuff — attached to this task</div>'
NEW7e = '<div class="task-expanded-label">Important Things — attached to this task</div>'
assert OLD7e in src, "task expanded label not found"
src = src.replace(OLD7e, NEW7e, 1)

# 7e. Missing attachment warning
OLD7f = 'Missing — removed from My Stuff'
NEW7f = 'Missing — removed from Important Things'
assert OLD7f in src, "missing attachment warning not found"
src = src.replace(OLD7f, NEW7f, 1)

# 7f. Picker empty state
OLD7g = "Nothing in My Stuff yet. Create the first one above."
NEW7g = "Nothing in Important Things yet. Create the first one above."
assert OLD7g in src, "picker empty state not found"
src = src.replace(OLD7g, NEW7g, 1)

# 7g. Picker all-attached state
OLD7h = "Every ${type} in My Stuff is already on this task."
NEW7h = "Every ${type} in Important Things is already on this task."
assert OLD7h in src, "picker all-attached state not found"
src = src.replace(OLD7h, NEW7h, 1)

# 7h. Dynamic picker divider (JS)
OLD7i = "Or pick from My Stuff (${avail.length})"
NEW7i = "Or pick from Important Things (${avail.length})"
assert OLD7i in src, "dynamic picker divider JS not found"
src = src.replace(OLD7i, NEW7i, 1)

print('  - Labels: "My Stuff" → "Important Things" (8 occurrences)')

# ── 8. Auth-screen links → standalone privacy.html ────────────────────────────
OLD8a = '''    <div class="auth-links">
      <button class="auth-link-btn" onclick="showPrivacy()">Privacy Policy</button>
      <span style="color:var(--ink-muted);font-size:11px;">&middot;</span>
      <button class="auth-link-btn" onclick="showPrivacy()">Terms of Use</button>
    </div>'''
NEW8a = '''    <div class="auth-links">
      <a class="auth-link-btn" href="./privacy.html" target="_blank" rel="noopener">Privacy Policy</a>
      <span style="color:var(--ink-muted);font-size:11px;">&middot;</span>
      <a class="auth-link-btn" href="./privacy.html" target="_blank" rel="noopener">Terms of Use</a>
    </div>'''
assert OLD8a in src, "auth-screen privacy/terms buttons not found"
src = src.replace(OLD8a, NEW8a, 1)
print('  - Auth links: Privacy Policy + Terms of Use → ./privacy.html')

# ── 9. Write output ────────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_6.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"const CACHE_NAME = 'daddy-duty-[^']*'",
                "const CACHE_NAME = 'daddy-duty-v5-6'", sw_src)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── 10. JS syntax check ───────────────────────────────────────────────────────
node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_6.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_6.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── 11. Sanity assertions ─────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.6 \xb7 cloud sync"                    in content, "version string missing"
assert "appVersion:'v5.6'"                        in content, "appVersion missing"
assert '<div class="module" data-mod="mystuff"' not in content, "mystuff module tile still present"
assert 'id="mystuff-progress"'                not in content, "mystuff-progress tile still present"
assert 'Important <em>Things</em>'                in content, "Important Things h1 missing"
assert 'Important Things'                         in content, "Important Things label missing"
assert 'settings-nav-row'                         in content, "settings nav row missing"
assert 'Or pick from My Stuff'                not in content, "old picker divider still present"
assert 'My Stuff — attached'             not in content, "old task label still present"
assert 'section id="mystuff"'                     in content, "mystuff screen itself was removed (should stay)"
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_6.html')
