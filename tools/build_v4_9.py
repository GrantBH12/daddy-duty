#!/usr/bin/env python3
"""Build v4.9: Fix library browse mode — only show cards the user has been presented with."""
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

SW_VERSION = 'v4-9'


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


src = open('daddy-duty-v4_8.html', encoding='utf-8').read()

# ── 1. Inject credentials ──────────────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)

# ── 2. Version bump ────────────────────────────────────────────────────────────
assert "v4.8 · cloud sync" in src
src = src.replace("v4.8 · cloud sync", "v4.9 · cloud sync", 1)
assert "appVersion:'v4.8'" in src
src = src.replace("appVersion:'v4.8'", "appVersion:'v4.9'", 1)
print("  - Version: v4.8 → v4.9")

# ── 3. Fix renderLibBrowse() — filter to seen cards only ──────────────────────
# Currently shows ALL cards in the phase pool, revealing future unread cards.
# Fix: filter to cards the user has been presented with (in dailyCardLog or readCardIds).
OLD_BROWSE_FILTER = (
    "  let pool = getPhasePool(phase);\n"
    "  if (libBrowseTrack) pool = pool.filter(c => c.track === libBrowseTrack);\n"
    "  if (libBrowseQuery) pool = pool.filter(c =>\n"
    "    c.title.toLowerCase().includes(libBrowseQuery) || c.body.toLowerCase().includes(libBrowseQuery)\n"
    "  );\n"
    "  if (!pool.length) {\n"
    "    stage.innerHTML = '<div class=\"lib-browse-empty\">No cards match.</div>';\n"
    "    return;\n"
    "  }\n"
)
NEW_BROWSE_FILTER = (
    "  let pool = getPhasePool(phase);\n"
    "  const seenIds = new Set([...Object.values(state.dailyCardLog||{}),...(state.readCardIds||[])]);\n"
    "  pool = pool.filter(c => seenIds.has(c.id));\n"
    "  if (!pool.length) {\n"
    "    stage.innerHTML = `<div class=\"lib-browse-empty\">Read today’s card first — your browse list grows as you use the app daily.</div>`;\n"
    "    return;\n"
    "  }\n"
    "  if (libBrowseTrack) pool = pool.filter(c => c.track === libBrowseTrack);\n"
    "  if (libBrowseQuery) pool = pool.filter(c =>\n"
    "    c.title.toLowerCase().includes(libBrowseQuery) || c.body.toLowerCase().includes(libBrowseQuery)\n"
    "  );\n"
    "  if (!pool.length) {\n"
    "    stage.innerHTML = '<div class=\"lib-browse-empty\">No cards match.</div>';\n"
    "    return;\n"
    "  }\n"
)
assert OLD_BROWSE_FILTER in src, "renderLibBrowse pool filter anchor not found"
src = src.replace(OLD_BROWSE_FILTER, NEW_BROWSE_FILTER, 1)
print("  - JS: renderLibBrowse() now filters to seen cards only (dailyCardLog ∪ readCardIds)")

# ── 4. Write output ────────────────────────────────────────────────────────────
with open('daddy-duty-v4_9.html', 'w', encoding='utf-8') as f:
    f.write(src)

os.makedirs('docs', exist_ok=True)
shutil.copy('daddy-duty-v4_9.html', 'docs/index.html')

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

# ── 5. Verify ──────────────────────────────────────────────────────────────────
content = open('daddy-duty-v4_9.html', encoding='utf-8').read()

node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', content, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v4_9.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v4_9.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print("  - JS syntax: ✓ (node --check passed)")
else:
    print("  - JS syntax: ⚠ skipped (node not found)")

assert "v4.9 · cloud sync" in content
assert 'seenIds' in content, "seen-cards filter missing"
assert 'dailyCardLog' in content, "dailyCardLog reference missing"

pattern = r"id:'([a-z]-\d+)',phase:'([^']+)',weekRange:([^\,]*(?:\[[^\]]*\])?[^,]*),track:'([^']+)'"
lib_start = content.find('const LIBRARY_CARDS = [')
lib_end   = content.find('];', lib_start)
cards = re.findall(pattern, content[lib_start:lib_end+2])
assert len(cards) == 191, f"Card count changed: {len(cards)} (expected 191)"
print(f"  - Card count preserved: {len(cards)}")
print("  - All assertions passed ✓")

print("\n✓ daddy-duty-v4_9.html written")
print("  - Version: v4.9")
print("  - Fix: Library browse mode now only shows cards previously drawn as daily cards")

# ── Deploy ─────────────────────────────────────────────────────────────────────
print("\nPushing to GitHub Pages...")
subprocess.run(['git', 'add', 'docs/'], check=True)
commit = subprocess.run(
    ['git', 'commit', '-m', 'deploy: v4.9 — fix library browse to only show seen cards'],
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
