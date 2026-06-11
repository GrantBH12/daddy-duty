#!/usr/bin/env python3
"""build_v5_9.py — v5.9: Launch blockers patch
Source: daddy-duty-v5_8.html -> daddy-duty-v5_9.html

Changes:
  1. Version bump v5.8 → v5.9
  2. Auth model: remove "New here" sign-up tab, replace with invite-only / Request Access panel
  3. Remove sendMagicLinkNew() sign-up JS and setAuthTab() toggle logic
  4. Update Terms of Use to accurately reflect private beta / invite-only status
  5. Add .lib-card-disclaimer CSS
  6. Inject disclaimer line into renderLibCard() card HTML
  7. Inject disclaimer line into Library browse card HTML (line ~5606)
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

src = open('daddy-duty-v5_8.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials ─────────────────────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version ─────────────────────────────────────────────────────────────────
OLD2a = "v5.8 \xb7 cloud sync"
NEW2a = "v5.9 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:'v5.8'"
NEW2b = "appVersion:'v5.9'"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.8 → v5.9')

# ── 3. Auth UI: remove "New here" tab, add "Request Access" panel ──────────────
OLD3 = """    <div class="auth-tabs">
      <button class="auth-tab active" id="auth-tab-return" onclick="setAuthTab('return')">Already have an account</button>
      <button class="auth-tab" id="auth-tab-new" onclick="setAuthTab('new')">New here</button>
    </div>
    <div id="auth-panel-return">
      <p class="auth-sub">Enter the email you signed up with. We&#8217;ll send a link &#8212; your data will be waiting.</p>
      <input type="email" id="auth-email" class="auth-input" placeholder="your@email.com"
             onkeydown="if(event.key==='Enter')sendMagicLink()" autocomplete="email" />
      <button class="auth-btn" id="auth-submit-btn" onclick="sendMagicLink()">Send sign-in link &rarr;</button>
      <div class="auth-msg" id="auth-msg"></div>
    </div>
    <div id="auth-panel-new" style="display:none;">
      <p class="auth-sub">Create your account with an email. No password needed.</p>
      <input type="email" id="auth-email-new" class="auth-input" placeholder="your@email.com"
             onkeydown="if(event.key==='Enter')sendMagicLinkNew()" autocomplete="email" />
      <button class="auth-btn" id="auth-submit-new" onclick="sendMagicLinkNew()">Create account &rarr;</button>
      <div class="auth-msg" id="auth-msg-new"></div>
    </div>"""

NEW3 = """    <div id="auth-panel-return">
      <p class="auth-sub">Enter the email you signed up with. We&#8217;ll send a link &#8212; your data will be waiting.</p>
      <input type="email" id="auth-email" class="auth-input" placeholder="your@email.com"
             onkeydown="if(event.key==='Enter')sendMagicLink()" autocomplete="email" />
      <button class="auth-btn" id="auth-submit-btn" onclick="sendMagicLink()">Send sign-in link &rarr;</button>
      <div class="auth-msg" id="auth-msg"></div>
    </div>
    <div class="auth-request-access">
      <p class="auth-request-label">New here?</p>
      <p class="auth-request-sub">Daddy Duty is currently in private beta &#8212; access is by invitation only.</p>
      <a class="auth-request-link" href="mailto:granthansell@gmail.com?subject=Daddy%20Duty%20access%20request">Request access &rarr;</a>
    </div>"""

assert OLD3 in src, "auth tab HTML not found"
src = src.replace(OLD3, NEW3, 1)
print('  - Auth UI: removed "New here" tab, added Request Access panel')

# ── 4. Remove setAuthTab() JS (no longer needed) ──────────────────────────────
OLD4 = """function setAuthTab(tab){
  document.getElementById('auth-panel-return').style.display=tab==='return'?'':'none';
  document.getElementById('auth-panel-new').style.display=tab==='new'?'':'none';
  document.getElementById('auth-tab-return').classList.toggle('active',tab==='return');
  document.getElementById('auth-tab-new').classList.toggle('active',tab==='new');
}

async function sendMagicLinkNew(){
  const email=(document.getElementById('auth-email-new')?.value||'').trim();
  await _sendOtp(email,'auth-msg-new','auth-submit-new');
}

"""

NEW4 = ""

assert OLD4 in src, "setAuthTab/sendMagicLinkNew JS not found"
src = src.replace(OLD4, NEW4, 1)
print('  - Removed setAuthTab() and sendMagicLinkNew() JS')

# ── 5. Update Terms of Use "invite-only" line ──────────────────────────────────
OLD5 = "        <li><strong>Private &amp; invite-only.</strong> This app is currently for personally invited users only. Sharing access is not permitted without permission.</li>"
NEW5 = "        <li><strong>Private beta.</strong> Daddy Duty is currently in private beta. Access is by invitation only. To request access, email <strong>granthansell@gmail.com</strong>.</li>"

assert OLD5 in src, "Terms invite-only line not found"
src = src.replace(OLD5, NEW5, 1)
print('  - Terms of Use: updated to accurately reflect private beta / invite-only')

# ── 6. Add CSS for auth request-access panel + lib-card-disclaimer ─────────────
# Insert after the last existing .auth- CSS rule block (near auth-tab styles)
OLD6 = "  .auth-tab.active{background:var(--cream,#f5ede0);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.08);}"
NEW6 = """  .auth-tab.active{background:var(--cream,#f5ede0);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.08);}
  .auth-request-access{margin-top:20px;padding-top:18px;border-top:1px solid var(--cream-deeper,#e0d2b6);text-align:center;}
  .auth-request-label{font-size:12px;font-weight:600;color:var(--ink);letter-spacing:.03em;margin-bottom:5px;}
  .auth-request-sub{font-size:11px;color:var(--ink-muted,#756d61);line-height:1.55;margin-bottom:12px;}
  .auth-request-link{font-size:12px;color:var(--terra,#c97156);font-weight:500;letter-spacing:.02em;text-decoration:none;}
  .auth-request-link:hover{text-decoration:underline;}
  .lib-card-disclaimer{font-size:11px;color:rgba(245,237,224,.4);margin-top:14px;font-style:italic;line-height:1.5;}"""

assert OLD6 in src, "auth-tab CSS not found"
src = src.replace(OLD6, NEW6, 1)
print('  - CSS: added .auth-request-access styles and .lib-card-disclaimer')

# ── 7. Inject disclaimer into renderLibCard() HTML ────────────────────────────
OLD7 = """    <p class="lib-card-body">${card.body}</p>
    <div class="lib-card-actions">
      ${isToday ? `<button class="lib-card-btn primary${alreadyRead?' done':''}" onclick="markLibCardRead('${card.id}')">${alreadyRead ? 'Read ✦' : 'Mark as read · +10 XP'}</button>` : ''}
      <button class="lib-card-btn ghost" onclick="reflectInJournal()">Reflect in journal</button>
    </div>
  </div>`"""

NEW7 = """    <p class="lib-card-body">${card.body}</p>
    <p class="lib-card-disclaimer">For informational purposes only &mdash; not medical advice.</p>
    <div class="lib-card-actions">
      ${isToday ? `<button class="lib-card-btn primary${alreadyRead?' done':''}" onclick="markLibCardRead('${card.id}')">${alreadyRead ? 'Read ✦' : 'Mark as read · +10 XP'}</button>` : ''}
      <button class="lib-card-btn ghost" onclick="reflectInJournal()">Reflect in journal</button>
    </div>
  </div>`"""

assert OLD7 in src, "renderLibCard() card HTML not found"
src = src.replace(OLD7, NEW7, 1)
print('  - renderLibCard(): disclaimer injected after card body')

# ── 8. Inject disclaimer into Library browse card view ────────────────────────
OLD8 = '<p class="lib-card-body">${card.body}</p><div class="lib-card-actions"><button class="lib-card-btn primary${alreadyRead?\' done\':\'\'}" onclick="markLibBrowseCardRead(\'${card.id}\')">${alreadyRead?\'Read \\u2726\':\'Mark as read \\u00b7 +10 XP\'}</button><button class="lib-card-btn ghost" onclick="reflectInJournal()">Reflect in journal</button></div></div>`'
NEW8 = '<p class="lib-card-body">${card.body}</p><p class="lib-card-disclaimer">For informational purposes only &mdash; not medical advice.</p><div class="lib-card-actions"><button class="lib-card-btn primary${alreadyRead?\' done\':\'\'}" onclick="markLibBrowseCardRead(\'${card.id}\')">${alreadyRead?\'Read \\u2726\':\'Mark as read \\u00b7 +10 XP\'}</button><button class="lib-card-btn ghost" onclick="reflectInJournal()">Reflect in journal</button></div></div>`'

assert OLD8 in src, "Library browse card HTML not found"
src = src.replace(OLD8, NEW8, 1)
print('  - Library browse card: disclaimer injected after card body')

# ── 9. Write output ────────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_9.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"(const CACHE\s*=\s*'daddy-duty-)[^']*(')", r'\1v5-9\2', sw_src)
sw_new = re.sub(r"(cache key: daddy-duty-)[^\s*]*", r'\1v5-9', sw_new)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── 10. JS syntax check ──────────────────────────────────────────────────────
node = '/opt/homebrew/bin/node'
if not os.path.exists(node):
    node = '/usr/local/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_9.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_9.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── 11. Sanity assertions ────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.9 \xb7 cloud sync"             in content, "version string missing"
assert "appVersion:'v5.9'"                in content, "appVersion missing"
assert "window.confirm("             not in content, "window.confirm() regression"
assert "auth-tab-new"                not in content, 'auth-tab-new still present'
assert "sendMagicLinkNew"            not in content, 'sendMagicLinkNew() still present'
assert "auth-panel-new"              not in content, 'auth-panel-new still present'
assert "Request access"                   in content, 'Request access panel missing'
assert "private beta"                     in content, 'private beta text missing'
assert "lib-card-disclaimer"              in content, 'disclaimer CSS/class missing'
assert "not medical advice"               in content, 'disclaimer text missing'
assert content.count("not medical advice") >= 2, 'disclaimer should appear in 2 card views'
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_9.html')
print()
print('⚠️  Reminder: Go to Supabase Dashboard → Authentication → Settings')
print('   and disable new user sign-ups to enforce invite-only at the server level.')
