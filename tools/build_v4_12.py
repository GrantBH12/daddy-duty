#!/usr/bin/env python3
"""Build v4.12: Onboarding-profile integration + 2 new questions.
- inferProfileFromOnboarding(): partnerName→isPartnered, non-GC-path→suppresses q-001
- q-006: birth attendance (new state field + filter + tags on s-015, t-007)
- q-021: support network milestone check-in (tags on s-003, t-016, n-032)
- renderSituationProfile(): birth attend 3-btn group + GC field hidden for non-surrogacy paths
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

SW_VERSION = 'v4-12'


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


src = open('daddy-duty-v4_11.html', encoding='utf-8').read()

# ── 1. Inject credentials ──────────────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)

# ── 2. Version bump ────────────────────────────────────────────────────────────
assert "v4.11 · cloud sync" in src
src = src.replace("v4.11 · cloud sync", "v4.12 · cloud sync", 1)
assert "appVersion:'v4.11'" in src
src = src.replace("appVersion:'v4.11'", "appVersion:'v4.12'", 1)
print("  - Version: v4.11 → v4.12")

# ── 3. Add birthAttendance:null to initial state settings ──────────────────────
OLD_INIT_STATE = "gcDistance:null, priorLoss:null, isFirstTimeParent:null, isPartnered:null"
NEW_INIT_STATE = "gcDistance:null, priorLoss:null, isFirstTimeParent:null, isPartnered:null, birthAttendance:null"
assert OLD_INIT_STATE in src, "initial state settings anchor not found"
src = src.replace(OLD_INIT_STATE, NEW_INIT_STATE, 1)
print("  - State: birthAttendance:null added to initial settings")

# ── 4. Add birthAttendance:null to loadState Object.assign defaults ────────────
OLD_LOAD_STATE = "gcDistance:null,priorLoss:null,isFirstTimeParent:null,isPartnered:null}"
NEW_LOAD_STATE = "gcDistance:null,priorLoss:null,isFirstTimeParent:null,isPartnered:null,birthAttendance:null}"
assert OLD_LOAD_STATE in src, "loadState Object.assign anchor not found"
src = src.replace(OLD_LOAD_STATE, NEW_LOAD_STATE, 1)
print("  - State: birthAttendance:null added to loadState defaults")

# ── 5. Add setBirthAttendance handler to applyQuestionAnswer() ─────────────────
OLD_APPLY_END = (
    "    if (stateUpdate.setIsPartnered !== undefined) {\n"
    "      state.settings.isPartnered = stateUpdate.setIsPartnered;\n"
    "    }\n"
    "  }\n"
    "  save();\n"
    "  renderDailyQuestion();\n"
)
NEW_APPLY_END = (
    "    if (stateUpdate.setIsPartnered !== undefined) {\n"
    "      state.settings.isPartnered = stateUpdate.setIsPartnered;\n"
    "    }\n"
    "    if (stateUpdate.setBirthAttendance) {\n"
    "      state.settings.birthAttendance = stateUpdate.setBirthAttendance;\n"
    "    }\n"
    "  }\n"
    "  save();\n"
    "  renderDailyQuestion();\n"
)
assert OLD_APPLY_END in src, "applyQuestionAnswer setIsPartnered anchor not found"
src = src.replace(OLD_APPLY_END, NEW_APPLY_END, 1)
print("  - JS: applyQuestionAnswer() handles setBirthAttendance")

# ── 6. Add q-006 (birth attendance setup question) ────────────────────────────
# Unique anchor: end of q-005 "solo intended parent" option + milestone comment
OLD_AFTER_Q005 = (
    "    {label:`I'm doing this as a solo intended parent`,stateUpdate:{setIsPartnered:false}},\n"
    "    {label:`Skip`,stateUpdate:{skipQuestion:true}}\n"
    "  ]},\n"
    "  // ── MILESTONE CHECK-IN QUESTIONS (triggered by card tag) ──\n"
)
NEW_AFTER_Q005 = (
    "    {label:`I'm doing this as a solo intended parent`,stateUpdate:{setIsPartnered:false}},\n"
    "    {label:`Skip`,stateUpdate:{skipQuestion:true}}\n"
    "  ]},\n"
    "  {id:'q-006',phase:'preparing',weekRange:null,triggeredByTag:null,\n"
    "   question:`Are you planning to be present at the birth?`,\n"
    "   options:[\n"
    "    {label:`Yes — I plan to be in the delivery room`,stateUpdate:{setBirthAttendance:'in-room'}},\n"
    "    {label:`At the hospital, but may not be in the room`,stateUpdate:{setBirthAttendance:'at-hospital'}},\n"
    "    {label:`I won't be present for the birth`,stateUpdate:{setBirthAttendance:'not-attending'}},\n"
    "    {label:`Skip`,stateUpdate:{skipQuestion:true}}\n"
    "  ]},\n"
    "  // ── MILESTONE CHECK-IN QUESTIONS (triggered by card tag) ──\n"
)
assert OLD_AFTER_Q005 in src, "end of q-005 anchor not found"
src = src.replace(OLD_AFTER_Q005, NEW_AFTER_Q005, 1)
print("  - DAILY_QUESTIONS: q-006 (birth attendance) added")

# ── 7. Add q-021 (support network milestone check-in) ─────────────────────────
# Unique anchor: q-020's last unique option + closing array ];
OLD_AFTER_Q020 = (
    "    {label:`We're waiting until closer to the birth to set it up`,stateUpdate:{noOp:true}},\n"
    "    {label:`Skip`,stateUpdate:{skipQuestion:true}}\n"
    "  ]},\n"
    "];\n"
)
NEW_AFTER_Q020 = (
    "    {label:`We're waiting until closer to the birth to set it up`,stateUpdate:{noOp:true}},\n"
    "    {label:`Skip`,stateUpdate:{skipQuestion:true}}\n"
    "  ]},\n"
    "  {id:'q-021',phase:'any',weekRange:null,triggeredByTag:'support-network',\n"
    "   question:`How's your support network for the newborn phase coming along?`,\n"
    "   options:[\n"
    "    {label:`Sorted — meals, coverage, and help are all organized`,stateUpdate:{addMilestone:'support-network'}},\n"
    "    {label:`Working on it, but not locked in yet`,stateUpdate:{noOp:true}},\n"
    "    {label:`Haven't really started thinking about it`,stateUpdate:{noOp:true}},\n"
    "    {label:`Skip`,stateUpdate:{skipQuestion:true}}\n"
    "  ]},\n"
    "];\n"
)
assert OLD_AFTER_Q020 in src, "end of q-020 anchor not found"
src = src.replace(OLD_AFTER_Q020, NEW_AFTER_Q020, 1)
print("  - DAILY_QUESTIONS: q-021 (support network milestone) added")

# ── 8. Tag s-015 with birth-attendance-ip ────────────────────────────────────
OLD_S015_TAGS = (
    "{id:'s-015',phase:'second',weekRange:null,track:'Logistics',\n"
    "   tags:[],"
)
NEW_S015_TAGS = (
    "{id:'s-015',phase:'second',weekRange:null,track:'Logistics',\n"
    "   tags:['birth-attendance-ip'],"
)
assert OLD_S015_TAGS in src, "s-015 tags anchor not found"
src = src.replace(OLD_S015_TAGS, NEW_S015_TAGS, 1)
print("  - Card s-015 tagged: birth-attendance-ip")

# ── 9. Tag t-007 with birth-attendance-ip ────────────────────────────────────
OLD_T007_TAGS = (
    "{id:'t-007',phase:'third',weekRange:[32,40],track:'Medical',\n"
    "   tags:['anxiety-content'],"
)
NEW_T007_TAGS = (
    "{id:'t-007',phase:'third',weekRange:[32,40],track:'Medical',\n"
    "   tags:['anxiety-content','birth-attendance-ip'],"
)
assert OLD_T007_TAGS in src, "t-007 tags anchor not found"
src = src.replace(OLD_T007_TAGS, NEW_T007_TAGS, 1)
print("  - Card t-007 tagged: birth-attendance-ip")

# ── 10. Tag s-003 with support-network ───────────────────────────────────────
OLD_S003_TAGS = (
    "{id:'s-003',phase:'second',weekRange:null,track:'Logistics',\n"
    "   tags:[],"
)
NEW_S003_TAGS = (
    "{id:'s-003',phase:'second',weekRange:null,track:'Logistics',\n"
    "   tags:['support-network'],"
)
assert OLD_S003_TAGS in src, "s-003 tags anchor not found"
src = src.replace(OLD_S003_TAGS, NEW_S003_TAGS, 1)
print("  - Card s-003 tagged: support-network")

# ── 11. Tag t-016 with support-network ───────────────────────────────────────
OLD_T016_TAGS = (
    "{id:'t-016',phase:'third',weekRange:null,track:'Logistics',\n"
    "   tags:[],"
)
NEW_T016_TAGS = (
    "{id:'t-016',phase:'third',weekRange:null,track:'Logistics',\n"
    "   tags:['support-network'],"
)
assert OLD_T016_TAGS in src, "t-016 tags anchor not found"
src = src.replace(OLD_T016_TAGS, NEW_T016_TAGS, 1)
print("  - Card t-016 tagged: support-network")

# ── 12. Tag n-032 with support-network ───────────────────────────────────────
OLD_N032_TAGS = (
    "{id:'n-032',phase:'newborn',weekRange:null,track:'Self',\n"
    "   tags:[],"
)
NEW_N032_TAGS = (
    "{id:'n-032',phase:'newborn',weekRange:null,track:'Self',\n"
    "   tags:['support-network'],"
)
assert OLD_N032_TAGS in src, "n-032 tags anchor not found"
src = src.replace(OLD_N032_TAGS, NEW_N032_TAGS, 1)
print("  - Card n-032 tagged: support-network")

# ── 13. Add birth-attendance-ip filter to getPhasePool() ─────────────────────
OLD_POOL_END = (
    "  if (isPartnered === false) {\n"
    "    const f = pool.filter(c => !(c.tags || []).includes('has-partner'));\n"
    "    if (f.length > 0) pool = f;\n"
    "  }\n"
    "\n"
    "  return pool;\n"
    "}"
)
NEW_POOL_END = (
    "  if (isPartnered === false) {\n"
    "    const f = pool.filter(c => !(c.tags || []).includes('has-partner'));\n"
    "    if (f.length > 0) pool = f;\n"
    "  }\n"
    "  if (state.settings && state.settings.birthAttendance === 'not-attending') {\n"
    "    const f = pool.filter(c => !(c.tags || []).includes('birth-attendance-ip'));\n"
    "    if (f.length > 0) pool = f;\n"
    "  }\n"
    "\n"
    "  return pool;\n"
    "}"
)
assert OLD_POOL_END in src, "getPhasePool isPartnered filter anchor not found"
src = src.replace(OLD_POOL_END, NEW_POOL_END, 1)
print("  - JS: getPhasePool() birth-attendance-ip filter added")

# ── 14. Add birth attendance field to "Your situation" HTML ───────────────────
# Insert between s-partnered field and content preferences field.
# Unique anchor: the "No, solo IP" button close + content prefs opening div.
OLD_BEFORE_CONTENT_PREFS = (
    '          <button onclick="setProfileField(\'isPartnered\',false)">No, solo IP</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="settings-situation-field" style="margin-bottom:0;">\n'
    '        <div class="settings-situation-label">Content preferences</div>\n'
)
NEW_BEFORE_CONTENT_PREFS = (
    '          <button onclick="setProfileField(\'isPartnered\',false)">No, solo IP</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="settings-situation-field">\n'
    '        <div class="settings-situation-label">Planning to attend the birth?</div>\n'
    '        <div class="settings-btn-group" id="s-birth-attend">\n'
    '          <button onclick="setProfileField(\'birthAttendance\',\'in-room\')">In the room</button>\n'
    '          <button onclick="setProfileField(\'birthAttendance\',\'at-hospital\')">At the hospital</button>\n'
    '          <button onclick="setProfileField(\'birthAttendance\',\'not-attending\')">Won\'t be present</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="settings-situation-field" style="margin-bottom:0;">\n'
    '        <div class="settings-situation-label">Content preferences</div>\n'
)
assert OLD_BEFORE_CONTENT_PREFS in src, "birth attendance HTML insertion anchor not found"
src = src.replace(OLD_BEFORE_CONTENT_PREFS, NEW_BEFORE_CONTENT_PREFS, 1)
print("  - HTML: 'Planning to attend the birth?' field added to Your situation")

# ── 15. Extend setProfileField() with birthAttendance case ───────────────────
OLD_SET_PROFILE_END = (
    "    if(!state.questionLog['q-004']||!state.questionLog['q-004'].answered)"
    "state.questionLog['q-004']={answered:todayStr(),update:{}};\n"
    "  }\n"
    "  save();renderSituationProfile();\n"
    "}"
)
NEW_SET_PROFILE_END = (
    "    if(!state.questionLog['q-004']||!state.questionLog['q-004'].answered)"
    "state.questionLog['q-004']={answered:todayStr(),update:{}};\n"
    "  }else if(field==='birthAttendance'){\n"
    "    state.settings.birthAttendance=value;\n"
    "    if(!state.questionLog['q-006']||!state.questionLog['q-006'].answered)"
    "state.questionLog['q-006']={answered:todayStr(),update:{}};\n"
    "  }\n"
    "  save();renderSituationProfile();\n"
    "}"
)
assert OLD_SET_PROFILE_END in src, "setProfileField end anchor not found"
src = src.replace(OLD_SET_PROFILE_END, NEW_SET_PROFILE_END, 1)
print("  - JS: setProfileField() handles birthAttendance")

# ── 16. Extend renderSituationProfile() with birth attend + GC visibility ─────
OLD_RENDER_SITUATION = (
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
NEW_RENDER_SITUATION = (
    "function renderSituationProfile(){\n"
    "  const s=state.settings||{};const mt=state.mutedTracks||[];const ms=state.mutedSensitivity||[];\n"
    "  function ab(id,first){const g=document.getElementById(id);if(!g)return;"
    "const b=g.querySelectorAll('button');if(b[0])b[0].classList.toggle('active',first===true);"
    "if(b[1])b[1].classList.toggle('active',first===false);}\n"
    "  ab('s-gc-dist',s.gcDistance==='same-state'?true:s.gcDistance==='different-state'?false:null);\n"
    "  ab('s-first-time',s.isFirstTimeParent===true?true:s.isFirstTimeParent===false?false:null);\n"
    "  ab('s-prior-loss',s.priorLoss===true?true:s.priorLoss===false?false:null);\n"
    "  ab('s-partnered',s.isPartnered===true?true:s.isPartnered===false?false:null);\n"
    "  const bg=document.getElementById('s-birth-attend');\n"
    "  if(bg){const bb=bg.querySelectorAll('button');\n"
    "    if(bb[0])bb[0].classList.toggle('active',s.birthAttendance==='in-room');\n"
    "    if(bb[1])bb[1].classList.toggle('active',s.birthAttendance==='at-hospital');\n"
    "    if(bb[2])bb[2].classList.toggle('active',s.birthAttendance==='not-attending');}\n"
    "  ab('s-content-legal',!mt.includes('Legal'));\n"
    "  ab('s-content-anxiety',!ms.includes('anxiety-content'));\n"
    "  const gcDistField=document.getElementById('s-gc-dist')?.closest('.settings-situation-field');\n"
    "  if(gcDistField)gcDistField.style.display=isSurrogacyPath(s.familyPath)?'':'none';\n"
    "}"
)
assert OLD_RENDER_SITUATION in src, "renderSituationProfile anchor not found"
src = src.replace(OLD_RENDER_SITUATION, NEW_RENDER_SITUATION, 1)
print("  - JS: renderSituationProfile() extended (birth attend + GC field visibility)")

# ── 17. Add inferProfileFromOnboarding() function ────────────────────────────
# Insert after renderSituationProfile() and before setTransferUnknown()
OLD_BEFORE_TRANSFER = "function setTransferUnknown(){"
NEW_BEFORE_TRANSFER = (
    "function inferProfileFromOnboarding(){\n"
    "  const s=state.settings||{};\n"
    "  if(!state.questionLog)state.questionLog={};\n"
    "  let mutated=false;\n"
    "  if(s.partnerName&&s.isPartnered===null){\n"
    "    s.isPartnered=true;\n"
    "    if(!state.questionLog['q-005']||!state.questionLog['q-005'].answered)"
    "state.questionLog['q-005']={answered:todayStr(),update:{}};\n"
    "    mutated=true;\n"
    "  }\n"
    "  if(!isSurrogacyPath(s.familyPath)){\n"
    "    if(!state.questionLog['q-001']||!state.questionLog['q-001'].answered){\n"
    "      state.questionLog['q-001']={answered:todayStr(),update:{}};\n"
    "      mutated=true;\n"
    "    }\n"
    "  }\n"
    "  if(mutated)save();\n"
    "}\n"
    "function setTransferUnknown(){"
)
assert OLD_BEFORE_TRANSFER in src, "setTransferUnknown anchor not found"
src = src.replace(OLD_BEFORE_TRANSFER, NEW_BEFORE_TRANSFER, 1)
print("  - JS: inferProfileFromOnboarding() function added")

# ── 18. Call inferProfileFromOnboarding() in onboardingDone() ─────────────────
OLD_OB_DONE = (
    "  state.settings.onboardingDone = true;\n"
    "  save();\n"
    "  closeOnboarding();\n"
)
NEW_OB_DONE = (
    "  state.settings.onboardingDone = true;\n"
    "  inferProfileFromOnboarding();\n"
    "  save();\n"
    "  closeOnboarding();\n"
)
assert OLD_OB_DONE in src, "onboardingDone anchor not found"
src = src.replace(OLD_OB_DONE, NEW_OB_DONE, 1)
print("  - JS: onboardingDone() calls inferProfileFromOnboarding()")

# ── 19. Call inferProfileFromOnboarding() at startup (migrates existing users) ─
OLD_STARTUP = "checkOnboarding();\n(function(){"
NEW_STARTUP = "checkOnboarding();\ninferProfileFromOnboarding();\n(function(){"
assert OLD_STARTUP in src, "startup checkOnboarding anchor not found"
src = src.replace(OLD_STARTUP, NEW_STARTUP, 1)
print("  - JS: startup calls inferProfileFromOnboarding() (migrates existing users)")

# ── 20. Write output ──────────────────────────────────────────────────────────
with open('daddy-duty-v4_12.html', 'w', encoding='utf-8') as f:
    f.write(src)

os.makedirs('docs', exist_ok=True)
shutil.copy('daddy-duty-v4_12.html', 'docs/index.html')

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

# ── 21. Verify ────────────────────────────────────────────────────────────────
content = open('daddy-duty-v4_12.html', encoding='utf-8').read()

node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', content, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v4_12.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v4_12.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print("  - JS syntax: ✓ (node --check passed)")
else:
    print("  - JS syntax: ⚠ skipped (node not found)")

assert "v4.12 · cloud sync" in content
assert 'birthAttendance:null' in content, "birthAttendance state field missing"
assert 'inferProfileFromOnboarding' in content, "inference function missing"
assert "q-006" in content, "q-006 missing"
assert "q-021" in content, "q-021 missing"
assert "birth-attendance-ip" in content, "birth-attendance-ip tag missing"
assert "support-network" in content, "support-network tag missing"
assert "s-birth-attend" in content, "birth attend settings group missing"
assert "setBirthAttendance" in content, "setBirthAttendance handler missing"

pattern = r"id:'([a-z]-\d+)',phase:'([^']+)',weekRange:([^\,]*(?:\[[^\]]*\])?[^,]*),track:'([^']+)'"
lib_start = content.find('const LIBRARY_CARDS = [')
lib_end   = content.find('];', lib_start)
cards = re.findall(pattern, content[lib_start:lib_end+2])
assert len(cards) == 191, f"Card count changed: {len(cards)} (expected 191)"
print(f"  - Card count preserved: {len(cards)}")
print("  - All assertions passed ✓")

print("\n✓ daddy-duty-v4_12.html written")
print("  - Version: v4.12")
print("  - Onboarding: partnerName→isPartnered, non-GC-path→suppresses q-001")
print("  - q-006: birth attendance (s-015, t-007 tagged)")
print("  - q-021: support network milestone (s-003, t-016, n-032 tagged)")

# ── Deploy ─────────────────────────────────────────────────────────────────────
print("\nPushing to GitHub Pages...")
subprocess.run(['git', 'add', 'docs/'], check=True)
commit = subprocess.run(
    ['git', 'commit', '-m', 'deploy: v4.12 — onboarding-profile integration, birth attendance + support network questions'],
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
