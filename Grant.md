# Daddy Duty — Project Charter

*The full reference document for Grant. Everything you need to understand, run, maintain, and grow this project.*

---

## What This Is

**Daddy Duty** is a personal web app built for you — a first-time father navigating fatherhood via gestational surrogacy. It lives at [https://GrantBH12.github.io/daddy-duty](https://GrantBH12.github.io/daddy-duty) and is designed to be your companion through the entire journey: from pre-transfer preparation through the newborn phase.

The app is intentionally personal and private. It's not a product for sale. It's not a startup. It's a tool built for one user (you), with the architecture of something that *could* grow if you ever wanted it to.

**Core purpose:** Give an intended father a structured, intelligent, emotionally grounded companion for the surrogacy-to-fatherhood journey — something that holds your tasks, tracks your budget, builds your knowledge, and helps you journal the experience.

---

## The App — What It Does

Daddy Duty is a **single-page web app** organized into seven modules, all accessible from a home hub.

### Module 01 — Master To-Do
A phased task list organized by your journey stage (pre-transfer → delivery). Tasks have:
- Steps/subtasks
- Attachments (links, contacts, documents from My Stuff)
- Tags and due dates
- GC-aware tasks gated to surrogacy path only
- "This Week" pinning for focus

### Module 02 — Budget
A pre-populated budget tracker covering major surrogacy and baby cost categories. Supports custom line items, category groups, and tracks budgeted vs. actual spend. Includes a product ideas panel for curated purchasing recommendations.

### Module 03 — Shopping List
Pre-populated baby gear items organized into buying tiers (essential, recommended, optional) with filter views and budget integration. Supports custom items.

### Module 04 — Hospital Bag
A packing checklist with four tabs: Dad, Partner, Baby, Documents. All items checkable. Pre-populated with a surrogacy-aware item set (e.g., pre-birth order in the documents tab).

### Module 05 — Knowledge Library
The intellectual core of the app. A curated card library of research-backed parenting and surrogacy content, organized by pregnancy phase. One card surfaces per day on the home screen; you can browse the full library and navigate back through previous days. Reading a card earns XP and builds your streak. **191 cards as of v4.2; goal is 365 (one per day for a full year).**

### Module 06 — Journal
A private, in-app journal. Supports free writing and prompted entries. The app nudges you with prompts when you haven't written recently. Entries are timestamped and browseable.

### Module 07 — My Stuff
A personal vault of links, contacts, and documents relevant to your surrogacy journey — agency portal, attorney contact, GCA document, etc. Items can be attached to tasks in Module 01.

### Home Hub
The daily dashboard, organized around the card as the primary focal point:
1. **Greeting** — personalized with your name, baby nickname, and journey context
2. **Today's Card** — the dark hero card; includes the card body, any active daily check-in question, action buttons, and your 7-day streak strip
3. **Nudge** — smart prompt surfacing the most relevant next action
4. **Countdown widget** — compact strip showing days to due date, current phase, and phase progress bar
5. **Parenthood Toolkit** — grid of all 7 modules

### Daily Questions
Short check-in questions that appear inside Today's Card. Two types:
- **Setup questions** (asked in pre-transfer phase): establish your profile — GC distance, first-time parent status, prior loss, track preferences, partnered/solo. Answered once.
- **Milestone check-ins**: triggered when today's card is related to a topic you may have completed (car seat installed? nursery ready?). Confirming removes related cards from future draws.

### Gamification
XP and streak system woven through the app. Reading cards earns +10 XP. Streaks are built by reading a card every consecutive day. The 7-day streak strip lives inside the card itself; XP is shown in the top bar.

### Onboarding
A 7-step first-run modal collects your name, partner name, baby nickname, GC name, family path, due date, and transfer date. Drives phase detection and personalizes greetings throughout the app.

---

## Who Has Access

The app uses **magic-link authentication** — no passwords. Users receive an email link that signs them in automatically. Three users are authorized:

| Person | Role |
|--------|------|
| Grant (you) | Primary user |
| Lauren | Partner — can view/share the app |
| Katelyn | GC — future restricted view (Phase D roadmap) |

Each user has their own cloud-synced data row. The app is private by default; the auth overlay blocks access until signed in.

---

## Technical Architecture

This is a **zero-build, zero-framework single-file web app.** The entire application — HTML, CSS, and JavaScript — lives in one file: `docs/index.html`. There's no React, no Node server, no build pipeline in the traditional sense. It's vanilla HTML/CSS/JS served as a static file.

### Why this architecture?
- Zero hosting cost (static file on GitHub Pages)
- Zero deployment complexity (git push = live)
- Zero runtime dependencies except the Supabase CDN for auth
- Entire app is readable and auditable in one place
- Works offline (localStorage) and syncs when online (Supabase)

### Data storage — two layers
1. **localStorage** — all state is saved locally in the browser under key `firstdad.app.v2_3`. Instant reads/writes. Works offline. Survives page reloads.
2. **Supabase** — cloud backup and multi-device sync. On sign-in, app compares local timestamp vs. cloud `updated_at` and loads whichever is newer. Saves are debounced (2.5s after last change) to avoid thrashing.

### PWA (Progressive Web App)
The app has a web manifest and Apple meta tags, so it can be installed to your home screen on iOS and Android as a standalone app. Install from Safari (Share → Add to Home Screen) or Chrome (address bar install prompt).

### Authentication
Supabase magic-link auth. User enters email → Supabase sends a one-time link → clicking the link signs you in. No passwords stored anywhere. Sessions persist until you explicitly sign out.

---

## Infrastructure & Costs

| Service | What It Does | Cost |
|---------|-------------|------|
| **GitHub Pages** | Hosts and serves the app | **Free** |
| **GitHub** (repo) | Version control | **Free** — public repo |
| **Supabase** (free tier) | Auth + cloud sync | **Free** — up to 500MB, 50,000 MAU |
| **Google Fonts** | Fraunces, IBM Plex Mono, Inter | **Free** |

**Total monthly cost: $0.00**

Previously hosted on Netlify; migrated to GitHub Pages in May 2026 (Netlify build credits were nearly exhausted; GitHub Pages has no credit system for static files).

---

## How Changes Get Made

Every change follows one pattern:

```
Edit source file → run build script → git push → live in ~60 seconds
```

More specifically:
1. The current source file (`daddy-duty-v4_2.html`) is the "working copy"
2. A new Python build script (`tools/build_vX_X.py`) reads the previous version, applies patches, injects credentials from `.env`, writes the new version file, copies it to `docs/index.html`, and pushes to GitHub
3. GitHub Pages serves `docs/index.html` automatically

### Version numbering
- Major.minor versions (v2.x, v3.x, v4.x) represent significant feature additions or redesigns
- Patch versions (v3.9.1) represent bug fixes without new features
- Current: **v4.2**

### The `.env` file
Lives at `Daddy Duty/.env` and is gitignored (never committed). Contains:
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
```
If this file is lost, retrieve the values from Supabase Dashboard → Settings → API.

---

## The Knowledge Library — Card Expansion Goal

The library is the most unique feature and the most active area of growth.

### How it works
Cards are organized by pregnancy phase. The app detects your current phase from your transfer date and due date, then draws one card per day from the matching phase pool. The draw is stable (same card all day), logged to your daily card log, and you can browse backwards through previous days. Once you've read all cards in a phase, the app cycles back through them deterministically.

The pool also adapts to your profile: cards are filtered based on your answers to daily check-in questions (first-time parent, prior loss, GC distance, partner status) and milestone completion. If you've confirmed a car seat is installed and inspected, car-seat cards stop appearing.

### Card structure
Each card has:
- `id` — unique string (e.g., `n-018`)
- `phase` — `preparing | first | second | third | newborn`
- `weekRange` — `[startWeek, endWeek]` or `null` (week-prioritized but not restricted)
- `track` — `Bonding | Legal | Medical | Emotional | Surrogacy | Self | Logistics`
- `tags` — milestone and behavioral labels (see full breakdown in `daddy-duty-card-system-spec.html`)
- `title` — plain text
- `body` — ~200–350 words of research-backed content

Surrogacy-track cards are hidden for non-surrogacy family paths; all other tracks show for all paths.

### Current count (v4.2 — 191 cards)

| Phase | Current | Target | Gap |
|-------|---------|--------|-----|
| preparing | 43 | 60 | 17 |
| first | 56 | 75 | 19 |
| second | 36 | 65 | 29 |
| third | 23 | 50 | 27 |
| newborn | 33 | 75 | **42** |
| **Total** | **191** | **365** | **174** |

**The newborn phase is the biggest gap.** Cards here are the most valuable — you'll be in this phase when the baby arrives, and it's the least well-covered territory in existing parenting resources for fathers.

### Adding cards
1. Write new cards to `daddy-duty-card-reference.html` first — this is the sourced reference file with citation metadata (certainty rating, source type, source label, URL)
2. Copy `title` and `body` into the app's `LIBRARY_CARDS` array in the source HTML
3. Always insert new cards *inside* the array, before the closing `];`
4. Use backtick template literals for all card text (prose contains apostrophes)

### Next IDs per phase
- preparing: `a-044`, `a-045`...
- first trimester: `f-042`, `f-043`...
- second trimester: `s-025`, `s-026`...
- third trimester: `t-022`, `t-023`...
- newborn: `n-034`, `n-035`...

Always grep the live source to confirm the last ID before writing new ones.

---

## Design System

The app has a full branded design system living in `brand/`.

### Palette
| Token | Hex | Role |
|-------|-----|------|
| `--cream` | `#f5ede0` | Primary background |
| `--ink` | `#2a2620` | Primary text, dark surfaces |
| `--terra` / terracotta | `#c97156` | Primary accent, CTAs |
| `--sage` | `#7a8b6b` | Secondary accent, medical/verified |
| `--honey` | `#e8b547` | Gamification, XP, streaks |

### Typography
- **Fraunces** — display headings, wordmark, card titles (variable serif with optical size)
- **IBM Plex Mono** — metadata, eyebrows, data labels
- **Inter** — body text, UI

### Icons
42 SVG icons in a sprite at `brand/assets/icons.svg`, all prefixed `dd-`. Seven module icons (`dd-mod-todo`, `dd-mod-budget`, etc.) and 35+ UI icons.

---

## Roadmap

### Completed
- ✓ 7 core modules (Todo, Budget, Shopping, Hospital Bag, Library, Journal, My Stuff)
- ✓ Phase-aware knowledge library with daily card draw
- ✓ Supabase magic-link auth + cloud sync
- ✓ PWA installability (home screen app)
- ✓ Full design system (palette, typography, icons)
- ✓ XP + streak gamification
- ✓ 7-step onboarding
- ✓ Multi-path support (GC surrogacy, adoption, IVF, natural)
- ✓ Tag system (milestone suppression + behavioral filters)
- ✓ Daily questions (setup + milestone check-ins)
- ✓ Card promoted to primary hero (v4.2 home redesign)

### Near-term
- Expand library from 191 → 365 cards (174 remaining; newborn phase is priority)
- Partner label personalization ("Parenthood Toolkit" section name via user settings)

### Phase C — Partner Mode (Lauren)
- Lauren gets a shared household view via Supabase Realtime
- Shared state on tasks, shopping, hospital bag
- Separate journal (private per user)

### Phase D — GC Mode (Katelyn)
- Restricted view: no financial data, no journal
- Check-in widget (how are you feeling today?)
- Appointment log she can fill in

### Long-term (if ever productized)
- Mobile-first redesign
- Push notifications for milestone reminders
- Custom card authoring (add your own notes to any card)
- Export as a printable "Year One Journal"

---

## Key Links & Credentials Guide

| Resource | URL / Location |
|----------|---------------|
| Live app | https://GrantBH12.github.io/daddy-duty |
| GitHub repo | https://github.com/GrantBH12/daddy-duty |
| Supabase project | supabase.com → your project (noqclfqpdgdtcxxeradf) |
| Supabase anon key | Supabase Dashboard → Settings → API → "anon / public" key (starts with `eyJ`) |
| Supabase URL | Supabase Dashboard → Settings → API → Project URL |
| `.env` file | `Daddy Duty/.env` (local only, gitignored — never commit) |
| SSH key for pushes | `~/.ssh/id_ed25519_github` |

### If you need to re-create `.env`
Go to Supabase → Settings → API. Copy "Project URL" as `SUPABASE_URL` and "anon / public" key as `SUPABASE_ANON_KEY`. Do not use the service_role key (starts with `sb_secret_`).

### If magic links stop working
Go to Supabase → Authentication → URL Configuration. Confirm:
- **Site URL:** `https://GrantBH12.github.io/daddy-duty`
- **Redirect URLs:** `https://GrantBH12.github.io/daddy-duty/**`

---

## File Map

```
Daddy Duty/
├── daddy-duty-v4_2.html               Current canonical source — never edit docs/index.html directly
├── daddy-duty-card-reference.html     Sourced card library with citation metadata
├── daddy-duty-question-reference.html Daily question reference (authoritative for DAILY_QUESTIONS)
├── daddy-duty-task-reference.html     Task/to-do reference
├── daddy-duty-card-system-spec.html   Card system deep-dive: phases, tracks, tags, algorithm, stats
├── docs/
│   ├── index.html                     Live deployed file — auto-generated, never hand-edit
│   └── manifest.json                  PWA manifest — auto-generated
├── tools/
│   └── build_v4_2.py                  Current build + deploy script
├── brand/
│   ├── brand-standards.md             Human-readable design reference
│   ├── tokens/colors-and-type.css     CSS custom properties (injected at build)
│   ├── assets/icons.svg               Full SVG sprite (injected at build)
│   ├── assets/icons/                  Individual SVG sources
│   ├── investor-deck.html             Investor presentation
│   └── preview/                       Design reference cards (HTML)
├── .env                               Supabase credentials (gitignored)
├── CLAUDE.md                          Instructions for Claude Code (AI assistant)
├── Grant.md                           This document
├── requirements.txt                   Python dependencies
└── workflows/                         SOPs for recurring tasks
```

---

## Terminology

The app and all documentation use specific language intentionally:

- **GC** or **gestational carrier** — never "surrogate" or "surrogate mother"
- **Intended parent / IP** — the parent(s) not carrying the pregnancy
- **Pre-birth order** — the legal document establishing parental rights before birth
- **Transfer date** — date of embryo transfer (start of the gestational pregnancy)
- **Family path** — the route to parenthood (gestational surrogacy, traditional surrogacy, IVF, adoption, natural)

---

*Last updated: June 2026 · v4.2*
