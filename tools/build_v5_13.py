#!/usr/bin/env python3
"""build_v5_13.py — v5.13: The Surfacing Engine
Source: daddy-duty-v5_12.html -> daddy-duty-v5_13.html

Changes:
  1. Version bump v5.12 → v5.13
  2. JS: add buildSurfaceContext() — shared signal context for all scorers
  3. JS: add scoreCard() — composable card scoring function
  4. JS: drawCardForDate() — replace diversity block with scored sort
  5. JS: add scoreQuestion() — composable question scoring function
  6. JS: getNextQuestion() — replace triggered/candidates return with scored sort
  7. JS: add JOURNAL_PROMPTS_BY_TRACK constant
  8. JS: renderNudge() — thematic journal prompt (track-matched) + resolveTokens
  9. JS: renderNudge() — add overdue task nudge condition (priority 3)
 10. JS: renderLibBrowse() — sort unread first, scored; read second
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

src = open('daddy-duty-v5_12.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials ─────────────────────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version ─────────────────────────────────────────────────────────────────
OLD2a = "v5.12 \xb7 cloud sync"
NEW2a = "v5.13 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:'v5.12'"
NEW2b = "appVersion:'v5.13'"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.12 → v5.13')

# ── 3. JS: add buildSurfaceContext() before getPhasePool() ─────────────────────
OLD3 = "function getPhasePool(phase) {"
NEW3 = """\
function buildSurfaceContext() {
  var today = todayStr();
  var todayCardId = state.dailyCardLog && state.dailyCardLog[today];
  var todayCard = todayCardId ? LIBRARY_CARDS.find(function(c) { return c.id === todayCardId; }) : null;
  var sortedLogDates = Object.keys(state.dailyCardLog || {}).sort();
  // Last 7 calendar days (excluding today) — used for track diversity penalty
  var recentTracks = sortedLogDates.slice(-8, -1).map(function(d) {
    var c = LIBRARY_CARDS.find(function(x) { return x.id === state.dailyCardLog[d]; });
    return c ? c.track : null;
  }).filter(Boolean);
  var settings = state.settings || {};
  // Which setup fields are still null — each null field = personalization filters inactive
  var pendingSetupFields = {
    gcDistance:        settings.gcDistance        === null || settings.gcDistance        === undefined,
    isFirstTimeParent: settings.isFirstTimeParent === null || settings.isFirstTimeParent === undefined,
    priorLoss:         settings.priorLoss         === null || settings.priorLoss         === undefined,
    isPartnered:       settings.isPartnered       === null || settings.isPartnered       === undefined,
    birthAttendance:   settings.birthAttendance   === null || settings.birthAttendance   === undefined,
  };
  var phase = getCurrentLibPhase();
  var week = getGestationalWeek();
  var readIds = state.readCardIds || [];
  var todayCardTags = (todayCard && todayCard.tags) || [];
  var milSt = state.milestoneStatus || {};
  // Milestone tags the user is actively working on — used for card affinity boost
  var inProgressMilestoneTags = Object.entries(milSt)
    .filter(function(e) { return e[1] === 'in-progress'; })
    .map(function(e) { return e[0]; });
  // Overdue task count — used for nudge priority
  var currentPhase = getCurrentPhase();
  var now = new Date();
  var overdueCount = (state.tasks || []).filter(function(t) {
    return t.phase === currentPhase && t.status !== 'done' && t.dueDate &&
           Math.ceil((new Date(t.dueDate) - now) / 86400000) < 0;
  }).length;
  return {
    today: today, phase: phase, week: week, readIds: readIds,
    recentTracks: recentTracks, settings: settings,
    pendingSetupFields: pendingSetupFields,
    todayCard: todayCard, todayCardTags: todayCardTags,
    inProgressMilestoneTags: inProgressMilestoneTags,
    overdueCount: overdueCount
  };
}

function getPhasePool(phase) {"""
assert OLD3 in src, "getPhasePool() not found"
src = src.replace(OLD3, NEW3, 1)
print('  - JS: added buildSurfaceContext()')

# ── 4. JS: add scoreCard() before drawCardForDate() ────────────────────────────
OLD4 = "function drawCardForDate(dateStr) {"
NEW4 = """\
function scoreCard(card, ctx) {
  var score = 0;
  var week = ctx.week;
  var readIds = ctx.readIds;
  var recentTracks = ctx.recentTracks;
  var inProgressMilestoneTags = ctx.inProgressMilestoneTags;
  // Week-range match: strongest signal — card is timely right now
  if (card.weekRange && week !== null &&
      week >= card.weekRange[0] && week <= card.weekRange[1]) score += 100;
  // Unread: always prefer unread over read cards
  if (!readIds.includes(card.id)) score += 30;
  // Track diversity penalty: scales naturally as library grows
  var recentRepeat = recentTracks.filter(function(t) { return t === card.track; }).length;
  score -= recentRepeat * 15;
  // Milestone affinity: boost cards relevant to milestones user is actively working on
  var cardMilTags = (card.tags || []).filter(function(t) { return MILESTONE_TAGS.includes(t); });
  if (cardMilTags.some(function(t) { return inProgressMilestoneTags.includes(t); })) score += 25;
  return score;
}

function drawCardForDate(dateStr) {"""
assert OLD4 in src, "drawCardForDate() not found"
src = src.replace(OLD4, NEW4, 1)
print('  - JS: added scoreCard()')

# ── 5. JS: drawCardForDate() — replace diversity block with scored sort ─────────
OLD5 = """\
  const unread = pool.filter(c => !readIds.includes(c.id));
  if (unread.length) {
    const sortedDates = Object.keys(state.dailyCardLog).sort();
    const prevDate = sortedDates.length >= 2 ? sortedDates[sortedDates.length - 2] : null;
    const prevCard = prevDate ? LIBRARY_CARDS.find(c => c.id === state.dailyCardLog[prevDate]) : null;
    const diverse = prevCard ? unread.filter(c => c.track !== prevCard.track) : unread;
    const best = diverse.length ? diverse[0] : unread[0];
    state.dailyCardLog[dateStr] = best.id; save(); return best;
  }"""
NEW5 = """\
  const unread = pool.filter(c => !readIds.includes(c.id));
  if (unread.length) {
    const ctx = buildSurfaceContext();
    const best = unread.slice().sort(function(a, b) { return scoreCard(b, ctx) - scoreCard(a, ctx); })[0];
    state.dailyCardLog[dateStr] = best.id; save(); return best;
  }"""
assert OLD5 in src, "drawCardForDate unread block not found"
src = src.replace(OLD5, NEW5, 1)
print('  - JS: drawCardForDate() — scored sort replaces diversity block')

# ── 6. JS: add scoreQuestion() before getNextQuestion() ───────────────────────
OLD6 = "function getNextQuestion() {"
NEW6 = """\
function scoreQuestion(q, ctx) {
  var score = 0;
  var pendingSetupFields = ctx.pendingSetupFields;
  var todayCardTags = ctx.todayCardTags;
  // Setup questions with null state: top priority — each one unlocks a pool filter
  var setupFieldMap = {
    'q-001': 'gcDistance',
    'q-002': 'isFirstTimeParent',
    'q-003': 'priorLoss',
    'q-005': 'isPartnered',
    'q-006': 'birthAttendance',
  };
  var field = setupFieldMap[q.id];
  if (field && pendingSetupFields[field]) score += 100;
  // Triggered by today's card tag: thematically relevant
  if (q.triggeredByTag && todayCardTags.includes(q.triggeredByTag)) score += 50;
  return score;
}

function getNextQuestion() {"""
assert OLD6 in src, "getNextQuestion() not found"
src = src.replace(OLD6, NEW6, 1)
print('  - JS: added scoreQuestion()')

# ── 7. JS: getNextQuestion() — replace final return with scored sort ──────────
OLD7 = """\
  // Prioritize: triggered by today's card tag
  const triggered = candidates.filter(q => q.triggeredByTag && lastCardTags.includes(q.triggeredByTag));
  return triggered[0] || candidates[0] || null;
}"""
NEW7 = """\
  // Score candidates: setup questions with null state beat milestone check-ins;
  // tag-triggered questions beat generic phase questions.
  const qCtx = buildSurfaceContext();
  const scored = candidates.slice().sort(function(a, b) { return scoreQuestion(b, qCtx) - scoreQuestion(a, qCtx); });
  return scored[0] || null;
}"""
assert OLD7 in src, "getNextQuestion final return not found"
src = src.replace(OLD7, NEW7, 1)
print('  - JS: getNextQuestion() — scored sort for question selection')

# ── 8. JS: add JOURNAL_PROMPTS_BY_TRACK after JOURNAL_PROMPTS_SHORT ───────────
OLD8 = "\nfunction daysSinceLastJournal() {"
NEW8 = """
const JOURNAL_PROMPTS_BY_TRACK = {
  'Surrogacy':     ['What do you want {{GC}} to know about how grateful you are right now?',
                    'How has your relationship with {{GC}} evolved from where it started?',
                    'What part of this surrogacy journey has surprised you most?'],
  'Partnership':   ['What\\'s one thing {{partner}} has done recently that you want to remember?',
                    'Where are you and {{partner}} most aligned right now — and where are you diverging?'],
  'Mental Health': ['What are you carrying right now that you haven\\'t said out loud?',
                    'What would you tell yourself six months ago about the anxiety you\\'re feeling now?'],
  'Fatherhood':    ['What kind of father do you want to be? Write one specific thing, not a value.',
                    'What does becoming a dad mean to you this week?'],
  'Practical':     ['What\\'s the one prep task that keeps getting bumped — and why?',
                    'What would be different if you did the hard thing on your list this week?'],
  'Medical':       ['How are you processing the medical side of this right now?',
                    'Write one sentence to your future self about this moment in the process.'],
  'Legal':         ['What feels unresolved legally — and does it need action or does it need acceptance?',
                    'Write down one thing about the legal side you want to understand better.'],
  'Bonding':       ['Write one thing you already know about the kind of relationship you want with your kid.',
                    'What does it feel like to be so close to meeting them?'],
};

function daysSinceLastJournal() {"""
assert OLD8 in src, "daysSinceLastJournal() anchor not found"
src = src.replace(OLD8, NEW8, 1)
print('  - JS: added JOURNAL_PROMPTS_BY_TRACK')

# ── 9. JS: renderNudge() — thematic journal prompt via track lookup ─────────────
OLD9 = "    const prompt = JOURNAL_PROMPTS_SHORT[Math.floor(Date.now() / 86400000) % JOURNAL_PROMPTS_SHORT.length];"
NEW9 = """\
    const nudgeCard = getTodayCard();
    const trackKey = nudgeCard && nudgeCard.track;
    const trackPrompts = trackKey && JOURNAL_PROMPTS_BY_TRACK[trackKey];
    const rawPrompt = trackPrompts
      ? trackPrompts[Math.floor(Date.now() / 86400000) % trackPrompts.length]
      : JOURNAL_PROMPTS_SHORT[Math.floor(Date.now() / 86400000) % JOURNAL_PROMPTS_SHORT.length];
    const prompt = resolveTokens(rawPrompt);"""
assert OLD9 in src, "journal prompt line in renderNudge() not found"
src = src.replace(OLD9, NEW9, 1)
print('  - JS: renderNudge() — thematic journal prompt (track-matched + resolveTokens)')

# ── 10. JS: renderNudge() — add overdue task nudge (priority 3) ────────────────
OLD10 = "  const isPartnerRole=((state.settings||{}).userRole==='partner');"
NEW10 = """\
  // Overdue task nudge: surfaces between journal nudge and settings nudge
  const nCtx = buildSurfaceContext();
  if (nCtx.overdueCount > 0) {
    const plural = nCtx.overdueCount === 1 ? 'task is' : 'tasks are';
    wrap.innerHTML = `<div class="nudge" onclick="go('tasks')">
      <div class="nudge-icon">⚠</div>
      <div>${nCtx.overdueCount} ${plural} overdue — worth a look today.</div>
      <div class="nudge-arrow">→</div>
    </div>`;
    return;
  }
  const isPartnerRole=((state.settings||{}).userRole==='partner');"""
assert OLD10 in src, "isPartnerRole line in renderNudge() not found"
src = src.replace(OLD10, NEW10, 1)
print('  - JS: renderNudge() — added overdue task nudge (priority 3)')

# ── 11. JS: renderLibBrowse() — sort unread first, scored within each group ────
OLD11 = """\
  const readIds = state.readCardIds || [];
  stage.innerHTML = `<div class="lib-browse-list">${pool.map(c => {
    const isRead = readIds.includes(c.id);
    return `<div class="lib-browse-row${isRead?' is-read':''}" onclick="libOpenCard('${c.id}')"><span class="lib-browse-track">${c.track}</span><span class="lib-browse-title">${escapeHtml(c.title)}</span>${isRead?'<span class="lib-browse-badge">\\u2713</span>':''}</div>`;
  }).join('')}</div>`;"""
NEW11 = """\
  const readIds = state.readCardIds || [];
  const browseCtx = buildSurfaceContext();
  const sortedPool = pool.slice().sort(function(a, b) {
    const aRead = readIds.includes(a.id);
    const bRead = readIds.includes(b.id);
    if (aRead !== bRead) return aRead ? 1 : -1; // unread cards first
    if (!aRead && !bRead) return scoreCard(b, browseCtx) - scoreCard(a, browseCtx);
    // Both read: most recently shown last (oldest reads sort higher, freshest lower)
    const aDate = Object.keys(state.dailyCardLog || {}).find(function(d) { return state.dailyCardLog[d] === a.id; }) || '';
    const bDate = Object.keys(state.dailyCardLog || {}).find(function(d) { return state.dailyCardLog[d] === b.id; }) || '';
    return bDate.localeCompare(aDate);
  });
  stage.innerHTML = `<div class="lib-browse-list">${sortedPool.map(c => {
    const isRead = readIds.includes(c.id);
    return `<div class="lib-browse-row${isRead?' is-read':''}" onclick="libOpenCard('${c.id}')"><span class="lib-browse-track">${c.track}</span><span class="lib-browse-title">${escapeHtml(c.title)}</span>${isRead?'<span class="lib-browse-badge">\\u2713</span>':''}</div>`;
  }).join('')}</div>`;"""
assert OLD11 in src, "renderLibBrowse() sort block not found"
src = src.replace(OLD11, NEW11, 1)
print('  - JS: renderLibBrowse() — unread first, scored sort')

# ── 12. Write output ───────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_13.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"(const CACHE\s*=\s*'daddy-duty-)[^']*(')", r'\1v5-13\2', sw_src)
sw_new = re.sub(r"(cache key: daddy-duty-)[^\s*]*", r'\1v5-13', sw_new)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── 13. JS syntax check ────────────────────────────────────────────────────────
node = '/opt/homebrew/bin/node'
if not os.path.exists(node):
    node = '/usr/local/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_13.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_13.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── 14. Sanity assertions ──────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.13 \xb7 cloud sync"         in content, "version string missing"
assert "appVersion:'v5.13'"             in content, "appVersion missing"
assert "buildSurfaceContext"            in content, "buildSurfaceContext missing"
assert "scoreCard"                      in content, "scoreCard missing"
assert "scoreQuestion"                  in content, "scoreQuestion missing"
assert "JOURNAL_PROMPTS_BY_TRACK"       in content, "JOURNAL_PROMPTS_BY_TRACK missing"
assert "resolveTokens(rawPrompt)"       in content, "resolveTokens journal prompt missing"
assert "overdueCount"                   in content, "overdueCount nudge missing"
assert "sortedPool"                     in content, "browse sort missing"
assert "window.confirm("          not  in content, "window.confirm() regression"
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_13.html')
