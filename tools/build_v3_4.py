#!/usr/bin/env python3
"""Build v3.4: Fix journal nudge — clicking it opens write view with today's prompt pre-filled"""
import re, subprocess, os, shutil, json

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

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠  SUPABASE_URL or SUPABASE_ANON_KEY not set in .env — aborting")
    raise SystemExit(1)

src = open('daddy-duty-v3_3.html', encoding='utf-8').read()

# ── 1. Inject credentials via regex ───────────────────────────────────────
src = re.sub(
    r"const SUPABASE_URL\s*=\s*'[^']*'",
    f"const SUPABASE_URL      = '{SUPABASE_URL}'",
    src, count=1
)
src = re.sub(
    r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
    f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'",
    src, count=1
)

# ── 2. Version bumps ───────────────────────────────────────────────────────
OLD_VERSION_META = "v3.3 · cloud sync"
NEW_VERSION_META = "v3.4 · cloud sync"
assert OLD_VERSION_META in src, f"Not found: {repr(OLD_VERSION_META)}"
src = src.replace(OLD_VERSION_META, NEW_VERSION_META, 1)

OLD_APP_VERSION = "appVersion:'v3.3'"
NEW_APP_VERSION = "appVersion:'v3.4'"
assert OLD_APP_VERSION in src, f"Not found: {repr(OLD_APP_VERSION)}"
src = src.replace(OLD_APP_VERSION, NEW_APP_VERSION, 1)

# ── 3. Fix journal nudge onclick ──────────────────────────────────────────
# The nudge previously called go('journal'), which always resets jView='list',
# so the prompt shown in the nudge was never carried into the write view.
# New function openJournalPrompt() mirrors reflectInJournal() but pre-fills
# jDraft.promptText with today's rotating prompt before rendering.
OLD_NUDGE_ONCLICK = '    wrap.innerHTML = `<div class="nudge" onclick="go(\'journal\')">'
NEW_NUDGE_ONCLICK = '    wrap.innerHTML = `<div class="nudge" onclick="openJournalPrompt()">'
assert OLD_NUDGE_ONCLICK in src, f"nudge onclick not found"
src = src.replace(OLD_NUDGE_ONCLICK, NEW_NUDGE_ONCLICK, 1)

# ── 4. Add openJournalPrompt() after reflectInJournal() ───────────────────
OLD_REFLECT = """function reflectInJournal(){
  go('journal');
  jDraft={body:'',isLetter:false,promptText:'',showPrompts:false,editingId:null};
  jView='write';
  renderJournal();
  updateJournalHeader();
}"""
NEW_REFLECT = """function reflectInJournal(){
  go('journal');
  jDraft={body:'',isLetter:false,promptText:'',showPrompts:false,editingId:null};
  jView='write';
  renderJournal();
  updateJournalHeader();
}
function openJournalPrompt(){
  const prompt=JOURNAL_PROMPTS_SHORT[Math.floor(Date.now()/86400000)%JOURNAL_PROMPTS_SHORT.length];
  go('journal');
  jDraft={body:'',isLetter:false,promptText:prompt,showPrompts:false,editingId:null};
  jView='write';
  renderJournal();
  updateJournalHeader();
}"""
assert OLD_REFLECT in src, "reflectInJournal not found"
src = src.replace(OLD_REFLECT, NEW_REFLECT, 1)

# ── Fix manifest href to relative path (GitHub Pages subpath-safe) ─────────
src = src.replace(
    '<link rel="manifest" href="/manifest.json"/>',
    '<link rel="manifest" href="manifest.json"/>'
)

# ── Write output ───────────────────────────────────────────────────────────
with open('daddy-duty-v3_4.html', 'w', encoding='utf-8') as f:
    f.write(src)

os.makedirs('docs', exist_ok=True)
shutil.copy('daddy-duty-v3_4.html', 'docs/index.html')

os.makedirs('docs/brand', exist_ok=True)
for logo in ['logo.svg', 'logo-cream.svg', 'logo-mono.svg', 'logo-favicon.svg']:
    src_path = f'brand/assets/{logo}'
    if os.path.exists(src_path):
        shutil.copy(src_path, f'docs/brand/{logo}')

manifest = {
    "name": "Daddy Duty", "short_name": "Daddy Duty",
    "description": "Your personal guide to becoming a father",
    "start_url": "./", "display": "standalone",
    "background_color": "#f5ede0", "theme_color": "#c97156", "icons": []
}
with open('docs/manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

# ── Verify ─────────────────────────────────────────────────────────────────
content = open('daddy-duty-v3_4.html', encoding='utf-8').read()
scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', content, re.DOTALL)
with open('/tmp/check_v3_4.js', 'w') as f:
    f.write(scripts[0])
result = subprocess.run(['node', '--check', '/tmp/check_v3_4.js'], capture_output=True, text=True)
assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"

assert f"'{SUPABASE_URL}'" in content, "URL not injected"
assert f"'{SUPABASE_ANON_KEY}'" in content, "Anon key not injected"
assert "v3.4" in content, "version not updated"
assert "openJournalPrompt" in content, "openJournalPrompt function missing"
assert 'onclick="openJournalPrompt()"' in content, "nudge onclick not updated"
assert 'href="manifest.json"' in content, "manifest href not relative"

print("✓ daddy-duty-v3_4.html written, JS syntax clean")
print(f"  - URL: {SUPABASE_URL}")
print(f"  - Key: {SUPABASE_ANON_KEY[:8]}... (eyJ: {SUPABASE_ANON_KEY.startswith('eyJ')})")
print("  - Version: v3.4")
print("  - Fix: journal nudge now opens write view with today's prompt pre-filled")

# ── Deploy ─────────────────────────────────────────────────────────────────
print("\nPushing to GitHub Pages...")
subprocess.run(['git', 'add', 'docs/'], check=True)
commit = subprocess.run(['git', 'commit', '-m', 'deploy: v3.4'], capture_output=True, text=True)
if commit.returncode == 0:
    push = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    if push.returncode == 0:
        print("✓ Pushed — https://GrantBH12.github.io/daddy-duty")
    else:
        print(f"⚠  Push failed:\n{push.stderr}")
elif 'nothing to commit' in commit.stdout or 'nothing to commit' in commit.stderr:
    print("⚠  Nothing to commit — docs/ unchanged")
else:
    print(f"⚠  Commit failed:\n{commit.stderr}")
