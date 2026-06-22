# Project context — "Secure code development" Xerte course

Read this if you are an agent/bot picking up work on this project. It captures
the **current state, decisions, conventions, and gotchas specific to this
course** that are not in the general `AGENT_COURSE_GUIDE.md`.

## What this project is

A SCORM 1.2 e-learning course titled **"Secure code development"**, built in a
local Xerte Online Toolkits (XOT) Docker instance and exported as a single
SCORM 1.2 package for upload to an LMS. The course interleaves the **OWASP
Top 10:2025** (classic app security) with the **OWASP Top 10 for Agentic
Applications 2026** (AI-agent security), organised into 7 themes, with a quiz
per theme and a final comprehensive quiz. Audience: engineers building software
with agents and building agents.

## Key files (all in the repo root, `/Users/robosan/gitclones/xerteonlinetoolkits`)

| File | Purpose |
|---|---|
| `COURSE_SPEC.md` | The full page-by-page spec: 48 pages, 7 themes, all quiz questions/options/correct answers, licensing, conventions. **The source of truth for what the course should contain.** |
| `COURSE_VERIFICATION.md` | Verification report of the export against the spec (what conforms, known deviations). |
| `AGENT_COURSE_GUIDE.md` | General guidance for building any Xerte course with browser automation (template choice, editor, SCORM export, gotchas). Read this first. |
| `RESTORE_GUIDE.md` | How to restore the course from backups (3 scenarios: project exists / wiped / SCORM-only). |
| `Secure_code_development_scorm.zip` | The **final exported SCORM 1.2 package** (~13 MB). Upload this to the LMS. |
| `course_backup/` | Backups: `Secure_code_development_scorm.zip`, `data.xml`, `preview.xml`. |
| `.mcp.json` | MCP server config (Playwright MCP, `--browser firefox`). Not used for the fast path; see below. |
| `~/.pi/agent/agents/xerte-author.md` | A pi subagent definition for authoring via `agent-browser` (model `accounts/fireworks/models/kimi-k2p7-code`). |

## Environment / access

- **Container**: `xerte` (image `xerte`), host port **8081** (`-p 8081:80`), named
  volumes `xerte-data` (MariaDB) + `xerte-files` (`USER-FILES`). Start with
  `docker start xerte` if stopped; recreate with the `docker run` in
  `AGENT_COURSE_GUIDE.md` §1.
- **Project**: `template_id=1`, Nottingham template, folder
  `/var/www/xerte/USER-FILES/1-guest2-Nottingham/`, `access_to_whom='Public'`,
  owned by `guest2` (user_id=1).
- **Guest auto-login** — no credentials needed.
- **Editor URL**: `http://localhost:8081/edithtml.php?template_id=1`
  (visit `/index.php` first; clear lockfile if prompted).
- **Play URL**: `http://localhost:8081/play.php?template_id=1`.
- **Browser automation**: use **`agent-browser`** (`/opt/homebrew/bin/agent-browser`,
  Chrome via CDP). Do **not** use the Playwright MCP for authoring — it is too
  slow. (The `.mcp.json` Playwright/firefox config is kept for ad-hoc screenshots
  only.) See `AGENT_COURSE_GUIDE.md` §4.

## Current state of the course (as last exported)

- **48 learner pages** in spec order: front matter (4) → 7 themes (each: intro +
  classic item page(s) + agentic item page(s) + theme quiz) → back matter (4:
  secure-SDLC integration, mapping, glossary, references) → final quiz.
- **Content page types**: pages 1–8 are `text` (Plain Text); pages from Theme 2
  onward are `bullets` (Bullets/Timed Content) with **`delaySecs="0"`** so they
  do **not** auto-play (a deliberate fix — see "Conventions" below).
- **All 20 OWASP items** present: A01–A10 (classic) + ASI01–ASI10 (agentic),
  each with its own page, interleaved by theme.
- **Quizzes**: 7 theme quizzes + 1 final quiz, all real `<quiz>` nodes with
  nested `<question>` children. **45 scored questions total** (23 theme +
  18 final + 4 … see `COURSE_VERIFICATION.md`). Every question has ≥2 options
  and ≥1 `correct="true"`; **no empty option nodes**.
- **Final quiz** has **18 distinct questions** (fresh scenarios, not duplicates
  of the theme-quiz questions), mix of single-answer risk-identification and
  true/false.
- **Pass mark**: `trackingPassed="80%"`, `trackingMode="full_first"`, all quizzes
  `judge="true"`. SCORM 1.2 score reporting verified (`apiwrapper_1.2.js` +
  `xttracking_scorm1.2.js` → `cmi.core.score.raw` + `lesson_status`).
- **No Trial MCQ** (an early trial page was removed).
- `play.php` returns 200; the export is `Secure_code_development_scorm.zip`.

## Conventions (MANDATORY for any content changes)

These were agreed with the course owner and must be preserved:

1. **Licensing**: course is **CC BY-SA 4.0** (required by the Agentic PDF's
   ShareAlike). The **About page** (page 2) and the **References page** must
   both carry: attribution to both OWASP sources (OWASP Top 10 for Agentic
   Applications 2026, genai.owasp.org, CC BY-SA 4.0; OWASP Top 10:2025,
   owasp.org/Top10/2025/, CC BY 3.0); a "changes were made" notice; a
   "not endorsed by OWASP" notice; and **provenance**:
   *"Generated with the pi coding-agent harness v0.79.8 using LLM models
   glm-5.2 and kimi k2.7-coder."*
2. **Acronym expansion**: the first time a security acronym is used **on a
   page**, give the full form in brackets, e.g. `TOCTOU (Time-of-check to
   time-of-use)`. Reuse the acronym thereafter on that page; expand again on the
   next page. (Checked: IDOR, RCE, TOCTOU, MCP, AIBOM, SBOM, HITL, NHI, MITM,
   RAG, etc. are all expanded.)
3. **Quiz wording**: frame questions with the **full descriptive name** of the
   risk (e.g. "Broken access control is best illustrated by…"), **never**
   "What causes A01" — item codes (A01/ASI01) may appear only as optional
   parenthetical cross-references, because OWASP reordering changes between
   releases. **No free-text questions** — only selection-based (single choice,
   multiple response, true/false, matching, categorise).
4. **Audience/tone**: engineers building software with agents **and** building
   agents. Write in our own words (derivative work), not verbatim from the OWASP
   sources.
5. **Incident callouts** must be **self-contained** for a learner who has not
   read the OWASP docs — explain the scenario in plain language; do not just
   name it (e.g. the ASI03 callout was rewritten from "Forged Agent Persona" to
   a plain explanation of a forged agent in a registry). Incident references on
   the References page must include **hyperlinked sources** (not just names).
6. **No auto-playing text**: content pages must show all content at once. If
  using the Bullets page type, set `delaySecs="0"` (via `lo_data`, see guide
  §4.5). Prefer Plain Text for new static content.
7. **Quizzes must be consistent**: every theme quiz is a real `<quiz>` node
   with nested `<question>` children (the Theme 2 quiz was rebuilt this way
   after it was found to be a Bullets page with standalone MCQs that "didn't
   load"). Never leave empty option nodes.
8. **Ambiguous questions are not acceptable**: each scenario must point to
   exactly one correct answer (the RCE and supply-chain questions were
   rewritten to be unambiguous — see `COURSE_SPEC.md`).

## Known deviations (acknowledged, not to "fix" without asking)

- **No per-quiz weighting (25%/75%)**: Nottingham has no weighting UI; the LMS
  receives the **aggregate** score across all quiz interactions. The owner
  accepted this. (A 25/75 split would need custom JS in the SCO.)
- **Item pages from Theme 2 onward use the "Bullets" page type** (cosmetic;
  rich HTML renders correctly, and `delaySecs="0"` disables the timed reveal).
  Plain Text would be "purer" but converting 27 pages is not worth the risk.

## How to make changes (workflow)

1. `docker start xerte` (if stopped). `curl -s -o /dev/null -w '%{http_code}' http://localhost:8081/` → 200.
2. Sync preview to data so the editor opens with the latest published content:
   `docker exec xerte sh -c 'cp /var/www/xerte/USER-FILES/1-guest2-Nottingham/data.xml /var/www/xerte/USER-FILES/1-guest2-Nottingham/preview.xml; rm -f /var/www/xerte/USER-FILES/1-guest2-Nottingham/lockfile.txt'`.
3. `agent-browser open http://localhost:8081/index.php` then
   `agent-browser open http://localhost:8081/edithtml.php?template_id=1`
   (click "Delete lockfile and continue" if prompted).
4. Make edits via the UI (`snapshot -i` + `eval`; CKEditor via `setData`).
   See `AGENT_COURSE_GUIDE.md` §4. **Do not edit `data.xml`/`preview.xml`
   directly** — author through the editor UI and Publish. (The only legitimate
   out-of-band file op is the `cp data.xml preview.xml` sync above, and
   `lo_data` attribute writes via `eval`, which go through the editor's own
   data model + Publish.)
5. **Publish** (`eval` click the Publish button).
6. **Verify**: read-only `docker exec xerte cat …/data.xml`; `curl play.php`;
   walk the affected pages/quizzes in `play.php` (complete a quiz to check
   Check/Next/Restart).
7. **Re-export SCORM** (needs guest cookie — see guide §7) and update
   `course_backup/` (`cp` the zip + `docker exec xerte cat data.xml > course_backup/data.xml` + same for preview.xml).
8. Update `COURSE_VERIFICATION.md` if the change affects conformance.

## Re-export command (copy-paste)

```bash
COOKIE=/tmp/x.cookies
curl -s -c "$COOKIE" http://localhost:8081/index.php -o /dev/null
curl -sL -b "$COOKIE" -o Secure_code_development_scorm.zip \
  -w "export HTTP=%{http_code}, size=%{size_download} bytes\n" \
  "http://localhost:8081/website_code/php/scorm/export.php?scorm=true&template_id=1"
cp Secure_code_development_scorm.zip course_backup/
docker exec xerte cat /var/www/xerte/USER-FILES/1-guest2-Nottingham/data.xml > course_backup/data.xml
docker exec xerte cat /var/www/xerte/USER-FILES/1-guest2-Nottingham/preview.xml > course_backup/preview.xml
# sanity checks:
unzip -p Secure_code_development_scorm.zip template.xml | grep -oE '<question' | wc -l   # ~45
unzip -p Secure_code_development_scorm.zip template.xml | grep -oE 'trackingPassed="[^"]*"'
```

## Verification checklist (run after any change)

```bash
unzip -p Secure_code_development_scorm.zip template.xml > /tmp/c.xml
grep -c "Trial MCQ" /tmp/c.xml                 # 0
grep -oE '<question' /tmp/c.xml | wc -l           # 45 (23 theme + 18 final + 4 …)
grep -oE 'trackingPassed="[^"]*"' /tmp/c.xml   # 80%
grep -oE 'judge="true"' /tmp/c.xml | wc -l     # 8
grep -oE 'delaySecs="0"' /tmp/c.xml | wc -l    # 27 (all bullets pages)
# empty options (must be 0):
python3 -c "import re,html as H;x=open('/tmp/c.xml').read();print(sum(1 for m in re.finditer(r'<option ([^>]*?)/>',x) if H.unescape(H.unescape(re.search(r'text=\"([^\"]*)\"',m.group(1)).group(1)).replace('<p>','').replace('</p>','').strip())==''))"
curl -s -o /dev/null -w "play=%{http_code}\n" http://localhost:8081/play.php?template_id=1   # 200
```
Then open `play.php` in a browser, walk a theme quiz and the final quiz
end-to-end (answer → Check → Next → complete → Restart) to confirm the UI works.

## Open / optional improvements (not requested; do not do unless asked)

- Convert the 27 Bullets content pages to Plain Text for "purer" page types
  (cosmetic only; current state renders fine with no auto-play).
- Add the 25%/75% theme/final weighting via custom SCO JS (Nottingham has no
  UI for it; owner declined).
- Rewrite the remaining incident callouts (Replit, Gemini, Amazon Q, etc.) in
  the same plain self-contained style as the ASI03 callout — they already
  explain their scenario in the body, but could be made more uniform.
- Expand the final quiz beyond 18 questions (it already meets the spec's
  "comprehensive" intent).

## Source licenses (binding on this derivative)

- **OWASP Top 10 for Agentic Applications 2026** (PDF): **CC BY-SA 4.0** —
  OWASP Gen AI Security Project, Agentic Security Initiative, genai.owasp.org.
  (ShareAlike → this course is CC BY-SA 4.0.)
- **OWASP Top 10:2025** (owasp.org/Top10/2025/): **CC BY 3.0** — OWASP Top 10
  Team, 2021–2025.
- Both require attribution + "changes were made" + "not endorsed by OWASP".
