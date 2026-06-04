#!/usr/bin/env python3
"""Build v4.11: Daily question UX redesign.
- One question per day cap (answer/skip one → slot empty for the rest of the day)
- "Your situation" profile section in settings modal (shows answered data, allows upfront setup)
- Setting a profile field marks the corresponding daily question as answered
"""
import re, subprocess, os, shutil, json, struct, zlib, math

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

SW_VERSION = 'v4-11'


def make_icon_png(size):
    bg=(245,237,224);terra=(201,113,86);sage_d=(92,107,74)
    scale=size*0.65/140.0;ox=(size-140*scale)/2;oy=(size-100*scale)/2
    c1_cx,c1_cy=ox+55*scale,oy+50*scale;c1_r,c1_sw=32*scale,max(2.0,6*scale)
    c2_cx,c2_cy=ox+92*scale,oy+50*scale;c2_r,c2_sw=22*scale,max(2.0,6*scale)
    pixels=[[list(bg) for _ in range(size)] for _ in range(size)]
    def draw_ring(cx,cy,r,sw,color,mask_fn=None):
        ri,ro=r-sw/2,r+sw/2
        for py in range(max(0,int(cy-ro-2)),min(size,int(cy+ro+3))):
            for px in range(max(0,int(cx-ro-2)),min(size,int(cx+ro+3))):
                if mask_fn and not mask_fn(px,py): continue
                d=math.sqrt((px-cx)**2+(py-cy)**2)
                aa=max(0.,min(1.,d-ri+0.5))*max(0.,min(1.,ro-d+0.5))
                if aa>0:
                    er,eg,eb=pixels[py][px];cr,cg,cb=color
                    pixels[py][px]=[int(er+(cr-er)*aa),int(eg+(cg-eg)*aa),int(eb+(cb-eb)*aa)]
    def knot_mask(px,py):
        d=math.sqrt((px-c1_cx)**2+(py-c1_cy)**2)
        return d<(c1_r-c1_sw/2) or d>(c1_r+c1_sw/2)
    draw_ring(c2_cx,c2_cy,c2_r,c2_sw,sage_d,mask_fn=knot_mask)
    draw_ring(c1_cx,c1_cy,c1_r,c1_sw,terra)
    def png_chunk(t,d):
        c=t+d;return struct.pack('>I',len(d))+c+struct.pack('>I',zlib.crc32(c)&0xffffffff)
    ihdr=struct.pack('>IIBBBBB',size,size,8,2,0,0,0)
    raw=b''.join(b'\x00'+bytes([v for px in row for v in px]) for row in pixels)
    return b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',ihdr)+png_chunk(b'IDAT',zlib.compress(raw,6))+png_chunk(b'IEND',b'')


src = open('daddy-duty-v4_10.html', encoding='utf-8').read()

# ── 1. Inject credentials ──────────────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)

# ── 2. Version bump ────────────────────────────────────────────────────────────
assert "v4.10 · cloud sync" in src
src = src.replace("v4.10 · cloud sync", "v4.11 · cloud sync", 1)
assert "appVersion:'v4.10'" in src
src = src.replace("appVersion:'v4.10'", "appVersion:'v4.11'", 1)
print("  - Version: v4.10 → v4.11")

# ── 3. One question per day cap ────────────────────────────────────────────────
# Insert hadInteractionToday check into getNextQuestion() — unique anchor is
# `const log = state.questionLog || {};` which only appears in that function.
OLD_GET_NEXT = (
    "  const log = state.questionLog || {};\n"
    "  const today = todayStr();\n"
    "  const week = getGestationalWeek();\n"
)
NEW_GET_NEXT = (
    "  const log = state.questionLog || {};\n"
    "  const today = todayStr();\n"
    "  const hadInteractionToday=Object.values(log).some(e=>e.answered===today||e.skipped===today);\n"
    "  if(hadInteractionToday)return null;\n"
    "  const week = getGestationalWeek();\n"
)
assert OLD_GET_NEXT in src, "getNextQuestion log/today anchor not found"
src = src.replace(OLD_GET_NEXT, NEW_GET_NEXT, 1)
print("  - JS: getNextQuestion() — one question per day cap added")

# ── 4. CSS — settings button group styles ─────────────────────────────────────
OLD_DANGER_CSS = "  .settings-danger-zone{padding-top:20px;}"
NEW_DANGER_CSS = (
    "  .settings-danger-zone{padding-top:20px;}\n"
    "  .settings-btn-group{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;}\n"
    "  .settings-btn-group button{padding:6px 12px;border-radius:20px;font-size:12px;"
    "font-family:var(--font-mono);border:1px solid var(--cream-deeper);background:var(--cream);"
    "color:var(--ink-soft);cursor:pointer;transition:all .15s;}\n"
    "  .settings-btn-group button:hover{border-color:var(--terracotta);color:var(--terracotta);}\n"
    "  .settings-btn-group button.active{background:var(--terracotta);border-color:var(--terracotta);color:#fff;}\n"
    "  .settings-situation-label{font-size:13px;color:var(--ink-soft);margin-bottom:6px;}\n"
    "  .settings-situation-field{margin-bottom:14px;}\n"
    "  .settings-situation-field:last-child{margin-bottom:0;}"
)
assert OLD_DANGER_CSS in src, "settings-danger-zone CSS anchor not found"
src = src.replace(OLD_DANGER_CSS, NEW_DANGER_CSS, 1)
print("  - CSS: .settings-btn-group + .settings-situation-* styles added")

# ── 5. HTML — "Your situation" section in settings modal ──────────────────────
# Insert before the Backup & restore section.
OLD_BACKUP_SECTION = (
    '    <div class="settings-section">\n'
    '      <div class="settings-section-label">Backup &amp; restore</div>\n'
)
NEW_SITUATION_SECTION = (
    '    <div class="settings-section">\n'
    '      <div class="settings-section-label">Your situation</div>\n'
    '      <div style="font-size:12px;color:var(--ink-soft);margin-bottom:16px;line-height:1.6;">'
    'These personalise which cards and content you see. Change them any time.</div>\n'
    '      <div class="settings-situation-field">\n'
    '        <div class="settings-situation-label">Your GC\'s proximity</div>\n'
    '        <div class="settings-btn-group" id="s-gc-dist">\n'
    '          <button onclick="setProfileField(\'gcDistance\',\'same-state\')">Same state</button>\n'
    '          <button onclick="setProfileField(\'gcDistance\',\'different-state\')">Different state</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="settings-situation-field">\n'
    '        <div class="settings-situation-label">First-time parent?</div>\n'
    '        <div class="settings-btn-group" id="s-first-time">\n'
    '          <button onclick="setProfileField(\'isFirstTimeParent\',true)">Yes, first time</button>\n'
    '          <button onclick="setProfileField(\'isFirstTimeParent\',false)">I have other children</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="settings-situation-field">\n'
    '        <div class="settings-situation-label">Prior loss or failed transfer?</div>\n'
    '        <div class="settings-btn-group" id="s-prior-loss">\n'
    '          <button onclick="setProfileField(\'priorLoss\',true)">Yes, we have</button>\n'
    '          <button onclick="setProfileField(\'priorLoss\',false)">No / prefer not to say</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="settings-situation-field">\n'
    '        <div class="settings-situation-label">Do you have a partner?</div>\n'
    '        <div class="settings-btn-group" id="s-partnered">\n'
    '          <button onclick="setProfileField(\'isPartnered\',true)">Yes, partnered</button>\n'
    '          <button onclick="setProfileField(\'isPartnered\',false)">No, solo IP</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="settings-situation-field" style="margin-bottom:0;">\n'
    '        <div class="settings-situation-label">Content preferences</div>\n'
    '        <div class="settings-btn-group" id="s-content-legal">\n'
    '          <button onclick="setProfileField(\'legalContent\',true)">Include legal content</button>\n'
    '          <button onclick="setProfileField(\'legalContent\',false)">Skip legal content</button>\n'
    '        </div>\n'
    '        <div class="settings-btn-group" id="s-content-anxiety" style="margin-top:6px;">\n'
    '          <button onclick="setProfileField(\'anxietyContent\',true)">Include clinical/risk content</button>\n'
    '          <button onclick="setProfileField(\'anxietyContent\',false)">Skip clinical/risk content</button>\n'
    '        </div>\n'
    '      </div>\n'
    '    </div>\n'
    '\n'
    '    <div class="settings-section">\n'
    '      <div class="settings-section-label">Backup &amp; restore</div>\n'
)
assert OLD_BACKUP_SECTION in src, "Backup & restore section anchor not found"
src = src.replace(OLD_BACKUP_SECTION, NEW_SITUATION_SECTION, 1)
print("  - HTML: 'Your situation' settings section added")

# ── 6. JS — setProfileField() + renderSituationProfile() functions ────────────
OLD_PREVIEW_FN = (
    "function previewSettings(){\n"
    "  // live preview not needed — save on button click\n"
    "}"
)
NEW_PROFILE_FNS = (
    "function previewSettings(){\n"
    "  // live preview not needed — save on button click\n"
    "}\n"
    "function setProfileField(field,value){\n"
    "  if(!state.questionLog)state.questionLog={};\n"
    "  if(field==='gcDistance'){\n"
    "    state.settings.gcDistance=value;\n"
    "    if(!state.questionLog['q-001']||!state.questionLog['q-001'].answered)state.questionLog['q-001']={answered:todayStr(),update:{}};\n"
    "  }else if(field==='isFirstTimeParent'){\n"
    "    state.settings.isFirstTimeParent=value;\n"
    "    if(!state.questionLog['q-002']||!state.questionLog['q-002'].answered)state.questionLog['q-002']={answered:todayStr(),update:{}};\n"
    "  }else if(field==='priorLoss'){\n"
    "    state.settings.priorLoss=value;\n"
    "    if(!state.questionLog['q-003']||!state.questionLog['q-003'].answered)state.questionLog['q-003']={answered:todayStr(),update:{}};\n"
    "  }else if(field==='isPartnered'){\n"
    "    state.settings.isPartnered=value;\n"
    "    if(!state.questionLog['q-005']||!state.questionLog['q-005'].answered)state.questionLog['q-005']={answered:todayStr(),update:{}};\n"
    "  }else if(field==='legalContent'){\n"
    "    if(!state.mutedTracks)state.mutedTracks=[];\n"
    "    if(value)state.mutedTracks=state.mutedTracks.filter(t=>t!=='Legal');\n"
    "    else if(!state.mutedTracks.includes('Legal'))state.mutedTracks.push('Legal');\n"
    "    if(!state.questionLog['q-004']||!state.questionLog['q-004'].answered)state.questionLog['q-004']={answered:todayStr(),update:{}};\n"
    "  }else if(field==='anxietyContent'){\n"
    "    if(!state.mutedSensitivity)state.mutedSensitivity=[];\n"
    "    if(value)state.mutedSensitivity=state.mutedSensitivity.filter(t=>t!=='anxiety-content');\n"
    "    else if(!state.mutedSensitivity.includes('anxiety-content'))state.mutedSensitivity.push('anxiety-content');\n"
    "    if(!state.questionLog['q-004']||!state.questionLog['q-004'].answered)state.questionLog['q-004']={answered:todayStr(),update:{}};\n"
    "  }\n"
    "  save();renderSituationProfile();\n"
    "}\n"
    "function renderSituationProfile(){\n"
    "  const s=state.settings||{};const mt=state.mutedTracks||[];const ms=state.mutedSensitivity||[];\n"
    "  function ab(id,first){const g=document.getElementById(id);if(!g)return;"
    "const b=g.querySelectorAll('button');if(b[0])b[0].classList.toggle('active',first===true);"
    "if(b[1])b[1].classList.toggle('active',first===false);}\n"
    "  ab('s-gc-dist',s.gcDistance==='same-state'?true:s.gcDistance==='different-state'?false:null);\n"
    "  ab('s-first-time',s.isFirstTimeParent===true?true:s.isFirstTimeParent===false?false:null);\n"
    "  ab('s-prior-loss',s.priorLoss===true?true:s.priorLoss===false?false:null);\n"
    "  ab('s-partnered',s.isPartnered===true?true:s.isPartnered===false?false:null);\n"
    "  ab('s-content-legal',!mt.includes('Legal'));\n"
    "  ab('s-content-anxiety',!ms.includes('anxiety-content'));\n"
    "}"
)
assert OLD_PREVIEW_FN in src, "previewSettings() anchor not found"
src = src.replace(OLD_PREVIEW_FN, NEW_PROFILE_FNS, 1)
print("  - JS: setProfileField() + renderSituationProfile() functions added")

# ── 7. openSettings() — call renderSituationProfile() on open ─────────────────
OLD_OPEN_SETTINGS_END = (
    "  renderAccountSection();\n"
    "  document.getElementById('settings-backdrop').classList.add('open');\n"
)
NEW_OPEN_SETTINGS_END = (
    "  renderAccountSection();\n"
    "  renderSituationProfile();\n"
    "  document.getElementById('settings-backdrop').classList.add('open');\n"
)
assert OLD_OPEN_SETTINGS_END in src, "openSettings renderAccountSection anchor not found"
src = src.replace(OLD_OPEN_SETTINGS_END, NEW_OPEN_SETTINGS_END, 1)
print("  - JS: openSettings() calls renderSituationProfile() on open")

# ── 8. Write output ────────────────────────────────────────────────────────────
with open('daddy-duty-v4_11.html', 'w', encoding='utf-8') as f:
    f.write(src)

os.makedirs('docs', exist_ok=True)
shutil.copy('daddy-duty-v4_11.html', 'docs/index.html')

os.makedirs('docs/brand', exist_ok=True)
for logo in ['logo.svg', 'logo-cream.svg', 'logo-mono.svg', 'logo-favicon.svg']:
    lpath = f'brand/assets/{logo}'
    if os.path.exists(lpath): shutil.copy(lpath, f'docs/brand/{logo}')

os.makedirs('docs/icons', exist_ok=True)
for icon_size, icon_name in [(192, 'icon-192'), (512, 'icon-512'), (180, 'icon-180')]:
    with open(f'docs/icons/{icon_name}.png', 'wb') as f:
        f.write(make_icon_png(icon_size))

sw_content = f"""/* Daddy Duty service worker — cache key: daddy-duty-{SW_VERSION} */
const CACHE = 'daddy-duty-{SW_VERSION}';
const APP_URL = self.location.pathname.replace(/sw\\.js$/, '');
self.addEventListener('install', e => {{ e.waitUntil(caches.open(CACHE).then(c => c.add(APP_URL)).then(() => self.skipWaiting())); }});
self.addEventListener('activate', e => {{ e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener('fetch', e => {{ if (!e.request.url.startsWith(self.location.origin)) return; e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).catch(() => caches.match(APP_URL)))); }});
"""
with open('docs/sw.js', 'w') as f: f.write(sw_content)

manifest = {"name":"Daddy Duty","short_name":"Daddy Duty","description":"Your personal guide to becoming a father","start_url":"/daddy-duty/","display":"standalone","background_color":"#f5ede0","theme_color":"#c97156","icons":[{"src":"./icons/icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},{"src":"./icons/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]}
with open('docs/manifest.json', 'w') as f: json.dump(manifest, f, indent=2)

# ── 9. Verify ──────────────────────────────────────────────────────────────────
content = open('daddy-duty-v4_11.html', encoding='utf-8').read()

node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', content, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v4_11.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v4_11.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print("  - JS syntax: ✓ (node --check passed)")
else:
    print("  - JS syntax: ⚠ skipped (node not found)")

assert "v4.11 · cloud sync" in content
assert 'hadInteractionToday' in content, "daily question cap missing"
assert 'settings-btn-group' in content, "settings btn group CSS missing"
assert 'Your situation' in content, "Your situation section missing"
assert 'setProfileField' in content, "setProfileField function missing"
assert 'renderSituationProfile' in content, "renderSituationProfile function missing"
assert 's-gc-dist' in content, "GC dist button group missing"
assert 's-content-legal' in content, "content pref button group missing"

pattern = r"id:'([a-z]-\d+)',phase:'([^']+)',weekRange:([^\,]*(?:\[[^\]]*\])?[^,]*),track:'([^']+)'"
lib_start = content.find('const LIBRARY_CARDS = [')
lib_end   = content.find('];', lib_start)
cards = re.findall(pattern, content[lib_start:lib_end+2])
assert len(cards) == 191, f"Card count changed: {len(cards)} (expected 191)"
print(f"  - Card count preserved: {len(cards)}")
print("  - All assertions passed ✓")

print("\n✓ daddy-duty-v4_11.html written")
print("  - Version: v4.11")
print("  - Fix: one question per day — no more rapid-fire question flood")
print("  - New: Settings → Your situation — shows and edits profile answers")

# ── Deploy ─────────────────────────────────────────────────────────────────────
print("\nPushing to GitHub Pages...")
subprocess.run(['git', 'add', 'docs/'], check=True)
commit = subprocess.run(
    ['git', 'commit', '-m', 'deploy: v4.11 — daily question UX redesign (one/day cap + settings profile section)'],
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
