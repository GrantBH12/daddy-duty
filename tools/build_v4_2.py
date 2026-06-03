#!/usr/bin/env python3
"""Build v4.2: Home screen hierarchy redesign — card promoted to primary hero,
daily question moved inside card, streak removed from topbar, countdown
demoted to compact widget, toolkit section renamed Parenthood Toolkit."""
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

src = open('daddy-duty-v4_1.html', encoding='utf-8').read()

# ── 1. Inject credentials ──────────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)

# ── 2. Version bump ────────────────────────────────────────────────────────
assert "v4.1 · cloud sync" in src
src = src.replace("v4.1 · cloud sync", "v4.2 · cloud sync", 1)
assert "appVersion:'v4.1'" in src
src = src.replace("appVersion:'v4.1'", "appVersion:'v4.2'", 1)
print("  - Version: v4.1 → v4.2")

# ── 3. Remove streak pill from topbar ─────────────────────────────────────
# Streak now lives inside the card (streak-strip); topbar only shows XP + sync
OLD_TOPBAR_STREAK = """    <span class="streak" id="topbar-streak">● no streak yet</span>
    <span class="xp" id="topbar-xp">★ 0 XP</span>"""
NEW_TOPBAR_STREAK = """    <span class="xp" id="topbar-xp">★ 0 XP</span>"""
assert OLD_TOPBAR_STREAK in src, "Topbar streak anchor not found"
src = src.replace(OLD_TOPBAR_STREAK, NEW_TOPBAR_STREAK, 1)
print("  - Topbar: streak pill removed")

# ── 4. Reorder home section — card first, question inside card, compact countdown ──
OLD_HOME_LAYOUT = """
    <div class="countdown">
      <div class="countdown-label">Estimated due date</div>
      <div class="countdown-num" id="countdown-num">—<span class="unit" id="countdown-unit">days to go</span></div>
      <div class="countdown-sub" id="countdown-sub">May 10, 2027 · your baby's first day</div>
      <div class="countdown-phase">
        <span class="phase-dot-hub"></span>
        <span>PHASE: PRE-TRANSFER · GESTATIONAL SURROGACY (US)</span>
      </div>
      <div class="phase-prog-wrap">
        <div class="phase-prog-header">
          <span class="phase-prog-title" id="phase-prog-title">Pre-transfer progress</span>
          <span class="phase-prog-label" id="phase-progress-label">— / —</span>
        </div>
        <div class="phase-prog-track">
          <div class="phase-prog-bar" id="phase-progress-bar"></div>
        </div>
      </div>
    </div>

    <div class="todays-card" id="home-card-wrap">
      <div class="todays-eyebrow" id="home-card-eyebrow">◉ Today's card</div>
      <h2 class="todays-title" id="home-card-title">Loading today's card…</h2>
      <p class="todays-body" id="home-card-body"></p>
      <div class="todays-actions">
        <button class="card-btn primary" id="mark-read-btn" onclick="markCardRead()">Mark as read · +10 XP</button>
        <button class="card-btn ghost" onclick="reflectInJournal()">Reflect in journal</button>
        <button class="card-btn ghost" onclick="go('library')">Full library</button>
      </div>
      <div class="streak-strip" id="streak-strip"></div>
    </div>

    <div id="home-nudge-wrap"></div>
    <div id="home-question-wrap"></div>
    <div class="hub-sectionhead"><h2>Your toolkit</h2></div>"""

NEW_HOME_LAYOUT = """
    <div class="todays-card" id="home-card-wrap">
      <div class="todays-eyebrow" id="home-card-eyebrow">◉ Today's card</div>
      <h2 class="todays-title" id="home-card-title">Loading today's card…</h2>
      <p class="todays-body" id="home-card-body"></p>
      <div id="home-question-wrap"></div>
      <div class="todays-actions">
        <button class="card-btn primary" id="mark-read-btn" onclick="markCardRead()">Mark as read · +10 XP</button>
        <button class="card-btn ghost" onclick="reflectInJournal()">Reflect in journal</button>
        <button class="card-btn ghost" onclick="go('library')">Full library</button>
      </div>
      <div class="streak-strip" id="streak-strip"></div>
    </div>

    <div id="home-nudge-wrap"></div>

    <div class="countdown-widget">
      <div class="cw-left">
        <div class="countdown-num" id="countdown-num">—<span class="unit" id="countdown-unit">days to go</span></div>
        <div class="countdown-sub" id="countdown-sub">May 10, 2027 · your baby's first day</div>
      </div>
      <div class="cw-right">
        <div class="countdown-phase">
          <span class="phase-dot-hub"></span>
          <span>PHASE: PRE-TRANSFER · GESTATIONAL SURROGACY (US)</span>
        </div>
        <div class="phase-prog-wrap">
          <div class="phase-prog-header">
            <span class="phase-prog-title" id="phase-prog-title">Pre-transfer progress</span>
            <span class="phase-prog-label" id="phase-progress-label">— / —</span>
          </div>
          <div class="phase-prog-track">
            <div class="phase-prog-bar" id="phase-progress-bar"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="hub-sectionhead"><h2>Parenthood Toolkit</h2></div>"""

assert OLD_HOME_LAYOUT in src, "Home layout anchor not found"
src = src.replace(OLD_HOME_LAYOUT, NEW_HOME_LAYOUT, 1)
print("  - Home: card promoted to top, question inside card, countdown widget, toolkit renamed")

# ── 5. Add CSS: countdown-widget + dark-card daily question overrides ──────
OLD_CSS_ANCHOR = """  .q-option-btn.skip-btn:hover { color:var(--ink); background:transparent; }

  /* library module tile badge */"""

NEW_CSS_ANCHOR = """  .q-option-btn.skip-btn:hover { color:var(--ink); background:transparent; }

  /* ── Countdown widget (compact secondary) ──────────────────────────────── */
  .countdown-widget { max-width:720px; margin:0 auto 40px; background:var(--cream-deep); border-radius:16px; padding:20px 26px; display:flex; align-items:center; gap:20px; border:1px solid var(--rule); }
  .cw-left { flex-shrink:0; padding-right:20px; border-right:1px solid var(--rule); }
  .cw-right { flex-grow:1; min-width:0; }
  .countdown-widget .countdown-num { font-size:40px; line-height:1; position:relative; }
  .countdown-widget .countdown-num .unit { font-size:13px; margin-left:4px; }
  .countdown-widget .countdown-sub { margin-top:4px; }
  .countdown-widget .countdown-phase { margin-top:0; margin-bottom:8px; }
  .countdown-widget .phase-prog-wrap { margin-top:0; }
  @media(max-width:560px){ .countdown-widget { flex-direction:column; align-items:stretch; } .cw-left { padding-right:0; border-right:none; border-bottom:1px solid var(--rule); padding-bottom:14px; } }

  /* ── Daily question inside today's card (dark background overrides) ─────── */
  .todays-card .daily-question { margin:0 0 22px; background:rgba(245,237,224,.07); border:1px solid rgba(245,237,224,.1); border-radius:14px; padding:20px 22px; max-width:none; }
  .todays-card .q-label { color:rgba(245,237,224,.45); }
  .todays-card .q-text { color:var(--cream); }
  .todays-card .q-option-btn { background:rgba(245,237,224,.08); border-color:rgba(245,237,224,.12); color:var(--cream); }
  .todays-card .q-option-btn:hover { background:rgba(245,237,224,.15); border-color:rgba(245,237,224,.3); }
  .todays-card .q-option-btn.skip-btn { color:rgba(245,237,224,.35); background:transparent; border:none; }
  .todays-card .q-option-btn.skip-btn:hover { color:rgba(245,237,224,.6); background:transparent; }

  /* library module tile badge */"""

assert OLD_CSS_ANCHOR in src, "CSS insertion anchor not found"
src = src.replace(OLD_CSS_ANCHOR, NEW_CSS_ANCHOR, 1)
print("  - CSS: countdown-widget styles + dark-card question overrides added")

# ── 6. Write output ────────────────────────────────────────────────────────
with open('daddy-duty-v4_2.html', 'w', encoding='utf-8') as f:
    f.write(src)

os.makedirs('docs', exist_ok=True)
shutil.copy('daddy-duty-v4_2.html', 'docs/index.html')

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

# ── 7. Verify ──────────────────────────────────────────────────────────────
content = open('daddy-duty-v4_2.html', encoding='utf-8').read()

# JS syntax check
node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', content, re.DOTALL)
    with open('/tmp/check_v4_2.js', 'w') as f:
        f.write(scripts[0])
    result = subprocess.run([node, '--check', '/tmp/check_v4_2.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print("  - JS syntax: ✓ (node --check passed)")
else:
    print("  - JS syntax: ⚠ skipped (node not found)")

# Structural assertions
assert "v4.2" in content, "version not updated"
assert 'id="topbar-streak"' not in content, "streak still in topbar"
assert 'class="countdown-widget"' in content, "countdown-widget not found"
assert '<div id="home-question-wrap"></div>' in content, "home-question-wrap not inside card"
# Verify question-wrap is inside home-card-wrap (not outside it)
card_start = content.find('<div class="todays-card" id="home-card-wrap">')
card_end   = content.find('</div>\n\n    <div id="home-nudge-wrap">', card_start)
assert card_end > card_start, "card end anchor not found"
card_html  = content[card_start:card_end]
assert 'id="home-question-wrap"' in card_html, "home-question-wrap not inside card HTML"
assert "Parenthood Toolkit" in content, "toolkit section not renamed"
assert "countdown-widget .countdown-num" in content, "countdown-widget CSS not added"
assert "todays-card .daily-question" in content, "dark-card question CSS not added"
print("  - All structural assertions passed")

# Card count preservation
pattern = r"id:'([a-z]-\d+)',phase:'([^']+)',weekRange:([^\,]*(?:\[[^\]]*\])?[^,]*),track:'([^']+)'"
lib_start = content.find('const LIBRARY_CARDS = [')
lib_end   = content.find('];', lib_start)
lib_section = content[lib_start:lib_end+2]
cards = re.findall(pattern, lib_section)
assert len(cards) == 191, f"Card count changed unexpectedly: {len(cards)} (expected 191)"
print(f"  - Card count preserved: {len(cards)}")

print("\n✓ daddy-duty-v4_2.html written")
print(f"  - URL: {SUPABASE_URL}")
print(f"  - Key: {SUPABASE_ANON_KEY[:8]}... (eyJ: {SUPABASE_ANON_KEY.startswith('eyJ')})")
print("  - Version: v4.2")
print("  - Home: card → question → actions → streak → nudge → countdown widget → toolkit")

# ── Deploy ─────────────────────────────────────────────────────────────────
print("\nPushing to GitHub Pages...")
subprocess.run(['git', 'add', 'docs/'], check=True)
commit = subprocess.run(
    ['git', 'commit', '-m', 'deploy: v4.2 — home redesign: card as primary hero, question inside card, compact countdown widget'],
    capture_output=True, text=True
)
if commit.returncode == 0:
    push = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    if push.returncode == 0:
        print("✓ Pushed — https://GrantBH12.github.io/daddy-duty")
    else:
        print(f"⚠  Push failed:\n{push.stderr}")
elif 'nothing to commit' in commit.stdout or 'nothing to commit' in commit.stderr:
    print("⚠  Nothing to commit")
else:
    print(f"⚠  Commit failed:\n{commit.stderr}")
