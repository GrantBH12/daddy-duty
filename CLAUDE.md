# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases

**Layer 2: Agents (The Decision-Maker)**
- Your role: intelligent coordination between intent and execution
- Read the relevant workflow, run tools in the correct sequence, handle failures, ask clarifying questions when needed
- Example: To pull data from a website, read `workflows/scrape_website.md` to get the required inputs, then execute `tools/scrape_single_site.py` — don't attempt it directly

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work: API calls, data transformations, file operations, database queries
- Credentials and API keys live in `.env`

**Why this separation matters:** When AI handles every step directly, accuracy compounds poorly — 90% accuracy per step means 59% success after five steps. Offloading execution to deterministic scripts keeps the agent focused on orchestration.

## Operating Rules

**1. Check `tools/` before building anything new.** Only create scripts when nothing exists for the task.

**2. When things fail:**
- Read the full error trace and fix the script
- If a fix requires paid API calls or credits, check before re-running
- Update the workflow with what you learned (rate limits, timing quirks, unexpected behavior) so the failure doesn't recur

**3. Don't create or overwrite workflows without asking** unless explicitly instructed. Workflows are the persistent instructions for this system and should be refined, not discarded.

## Python Environment

Activate before running any tool scripts:
```
source .venv/bin/activate
```

Install new packages with `.venv/bin/pip install <package>` and add them to `requirements.txt`.

## File Structure

```
.tmp/                         # Temporary files (scraped data, intermediate exports) — regenerated as needed, disposable
tools/                        # Python scripts for deterministic execution
workflows/                    # Markdown SOPs
.env                          # API keys and environment variables
credentials.json, token.json  # Google OAuth (gitignored)
```

Deliverables (final outputs) go to cloud services (Google Sheets, Slides, etc.) where the user can access them directly. Local files are for processing only.