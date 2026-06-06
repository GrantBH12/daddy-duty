#!/usr/bin/env python3
"""build_v5_1.py — v5.1: situation-aware dynamic content
Source: daddy-duty-v5_0.html -> daddy-duty-v5_1.html
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

src = open('daddy-duty-v5_0.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials (always regex) ─────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version: v5.0 → v5.1 ──────────────────────────────────────────────────
OLD2a = "v5.0 \xb7 cloud sync"
NEW2a = "v5.1 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:\x27v5.0\x27"
NEW2b = "appVersion:\x27v5.1\x27"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.0 → v5.1')

# ── 3. situationSuppressed() + extend passesFilter() ─────────────────────────
OLD3 = (
    "function passesFilter(t){\n"
    "  if(!isSurrogacyPath(state.settings.familyPath)&&t.tags&&t.tags.includes(\x27GC\x27))return false;\n"
    "  if((state.settings||{}).userRole===\x27partner\x27&&t.tags&&t.tags.includes(\x27GC\x27))return false;"
)
NEW3 = (
    "function situationSuppressed(tags){\n"
    "  if(!tags||!tags.length)return false;\n"
    "  const s=state.settings;\n"
    "  if(tags.includes(\x27remote-gc\x27)&&s.gcDistance===\x27same-state\x27)return true;\n"
    "  if(tags.includes(\x27same-state-gc\x27)&&s.gcDistance===\x27different-state\x27)return true;\n"
    "  if(tags.includes(\x27first-time-parent\x27)&&s.isFirstTimeParent===false)return true;\n"
    "  if(tags.includes(\x27prior-loss\x27)&&s.priorLoss===false)return true;\n"
    "  if(tags.includes(\x27has-partner\x27)&&s.isPartnered===false)return true;\n"
    "  if(tags.includes(\x27in-room-birth\x27)&&s.birthAttendance!==\x27in-room\x27)return true;\n"
    "  return false;\n"
    "}\n\n"
    "function passesFilter(t){\n"
    "  if(!isSurrogacyPath(state.settings.familyPath)&&t.tags&&t.tags.includes(\x27GC\x27))return false;\n"
    "  if((state.settings||{}).userRole===\x27partner\x27&&t.tags&&t.tags.includes(\x27GC\x27))return false;\n"
    "  if(situationSuppressed(t.tags))return false;"
)
assert OLD3 in src, "passesFilter anchor not found"
src = src.replace(OLD3, NEW3, 1)
print('  - situationSuppressed() added; passesFilter() extended')

# ── 4–14. Task tag additions (has-partner, in-room-birth) ─────────────────────
TASK_PATCHES = [
    # pre-transfer
    (
        "{ phase:\x27pre-transfer\x27, cat:\x27Emotional\x27,  tags:[\x27Wife\x27],       title:\x27Decide with {{partner}} what names you will each go by as parents\x27 },",
        "{ phase:\x27pre-transfer\x27, cat:\x27Emotional\x27,  tags:[\x27Wife\x27,\x27has-partner\x27], title:\x27Decide with {{partner}} what names you will each go by as parents\x27 },"
    ),
    (
        "{ phase:\x27pre-transfer\x27, cat:\x27Emotional\x27,  tags:[\x27Wife\x27],       title:\x27Agree with {{partner}} on how and when to tell family and friends about the transfer\x27 },",
        "{ phase:\x27pre-transfer\x27, cat:\x27Emotional\x27,  tags:[\x27Wife\x27,\x27has-partner\x27], title:\x27Agree with {{partner}} on how and when to tell family and friends about the transfer\x27 },"
    ),
    (
        "{ phase:\x27pre-transfer\x27, cat:\x27Medical\x27,    tags:[\x27GC\x27,\x27Wife\x27],  title:\x27Decide on induced lactation before transfer — starting the protocol takes months\x27 },",
        "{ phase:\x27pre-transfer\x27, cat:\x27Medical\x27,    tags:[\x27GC\x27,\x27Wife\x27,\x27has-partner\x27], title:\x27Decide on induced lactation before transfer — starting the protocol takes months\x27 },"
    ),
    # first trimester
    (
        "{ phase:\x27first\x27, cat:\x27Emotional\x27, tags:[\x27GC\x27,\x27Wife\x27],  title:\x27Mark the moment with {{partner}} when {{GC}} is discharged from the fertility clinic to OB care\x27 },",
        "{ phase:\x27first\x27, cat:\x27Emotional\x27, tags:[\x27GC\x27,\x27Wife\x27,\x27has-partner\x27], title:\x27Mark the moment with {{partner}} when {{GC}} is discharged from the fertility clinic to OB care\x27 },"
    ),
    (
        "{ phase:\x27first\x27, cat:\x27Partner\x27,   tags:[\x27Wife\x27],       title:\x27Book a date with {{partner}} before things get busy\x27 },",
        "{ phase:\x27first\x27, cat:\x27Partner\x27,   tags:[\x27Wife\x27,\x27has-partner\x27], title:\x27Book a date with {{partner}} before things get busy\x27 },"
    ),
    # third trimester
    (
        "{ phase:\x27third\x27, cat:\x27Logistics\x27, tags:[\x27Wife\x27],       title:\"Pack hospital bags \xd7 3: yours, {{partner}}\x27s, and baby\x27s\" },",
        "{ phase:\x27third\x27, cat:\x27Logistics\x27, tags:[\x27Wife\x27,\x27has-partner\x27], title:\"Pack hospital bags \xd7 3: yours, {{partner}}\x27s, and baby\x27s\" },"
    ),
    (
        "{ phase:\x27third\x27, cat:\x27Emotional\x27, tags:[\x27GC\x27,\x27Wife\x27],  title:\x27Walk through the delivery-day plan with {{GC}}, agency, and {{partner}}\x27 },",
        "{ phase:\x27third\x27, cat:\x27Emotional\x27, tags:[\x27GC\x27,\x27Wife\x27,\x27has-partner\x27], title:\x27Walk through the delivery-day plan with {{GC}}, agency, and {{partner}}\x27 },"
    ),
    (
        "{ phase:\x27third\x27, cat:\x27Emotional\x27, tags:[\x27GC\x27],         title:\x27Confirm the delivery room guest list with {{GC}} and the hospital\x27 },",
        "{ phase:\x27third\x27, cat:\x27Emotional\x27, tags:[\x27GC\x27,\x27in-room-birth\x27], title:\x27Confirm the delivery room guest list with {{GC}} and the hospital\x27 },"
    ),
    # final
    (
        "{ phase:\x27final\x27, cat:\x27Partner\x27,   tags:[\x27Wife\x27], title:\"Plan a last couple\x27s getaway before delivery — babymoon, IP edition\" },",
        "{ phase:\x27final\x27, cat:\x27Partner\x27,   tags:[\x27Wife\x27,\x27has-partner\x27], title:\"Plan a last couple\x27s getaway before delivery — babymoon, IP edition\" },"
    ),
    # post-birth
    (
        "{ phase:\x27post-birth\x27, cat:\x27Partner\x27,   tags:[\x27Wife\x27], title:\x27Establish a shift schedule with {{partner}} for the first two weeks\x27 },",
        "{ phase:\x27post-birth\x27, cat:\x27Partner\x27,   tags:[\x27Wife\x27,\x27has-partner\x27], title:\x27Establish a shift schedule with {{partner}} for the first two weeks\x27 },"
    ),
    (
        "{ phase:\x27post-birth\x27, cat:\x27Partner\x27,   tags:[\x27Wife\x27], title:\x27Check in on {{partner}}: grief, joy, or both are valid\x27 },",
        "{ phase:\x27post-birth\x27, cat:\x27Partner\x27,   tags:[\x27Wife\x27,\x27has-partner\x27], title:\x27Check in on {{partner}}: grief, joy, or both are valid\x27 },"
    ),
]
for i, (old, new) in enumerate(TASK_PATCHES):
    assert old in src, f"Task patch {i+4} anchor not found: {old[:80]}"
    src = src.replace(old, new, 1)
print(f'  - SEED_TASKS: {len(TASK_PATCHES)} task tag additions (has-partner, in-room-birth)')

# ── 15. New task: prior-loss (pre-transfer, before "Save fertility clinic...") ─
OLD15 = (
    "  { phase:\x27pre-transfer\x27, cat:\x27Logistics\x27,  tags:[],             "
    "title:\x27Save fertility clinic, agency coordinator, and attorney numbers in your phone\x27 },"
)
NEW15 = (
    "  { phase:\x27pre-transfer\x27, cat:\x27Emotional\x27,  tags:[\x27prior-loss\x27], "
    "title:\x27Connect with a loss-informed therapist before transfer — carrying grief into hope takes its own kind of support\x27 },\n"
    "  { phase:\x27pre-transfer\x27, cat:\x27Logistics\x27,  tags:[],             "
    "title:\x27Save fertility clinic, agency coordinator, and attorney numbers in your phone\x27 },"
)
assert OLD15 in src, "prior-loss task insertion anchor not found"
src = src.replace(OLD15, NEW15, 1)
print('  - SEED_TASKS: new prior-loss task added (pre-transfer)')

# ── 16. New task: remote-gc (final weeks, before "Prioritize sleep") ──────────
OLD16 = (
    "  { phase:\x27final\x27, cat:\x27Self\x27,      tags:[],       title:\x27Prioritize sleep\x27 },"
)
NEW16 = (
    "  { phase:\x27final\x27, cat:\x27Logistics\x27, tags:[\x27GC\x27,\x27remote-gc\x27], "
    "title:\x27Confirm your travel logistics for birth — flights, accommodation, and a plan if {{GC}} goes early\x27 },\n"
    "  { phase:\x27final\x27, cat:\x27Self\x27,      tags:[],       title:\x27Prioritize sleep\x27 },"
)
assert OLD16 in src, "remote-gc task insertion anchor not found"
src = src.replace(OLD16, NEW16, 1)
print('  - SEED_TASKS: new remote-gc task added (final weeks)')

# ── 17. Add SITUATION_JOURNAL_PROMPTS + getSituationPrompts() ─────────────────
OLD17 = "};\n\nconst JOURNAL_EVERGREEN = ["
NEW17 = (
    "};\n\n"
    "const SITUATION_JOURNAL_PROMPTS = {\n"
    "  \x27remote-gc\x27: [\n"
    "    \"Your GC is carrying your child from another city. Write about what the distance feels like.\",\n"
    "    \"What does it mean to trust someone so completely when they\x27re so far away?\",\n"
    "  ],\n"
    "  \x27prior-loss\x27: [\n"
    "    \"You\x27ve carried loss into this. What does hope feel like alongside that weight?\",\n"
    "    \"Write about what this pregnancy means in the context of what came before.\",\n"
    "  ],\n"
    "  \x27first-time-parent\x27: [\n"
    "    \"Write about the first time it really hit you that you were going to be a dad.\",\n"
    "    \"What kind of father do you want to be? Specific and honest, not aspirational.\",\n"
    "  ],\n"
    "  \x27has-partner\x27: [\n"
    "    \"Write to your partner about what this journey has meant to your relationship.\",\n"
    "    \"What has this done to the two of you — the hard parts, and the parts that brought you closer?\",\n"
    "  ],\n"
    "};\n\n"
    "function getSituationPrompts(){\n"
    "  const s=state.settings;\n"
    "  const prompts=[];\n"
    "  if(s.gcDistance===\x27different-state\x27)prompts.push(...(SITUATION_JOURNAL_PROMPTS[\x27remote-gc\x27]||[]));\n"
    "  if(s.priorLoss===true)prompts.push(...(SITUATION_JOURNAL_PROMPTS[\x27prior-loss\x27]||[]));\n"
    "  if(s.isFirstTimeParent===true)prompts.push(...(SITUATION_JOURNAL_PROMPTS[\x27first-time-parent\x27]||[]));\n"
    "  if(s.isPartnered===true)prompts.push(...(SITUATION_JOURNAL_PROMPTS[\x27has-partner\x27]||[]));\n"
    "  return prompts;\n"
    "}\n\n"
    "const JOURNAL_EVERGREEN = ["
)
assert OLD17 in src, "JOURNAL_PROMPTS end anchor not found"
src = src.replace(OLD17, NEW17, 1)
print('  - SITUATION_JOURNAL_PROMPTS + getSituationPrompts() added')

# ── 18. Include situation prompts in allPrompts pool ─────────────────────────
OLD18 = "  const allPrompts = [...phasePrompts,...JOURNAL_EVERGREEN];"
NEW18 = "  const allPrompts = [...phasePrompts,...getSituationPrompts(),...JOURNAL_EVERGREEN];"
assert OLD18 in src, "allPrompts line anchor not found"
src = src.replace(OLD18, NEW18, 1)
print('  - Journal allPrompts: situation-specific prompts included')

# ── Write output ──────────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_1.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"const CACHE_NAME = 'daddy-duty-[^']*'",
                "const CACHE_NAME = 'daddy-duty-v5-1'", sw_src)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── JS syntax check ───────────────────────────────────────────────────────────
node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_1.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_1.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── Sanity assertions ─────────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.1 \xb7 cloud sync" in content, "version string missing"
assert "appVersion:\x27v5.1\x27" in content, "appVersion missing"
assert "situationSuppressed" in content, "situationSuppressed missing"
assert "has-partner" in content, "has-partner tag missing"
assert "in-room-birth" in content, "in-room-birth tag missing"
assert "prior-loss" in content, "prior-loss tag missing"
assert "remote-gc" in content, "remote-gc tag missing"
assert "SITUATION_JOURNAL_PROMPTS" in content, "SITUATION_JOURNAL_PROMPTS missing"
assert "getSituationPrompts" in content, "getSituationPrompts missing"
assert "getSituationPrompts()" in content, "getSituationPrompts() call missing"
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_1.html')
