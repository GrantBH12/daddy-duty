#!/usr/bin/env python3
"""build_v5_7.py — v5.7: Replace window.confirm() in deleteAccount() with undo-toast pattern
Source: daddy-duty-v5_6.html -> daddy-duty-v5_7.html

Changes:
  1. deleteAccount(): replace window.confirm() with delayed-execution undo-toast
     (5s countdown; clicking Undo cancels the deletion)
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

src = open('daddy-duty-v5_6.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials (always regex) ─────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version ─────────────────────────────────────────────────────────────────
OLD2a = "v5.6 \xb7 cloud sync"
NEW2a = "v5.7 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:'v5.6'"
NEW2b = "appVersion:'v5.7'"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.6 → v5.7')

# ── 3. Replace window.confirm() in deleteAccount() with undo-toast pattern ────
OLD3 = """async function deleteAccount() {
  if (!confirm('This will permanently delete all your cloud data and sign you out. Local data on this device will also be cleared. This cannot be undone. Continue?')) return;
  showToast('Deleting your data...');
  const sb = getSB();
  if (sb && _authUser) {
    try {
      await sb.from('user_app_data').delete().eq('user_id', _authUser.id);
    } catch(e) { console.error('Delete data error:', e); }
    try {
      await sb.auth.signOut();
    } catch(e) { console.error('Sign out error:', e); }
  }
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem('firstdad.snapshots');
  localStorage.removeItem(LEGACY_KEY_V22);
  window.location.reload();
}"""
NEW3 = """function deleteAccount() {
  let cancelled = false;
  showToast('Account will be deleted — click Undo to cancel', () => { cancelled = true; });
  setTimeout(async () => {
    if (cancelled) return;
    const sb = getSB();
    if (sb && _authUser) {
      try { await sb.from('user_app_data').delete().eq('user_id', _authUser.id); } catch(e) { console.error('Delete data error:', e); }
      try { await sb.auth.signOut(); } catch(e) { console.error('Sign out error:', e); }
    }
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem('firstdad.snapshots');
    localStorage.removeItem(LEGACY_KEY_V22);
    window.location.reload();
  }, 5000);
}"""
assert OLD3 in src, "deleteAccount() with confirm() not found"
src = src.replace(OLD3, NEW3, 1)
print('  - deleteAccount(): window.confirm() replaced with undo-toast (5s delay)')

# ── 4. Write output ────────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_7.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"const CACHE_NAME = 'daddy-duty-[^']*'",
                "const CACHE_NAME = 'daddy-duty-v5-7'", sw_src)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── 5. JS syntax check ───────────────────────────────────────────────────────
node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_7.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_7.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── 6. Sanity assertions ─────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.7 \xb7 cloud sync"          in content, "version string missing"
assert "appVersion:'v5.7'"             in content, "appVersion missing"
assert "window.confirm("           not in content, "window.confirm() still present"
assert "cancelled = true"              in content, "undo-toast cancel not found"
assert "deleteAccount"                 in content, "deleteAccount function missing"
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_7.html')
