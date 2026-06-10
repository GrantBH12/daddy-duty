#!/usr/bin/env python3
"""build_v5_4.py — v5.4: Unified Today Card (home screen redesign)
Source: daddy-duty-v5_3.html -> daddy-duty-v5_4.html

Replaces three separate home-screen blocks (todays-card, home-nudge-wrap,
countdown-widget) with a single unified .today-card presenting read / journal /
reflect as completable items, with phase + countdown as a footer strip.
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

src = open('daddy-duty-v5_3.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials (always regex) ─────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version ─────────────────────────────────────────────────────────────────
OLD2a = "v5.3 \xb7 cloud sync"
NEW2a = "v5.4 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:'v5.3'"
NEW2b = "appVersion:'v5.4'"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.3 → v5.4')

# ── 3. HTML: Replace 3 old blocks with unified today-card ─────────────────────
# Anchor: unique start/end markers around the three blocks
OLD3_START = '    <div class="todays-card" id="home-card-wrap">'
OLD3_END   = '        <button class="cw-settings-btn" onclick="openSettings()">⚙ Edit dates</button>\n      </div>\n    </div>'

assert OLD3_START in src, "todays-card block not found"
assert OLD3_END   in src, "countdown-widget end not found"

s_start = src.index(OLD3_START)
s_end   = src.index(OLD3_END) + len(OLD3_END)
old_html = src[s_start:s_end]

NEW3 = """\
    <div class="today-card" id="today-card">

      <!-- Header -->
      <div class="today-card-head">
        <div class="today-card-eyebrow">
          <span class="today-eyebrow-dot" id="today-eyebrow-dot"></span>
          Today
        </div>
        <div class="today-card-meta">
          <span class="today-card-date" id="today-card-date"></span>
          <span class="today-done-badge" id="today-done-badge">0 / 3</span>
        </div>
      </div>

      <!-- Items -->
      <div class="today-card-items">

        <!-- Item 1: Read -->
        <div class="today-item" id="today-item-reading" onclick="todayToggleExpand('reading')">
          <div class="today-type-dot terra" id="today-dot-reading"></div>
          <div class="today-item-body">
            <div class="today-item-label" id="today-reading-label">Loading…</div>
            <div class="today-item-pills" id="today-reading-pills"></div>
            <div class="today-item-expand open" id="today-exp-reading">
              <div class="today-expand-inner">
                <p class="today-preview-text" id="today-reading-preview"></p>
                <button class="today-item-cta primary" id="today-read-btn" onclick="event.stopPropagation(); markCardRead()">\
Read today →</button>
                <button class="today-item-cta" style="margin-left:6px;" onclick="event.stopPropagation(); go('library')">Full library</button>
              </div>
            </div>
          </div>
          <button class="today-check-circle" id="today-check-reading"
            onclick="event.stopPropagation(); todayMarkDone('reading')"
            aria-label="Mark reading done">
            <svg width="11" height="9" viewBox="0 0 11 9" fill="none">
              <path d="M1 4.5L4 7.5L10 1.5" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

        <!-- Item 2: Journal -->
        <div class="today-item" id="today-item-journal" onclick="todayToggleExpand('journal')">
          <div class="today-type-dot honey"></div>
          <div class="today-item-body">
            <div class="today-item-label">Write in your journal</div>
            <div class="today-item-sub" id="today-journal-prompt"></div>
            <div class="today-item-expand" id="today-exp-journal">
              <div class="today-expand-inner">
                <button class="today-item-cta" onclick="event.stopPropagation(); reflectInJournal()">Open journal →</button>
              </div>
            </div>
          </div>
          <button class="today-check-circle" id="today-check-journal"
            onclick="event.stopPropagation(); todayMarkDone('journal')"
            aria-label="Mark journal done">
            <svg width="11" height="9" viewBox="0 0 11 9" fill="none">
              <path d="M1 4.5L4 7.5L10 1.5" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

        <!-- Item 3: Daily question -->
        <div class="today-item" id="today-item-question" onclick="todayToggleExpand('question')">
          <div class="today-type-dot sage"></div>
          <div class="today-item-body" id="today-question-body">
            <!-- populated by renderTodayQuestion() -->
          </div>
          <button class="today-check-circle" id="today-check-question"
            onclick="event.stopPropagation(); todayMarkDone('question')"
            aria-label="Mark question done">
            <svg width="11" height="9" viewBox="0 0 11 9" fill="none">
              <path d="M1 4.5L4 7.5L10 1.5" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

      </div><!-- /today-card-items -->

      <!-- Phase footer -->
      <div class="today-card-footer">
        <div class="today-footer-row1">
          <div class="today-phase-dot"></div>
          <span class="today-phase-name" id="today-phase-name"></span>
          <span class="today-days-num" id="today-days-num">—<span class="today-days-unit">days</span></span>
        </div>
        <div class="today-footer-row2">
          <div class="today-mini-track">
            <div class="today-mini-bar" id="today-mini-bar"></div>
          </div>
          <span class="today-prog-label" id="today-prog-label"></span>
        </div>
        <button class="today-edit-btn" onclick="openSettings()">⚙ Edit dates</button>
      </div>

      <!-- Streak -->
      <div class="today-streak-row" id="today-streak-row"></div>

    </div><!-- /today-card -->"""

src = src[:s_start] + NEW3 + src[s_end:]
print('  - HTML: 3 old blocks → unified today-card')

# ── 4. CSS: Add today-card styles after last </style> ──────────────────────────
OLD4 = '</style>\n<link rel="icon"'
assert OLD4 in src, "CSS insertion anchor not found"

TODAY_CSS = """
<style id="today-card-styles">
/* ─────────────────────────────────────────────────────────
   TODAY CARD — unified home hero
───────────────────────────────────────────────────────── */

.today-card {
  max-width: 720px;
  margin: 0 auto 40px;
  background: var(--ink);
  border-radius: var(--r-xl);
  box-shadow: 0 12px 40px rgba(42,38,32,.18), 0 2px 6px rgba(42,38,32,.1);
  position: relative;
  overflow: hidden;
}
.today-card::before {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse at 85% 0%, rgba(201,113,86,.17), transparent 52%),
    radial-gradient(ellipse at 10% 100%, rgba(122,139,107,.08), transparent 45%);
  pointer-events: none;
}
.today-card-head {
  padding: 20px 22px 0;
  display: flex; align-items: center; justify-content: space-between;
  position: relative;
}
.today-card-eyebrow {
  display: flex; align-items: center; gap: 7px;
  font-family: var(--font-mono);
  font-size: var(--fs-eyebrow);
  letter-spacing: var(--tracking-eyebrow);
  text-transform: uppercase;
  color: var(--terra-soft);
  transition: color 400ms var(--ease-out);
}
.today-eyebrow-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--terra);
  box-shadow: 0 0 0 3px rgba(201,113,86,.22);
  transition: background 400ms, box-shadow 400ms;
  flex-shrink: 0;
}
.today-card-meta {
  display: flex; align-items: center; gap: 10px;
  white-space: nowrap; flex-shrink: 0;
}
.today-card-date {
  font-family: var(--font-mono);
  font-size: 9.5px; letter-spacing: .12em; text-transform: uppercase;
  color: rgba(245,237,224,.3);
  white-space: nowrap;
}
.today-done-badge {
  font-family: var(--font-mono);
  font-size: 9.5px; color: rgba(245,237,224,.3);
  letter-spacing: .06em;
  transition: color 400ms var(--ease-out);
  white-space: nowrap;
}
.today-done-badge.complete { color: var(--sage-soft); }
.today-card-items { padding: 14px 22px 0; }
.today-item {
  display: grid;
  grid-template-columns: 10px 1fr 26px;
  gap: 12px;
  align-items: start;
  padding: 14px 0;
  border-bottom: 1px solid rgba(245,237,224,.09);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  transition: opacity var(--dur-fast);
}
.today-item:last-child { border-bottom: none; }
.today-item:active     { opacity: .8; }
.today-type-dot {
  width: 8px; height: 8px; border-radius: 50%;
  margin-top: 5px; flex-shrink: 0;
  transition: background var(--dur-base) var(--ease-out), box-shadow var(--dur-base) var(--ease-out);
}
.today-type-dot.terra { background: var(--terra);  box-shadow: 0 0 0 2.5px rgba(201,113,86,.22); }
.today-type-dot.honey { background: var(--honey);  box-shadow: 0 0 0 2.5px rgba(232,181,71,.22); }
.today-type-dot.sage  { background: var(--sage);   box-shadow: 0 0 0 2.5px rgba(122,139,107,.22); }
.today-item-body  { min-width: 0; }
.today-item-label {
  font-family: var(--font-display);
  font-size: 15.5px; font-weight: 400;
  color: var(--cream); line-height: 1.25;
  letter-spacing: -.01em;
  transition: opacity var(--dur-base) var(--ease-out);
}
#today-item-reading .today-item-label { font-size: 17px; }
.today-item-pills {
  display: flex; align-items: center; gap: 5px;
  margin-top: 5px; flex-wrap: nowrap;
}
.today-track-pill {
  font-family: var(--font-mono);
  font-size: 8.5px; letter-spacing: .14em; text-transform: uppercase;
  padding: 2px 7px; border-radius: var(--r-pill);
  font-weight: 500; white-space: nowrap;
}
.today-track-pill.terra  { background: rgba(201,113,86,.2);   color: var(--terra-soft); }
.today-track-pill.status { background: rgba(245,237,224,.08); color: rgba(245,237,224,.45); }
.today-item-sub {
  font-family: var(--font-display);
  font-style: italic;
  font-size: 13px; line-height: 1.5;
  color: rgba(245,237,224,.42);
  margin-top: 5px;
  transition: opacity var(--dur-base);
}
.today-item-expand {
  max-height: 0; overflow: hidden;
  transition: max-height 380ms var(--ease-out);
}
.today-item-expand.open { max-height: 300px; }
.today-expand-inner     { padding-top: 10px; }
.today-preview-text {
  font-size: 13px; line-height: 1.65;
  color: rgba(245,237,224,.48);
  margin-bottom: 11px;
  text-wrap: pretty;
}
.today-item-cta {
  display: inline-flex; align-items: center; gap: 5px;
  font-family: var(--font-body); font-size: 12px; font-weight: 500;
  color: var(--cream);
  background: rgba(245,237,224,.1);
  border: 1px solid rgba(245,237,224,.18);
  border-radius: var(--r-pill);
  padding: 6px 14px;
  cursor: pointer;
  transition: background var(--dur-fast), border-color var(--dur-fast);
  letter-spacing: .01em;
}
.today-item-cta:hover         { background: rgba(245,237,224,.16); border-color: rgba(245,237,224,.28); }
.today-item-cta.primary       { background: var(--terra);          border-color: transparent; }
.today-item-cta.primary:hover { background: var(--terra-deep); }
.today-q-opts { display: flex; flex-direction: column; gap: 6px; }
.today-q-opt {
  text-align: left;
  background: rgba(245,237,224,.06);
  border: 1px solid rgba(245,237,224,.1);
  border-radius: var(--r-sm);
  padding: 9px 13px;
  font-size: 13px; color: rgba(245,237,224,.85);
  cursor: pointer; font-family: var(--font-body);
  line-height: 1.45;
  transition: background var(--dur-fast), border-color var(--dur-fast);
}
.today-q-opt:hover    { background: rgba(245,237,224,.12); border-color: rgba(245,237,224,.2); }
.today-q-opt.selected { background: rgba(92,107,74,.35);   border-color: var(--sage-deep); color: var(--cream); }
.today-check-circle {
  width: 24px; height: 24px; border-radius: 50%;
  border: 1.5px solid rgba(245,237,224,.22);
  background: transparent;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: all var(--dur-base) cubic-bezier(.34,1.56,.64,1);
  margin-top: 1px; flex-shrink: 0;
}
.today-check-circle svg {
  transform: scale(0);
  transition: transform 280ms cubic-bezier(.34,1.56,.64,1);
}
.today-item.done .today-check-circle {
  background: var(--sage-deep);
  border-color: var(--sage-deep);
  box-shadow: 0 0 0 3px rgba(92,107,74,.2);
}
.today-item.done .today-check-circle svg { transform: scale(1); }
.today-item.done .today-item-label       { opacity: .38; }
.today-item.done .today-item-sub         { opacity: .25; }
.today-item.done .today-item-pills       { opacity: .3; }
.today-item.done .today-type-dot         { background: var(--sage-deep) !important; box-shadow: none !important; }
@keyframes today-check-pop {
  0%   { transform: scale(.8); }
  60%  { transform: scale(1.12); }
  100% { transform: scale(1); }
}
.today-check-pop { animation: today-check-pop 320ms cubic-bezier(.34,1.56,.64,1) forwards; }
.today-card-footer {
  margin: 4px 22px 0;
  padding: 14px 0 16px;
  border-top: 1px solid rgba(245,237,224,.09);
}
.today-footer-row1 {
  display: flex; align-items: center; gap: 8px; margin-bottom: 9px;
}
.today-phase-dot {
  width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
  background: var(--sage);
  box-shadow: 0 0 0 3px rgba(122,139,107,.2);
}
.today-phase-name {
  font-family: var(--font-mono);
  font-size: 9px; letter-spacing: .14em; text-transform: uppercase;
  color: rgba(245,237,224,.38);
  flex: 1;
}
.today-days-num {
  font-family: var(--font-display);
  font-weight: 300; font-size: 20px; letter-spacing: -.02em;
  color: rgba(245,237,224,.75); line-height: 1;
  white-space: nowrap;
}
.today-days-unit {
  font-family: var(--font-body);
  font-size: 10px; font-weight: 400;
  color: rgba(245,237,224,.35);
  margin-left: 3px;
}
.today-footer-row2 { display: flex; align-items: center; gap: 8px; }
.today-mini-track {
  flex: 1; height: 3px; border-radius: var(--r-pill);
  background: rgba(245,237,224,.1); overflow: hidden;
}
.today-mini-bar {
  height: 100%; border-radius: var(--r-pill);
  background: var(--sage-deep); width: 0%;
  transition: width 600ms var(--ease-out);
}
.today-prog-label {
  font-family: var(--font-mono);
  font-size: 8.5px; color: rgba(245,237,224,.3);
  letter-spacing: .08em; white-space: nowrap;
}
.today-edit-btn {
  display: block; margin-top: 8px; padding: 0;
  background: none; border: none; cursor: pointer;
  font-family: var(--font-mono); font-size: 8.5px;
  letter-spacing: .12em; text-transform: uppercase;
  color: rgba(245,237,224,.2);
  transition: color var(--dur-fast);
  white-space: nowrap;
}
.today-edit-btn:hover { color: rgba(245,237,224,.45); }
.today-streak-row {
  display: flex; justify-content: center; gap: 7px;
  padding: 0 22px 20px;
}
.today-sdot {
  width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-size: 8.5px;
  background: rgba(245,237,224,.07);
  border: 1.5px solid rgba(245,237,224,.1);
  color: rgba(245,237,224,.28);
  transition: all var(--dur-base) var(--ease-out);
}
.today-sdot.on    { background: var(--terra);  border-color: var(--terra); color: var(--cream); }
.today-sdot.today { background: var(--honey);  border-color: rgba(42,38,32,.4); color: var(--ink); font-weight: 700; }
.today-card.all-done .today-card-eyebrow { color: var(--sage-soft); }
.today-card.all-done .today-eyebrow-dot  { background: var(--sage); box-shadow: 0 0 0 3px rgba(122,139,107,.25); }
.today-card.all-done::before {
  background:
    radial-gradient(ellipse at 85% 0%, rgba(92,107,74,.2), transparent 52%),
    radial-gradient(ellipse at 10% 100%, rgba(92,107,74,.1), transparent 45%);
}
@media (min-width: 640px) {
  .today-card        { border-radius: 26px; }
  .today-card-head   { padding: 24px 28px 0; }
  .today-card-items  { padding: 16px 28px 0; }
  .today-card-footer { margin: 4px 28px 0; padding: 16px 0 18px; }
  .today-streak-row  { padding: 0 28px 22px; }
  .today-item        { padding: 16px 0; }
  .today-item-label  { font-size: 16px; }
  #today-item-reading .today-item-label  { font-size: 18px; }
  #today-item-reading .today-item-expand { max-height: 300px !important; }
  .today-preview-text { font-size: 13.5px; }
  .today-footer-row1  { margin-bottom: 10px; }
  .today-days-num     { font-size: 24px; }
}
</style>"""

src = src.replace(OLD4, '</style>' + TODAY_CSS + '\n<link rel="icon"', 1)
print('  - CSS: today-card styles injected')

# ── 5. JS: Wire renderTodayCard() into renderHomeCard() ────────────────────────
# Add renderTodayCard() as the last call inside renderHomeCard() so every
# existing call site automatically keeps the today card in sync.
OLD5 = '  renderNudge();\n  renderLibHomeProgress();\n  renderDailyQuestion();\n}'
NEW5 = '  renderNudge();\n  renderLibHomeProgress();\n  renderDailyQuestion();\n  renderTodayCard();\n}'
assert OLD5 in src, "end of renderHomeCard not found"
src = src.replace(OLD5, NEW5, 1)
print('  - JS: renderTodayCard() wired into renderHomeCard()')

# ── 6. JS: Add todayCardState + all renderToday* functions ────────────────────
# Insert after renderHomeCard()'s closing brace, before the NUDGE ENGINE comment
NUDGE_ENGINE_ANCHOR = '\n\n/* ── NUDGE ENGINE ── */'
assert NUDGE_ENGINE_ANCHOR in src, "NUDGE ENGINE anchor not found"

TODAY_JS = """

/* ──────────────────────────────────────────────────────────
   TODAY CARD — state + render
────────────────────────────────────────────────────────── */

const todayCardState = {
  reading:  { expanded: true,  done: false },
  journal:  { expanded: false, done: false },
  question: { expanded: false, done: false },
};

function renderTodayCard() {
  renderTodayDate();
  renderTodayReading();
  renderTodayJournal();
  renderTodayQuestion();
  renderTodayFooter();
  renderTodayStreak();
  updateTodayDoneBadge();
}

function renderTodayDate() {
  const el = document.getElementById('today-card-date');
  if (!el) return;
  const d = new Date();
  const days   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  el.textContent = days[d.getDay()] + ' \xb7 ' + months[d.getMonth()] + ' ' + d.getDate();
}

function renderTodayReading() {
  const card = getTodayCard();
  if (!card) return;
  const label   = document.getElementById('today-reading-label');
  const pills   = document.getElementById('today-reading-pills');
  const preview = document.getElementById('today-reading-preview');
  if (label)   label.textContent   = card.title;
  if (preview) preview.textContent = card.body ? card.body.slice(0, 220) + '…' : '';
  if (pills) {
    pills.innerHTML =
      '<span class="today-track-pill terra">' + (card.track || '') + '</span>' +
      (card.tags && card.tags.length ? '<span class="today-track-pill status">' + card.tags[0] + '</span>' : '');
  }
  // Sync done state from app state
  const alreadyRead = (state.readCardIds || []).includes(card.id);
  const item = document.getElementById('today-item-reading');
  const exp  = document.getElementById('today-exp-reading');
  if (alreadyRead && !todayCardState.reading.done) {
    todayCardState.reading.done     = true;
    todayCardState.reading.expanded = false;
    if (item) item.classList.add('done');
    if (exp)  exp.classList.remove('open');
  } else if (!alreadyRead && todayCardState.reading.done) {
    // Card was unread (e.g. day rolled over); reset
    todayCardState.reading.done     = false;
    todayCardState.reading.expanded = true;
    if (item) item.classList.remove('done');
    if (exp)  exp.classList.add('open');
  }
}

function renderTodayJournal() {
  const promptEl = document.getElementById('today-journal-prompt');
  if (!promptEl) return;
  const prompts = JOURNAL_PROMPTS_SHORT;
  promptEl.textContent = prompts[Math.floor(Date.now() / 86400000) % prompts.length];
  // Sync done state if journal entry exists today
  const today = todayStr();
  const hasEntryToday = (state.journal || []).some(e => e.createdAt && e.createdAt.startsWith(today));
  const item = document.getElementById('today-item-journal');
  if (hasEntryToday && !todayCardState.journal.done) {
    todayCardState.journal.done = true;
    if (item) item.classList.add('done');
  } else if (!hasEntryToday && todayCardState.journal.done) {
    todayCardState.journal.done = false;
    if (item) item.classList.remove('done');
  }
}

function renderTodayQuestion() {
  const body = document.getElementById('today-question-body');
  if (!body) return;
  const q = getNextQuestion();
  if (!q) {
    const item = document.getElementById('today-item-question');
    if (item) item.style.display = 'none';
    return;
  }
  // Don't re-render if already answered (question is done)
  if (todayCardState.question.done) return;
  const item = document.getElementById('today-item-question');
  if (item) item.style.display = '';
  body.innerHTML =
    '<div class="today-item-label">Quick reflection</div>' +
    '<div class="today-item-sub">' + q.question + '</div>' +
    '<div class="today-item-expand" id="today-exp-question"><div class="today-expand-inner">' +
    '<div class="today-q-opts">' +
    q.options.map(function(opt) {
      return '<button class="today-q-opt" onclick="event.stopPropagation(); todaySelectAnswer(this, \\'' + q.id + '\\', ' +
        JSON.stringify(opt.stateUpdate).replace(/"/g, '&quot;') + ')">' + opt.label + '</button>';
    }).join('') +
    '</div></div></div>';
}

function renderTodayFooter() {
  // Phase name
  const phaseNameEl = document.getElementById('today-phase-name');
  if (phaseNameEl) {
    const s = state.settings || {};
    const phaseId = s.currentPhase || 'pre-transfer';
    const phaseObj = (typeof PHASES !== 'undefined') ? PHASES.find(function(p) { return p.id === phaseId; }) : null;
    const phaseLabel = phaseObj ? phaseObj.label : phaseId.replace(/-/g, ' ').replace(/\\b\\w/g, function(c) { return c.toUpperCase(); });
    const fp = s.familyPath || 'gestational-surrogacy';
    const fpLabel = fp === 'gestational-surrogacy' ? 'Gestational Surrogacy (US)'
                  : fp === 'traditional-surrogacy'  ? 'Traditional Surrogacy'
                  : fp.replace(/-/g, ' ').replace(/\\b\\w/g, function(c) { return c.toUpperCase(); });
    phaseNameEl.textContent = phaseLabel + ' \xb7 ' + fpLabel;
  }
  // Days remaining — compute directly
  const daysEl = document.getElementById('today-days-num');
  if (daysEl) {
    const today = new Date(); today.setHours(0,0,0,0);
    const msLeft = getDueDate() - today;
    const daysLeft = Math.ceil(msLeft / 86400000);
    const unitEl = daysEl.querySelector('.today-days-unit');
    daysEl.childNodes[0].textContent = daysLeft > 0 ? daysLeft : Math.abs(daysLeft);
    if (unitEl) unitEl.textContent = daysLeft > 0 ? 'days' : 'days old';
  }
  // Progress bar from tasks in current phase
  const bar       = document.getElementById('today-mini-bar');
  const progLabel = document.getElementById('today-prog-label');
  const phaseId   = (state.settings || {}).currentPhase || 'pre-transfer';
  const phaseTasks = state.tasks.filter(function(t) { return t.phase === phaseId; });
  const doneTasks  = phaseTasks.filter(function(t) { return t.status === 'done'; }).length;
  const total      = phaseTasks.length;
  const pct        = total > 0 ? Math.round(doneTasks / total * 100) : 0;
  if (bar)       bar.style.width = pct + '%';
  if (progLabel) progLabel.textContent = doneTasks + ' / ' + total + ' tasks \xb7 ' + pct + '%';
}

function renderTodayStreak() {
  const row = document.getElementById('today-streak-row');
  if (!row) return;
  const today = todayStr();
  const days  = ['S','M','T','W','T','F','S'];
  const dots  = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const str = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    const isToday = str === today;
    const wasRead = (state.readCardIds || []).includes((state.dailyCardLog || {})[str]);
    const cls = isToday ? 'today' : (wasRead ? 'on' : '');
    dots.push('<div class="today-sdot ' + cls + '">' + days[d.getDay()] + '</div>');
  }
  row.innerHTML = dots.join('');
}

function todayToggleExpand(id) {
  if (todayCardState[id] && todayCardState[id].done) return;
  const isOpen = todayCardState[id] ? todayCardState[id].expanded : false;
  if (todayCardState[id]) todayCardState[id].expanded = !isOpen;
  const exp = document.getElementById('today-exp-' + id);
  if (exp) exp.classList.toggle('open', !isOpen);
}

function todayMarkDone(id) {
  if (!todayCardState[id]) return;
  todayCardState[id].done = !todayCardState[id].done;
  const item   = document.getElementById('today-item-' + id);
  const circle = document.getElementById('today-check-' + id);
  if (todayCardState[id].done) {
    if (item) item.classList.add('done');
    todayCardState[id].expanded = false;
    const exp = document.getElementById('today-exp-' + id);
    if (exp) exp.classList.remove('open');
    if (circle) {
      circle.classList.remove('today-check-pop');
      void circle.offsetWidth;
      circle.classList.add('today-check-pop');
    }
  } else {
    if (item) item.classList.remove('done');
  }
  updateTodayDoneBadge();
}

function todaySelectAnswer(btn, qId, stateUpdate) {
  document.querySelectorAll('#today-question-body .today-q-opt')
    .forEach(function(b) { b.classList.remove('selected'); });
  btn.classList.add('selected');
  applyQuestionAnswer(qId, stateUpdate);
  setTimeout(function() { todayMarkDone('question'); }, 420);
}

function updateTodayDoneBadge() {
  const count = Object.values(todayCardState).filter(function(s) { return s.done; }).length;
  const badge = document.getElementById('today-done-badge');
  const card  = document.getElementById('today-card');
  if (!badge) return;
  if (count === 3) {
    badge.textContent = 'All done ✶';
    badge.classList.add('complete');
    if (card) card.classList.add('all-done');
  } else {
    badge.textContent = count + ' / 3';
    badge.classList.remove('complete');
    if (card) card.classList.remove('all-done');
  }
}"""

src = src.replace(NUDGE_ENGINE_ANCHOR, TODAY_JS + NUDGE_ENGINE_ANCHOR, 1)
print('  - JS: todayCardState + renderToday* functions added')

# ── 7. Write output ────────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_4.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"const CACHE_NAME = 'daddy-duty-[^']*'",
                "const CACHE_NAME = 'daddy-duty-v5-4'", sw_src)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── 8. JS syntax check ────────────────────────────────────────────────────────
node = shutil.which('node') or '/opt/homebrew/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_4.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_4.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── 9. Sanity assertions ──────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.4 \xb7 cloud sync"   in content, "version string missing"
assert "appVersion:'v5.4'"       in content, "appVersion missing"
assert 'id="today-card"'         in content, "today-card HTML missing"
assert 'today-card-styles'       in content, "today-card CSS missing"
assert 'todayCardState'          in content, "todayCardState JS missing"
assert 'renderTodayCard'         in content, "renderTodayCard missing"
assert 'todayToggleExpand'       in content, "todayToggleExpand missing"
assert 'id="home-card-wrap"' not in content, "old todays-card still present"
assert 'id="home-nudge-wrap"' not in content, "old nudge wrap still present"
assert 'class="countdown-widget"' not in content, "old countdown-widget still present"
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_4.html')
