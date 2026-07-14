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
- **Pass mark**: `trackingPassed="80%"`, `trackingMode="full"` (last attempt
  counts; see "SCORM scoring" below), all quizzes `judge="true"`. SCORM 1.2
  score reporting verified (`apiwrapper_1.2.js` + `xttracking_scorm1.2.js` →
  `cmi.core.score.raw` + `lesson_status`).
- **No Trial MCQ** (an early trial page was removed).
- **Welcome page carries `unmarkForCompletion="true"`** — see "SCORM completion
  bug fix" below for why; it is the fix for LMS completion tracking.
- **Root `<learningObject>` carries a `script="..."` attribute** (SCORM
  autosave) — see "SCORM autosave on progress" below; it makes results report
  to the LMS as the learner progresses instead of only on Save Session.
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
9. **Validate every `source/data.xml` change through XOT before shipping**
   (MANDATORY). The release workflow builds the SCORM zip by importing
   `source/data.xml` into a real XOT instance and exporting, so the file must
   be accepted by XOT — not just well-formed XML. After any edit, run the
   XOT validation in §"How to make changes" (push the file into a running
   XOT instance, confirm `play.php` returns 200 and the editor opens without
   error, export a SCORM package, and grep the exported `template.xml` to
   confirm `trackingMode`, `trackingWeight`, `trackingPassed`, the question
   count, and the empty-option count are all as expected). Do not merge a
   `source/data.xml` change that has not passed this validation.

## Known deviations (acknowledged, not to "fix" without asking)

- **Per-quiz weighting is set via the `trackingWeight` attribute** on each
  `<quiz>` node (7 theme quizzes `trackingWeight="1"`, final quiz
  `trackingWeight="21"` → final is 21/28 = 75% of the LMS grade, themes
  7/28 = 25%, matching `COURSE_SPEC.md`). Nottingham has **no UI** for
  `trackingWeight`; it is set as a direct attribute on `source/data.xml` +
  `source/preview.xml`. The Xerte HTML5 editor **does** preserve it: the
  `lo_data` loader reads `trackingWeight` into the in-memory model and the
  Publish serializer writes it back to `data.xml`/`preview.xml` (verified by
  an editor open + Publish round-trip — all 8 `trackingWeight` values survived).
  So editor-based edits are safe; no re-application needed. See "SCORM
  scoring" below for the full rationale.
- **Item pages from Theme 2 onward use the "Bullets" page type** (cosmetic;
  rich HTML renders correctly, and `delaySecs="0"` disables the timed reveal).
  Plain Text would be "purer" but converting 27 pages is not worth the risk.

## SCORM completion bug fix (0.0.4 — `unmarkForCompletion` on Welcome)

**Symptom**: on LMS the course reported **0% completion**
even though the learner finished every quiz and `cmi.core.score.raw` was
being sent (75, then 100). `cmi.core.lesson_status` was never reported as
`passed`/`completed`/`failed`.

**Root cause** (a Xerte Nottingham engine bug, worked around at the content
level): with `navigation="Menu with Page Controls"`, Xerte inserts a built-in
Table-of-Contents page as `x_pages[0]` **after** `toCompletePages` is built
from `currActPage` over the 43 content nodes. So every content page's
`page_nr` (used by `exitInteraction` to mark `completedPages[i]`) is
`currActPage + 1` — a systematic **off-by-one**:

- `toCompletePages[0] == 0` is only matched by `page_nr == 0` (the menu),
  which is never exited (menu pages are excluded from `x_endPageTracking`),
  so `completedPages[0]` (the first content page, "Welcome") stayed `false`
  forever.
- The last content page (Final quiz, `page_nr == 43`) had no
  `toCompletePages` entry, so its completion was lost too.
- `getSuccessStatus()` returns `'incomplete'` whenever any `completedPages[i]`
  is `false`, so `finishTracking()` set `cmi.core.lesson_status='incomplete'`
  (a no-op against Moodle's pre-set 'incomplete'), and the LMS never left the
  incomplete state.

**Fix**: add `unmarkForCompletion="true"` to the **first content page**
("Welcome & how to use this course", `linkID="PG1781882348053"`) in
`source/data.xml` + `source/preview.xml`. This makes `markedPages` skip
`currActPage == 0`, so `toCompletePages` becomes `[1,2,…,42]`, which now
matches the content pages' `page_nr` values (`1…42`). `completedPages[0]`
(Welcome) is now marked `true` when the learner leaves it, and when all
tracked pages are visited `getSuccessStatus()` returns `passed`/`failed`
against `trackingPassed="80%"`. Verified locally with a SCORM 1.2 mock API:
a completed run sends `cmi.core.lesson_status="passed"`, `cmi.core.exit=""`,
`cmi.core.score.raw`, `score.min`, `score.max`, and `cmi.core.session_time`.

**Trade-off**: the Final quiz (`page_nr == 43`) is still not in
`toCompletePages` (there is no index 43), so its *completion* is not tracked
in `completedPages` — but its *score* is still tracked via its interactions
and `trackingWeight="21"`, so the LMS grade and pass/fail are correct. The
Welcome page is no longer "required" for completion, which is acceptable for
an intro page. A proper fix would be in the Xerte engine (`xenith.js`: build
`toCompletePages` from `page_nr` after the menu is inserted, or do not insert
the menu into `x_pages` for tracking); this content workaround is used because
the release workflow builds from the XOT engine and an engine patch would not
persist across XOT rebuilds.

**Do not remove `unmarkForCompletion="true"` from the Welcome page** without
a replacement fix — re-introducing the off-by-one will silently break LMS
completion reporting again.

## SCORM autosave on progress (root `script` attribute)

**Symptom**: on LMS, results (`cmi.core.score.raw`, `cmi.core.lesson_status`,
interactions, `suspend_data`) were only reported to the LMS when the learner
clicked **Save Session** (or the window unloaded). If the LMS viewer unloaded
the SCO without reliably firing `onbeforeunload`, nothing was reported and the
gradebook stayed empty mid-attempt.

**Root cause** (Xerte Nottingham engine behaviour, **not** a bug we can fix in
content via the engine files — the release workflow builds the engine from the
`docker-container` branch of `RichardoC/xerteonlinetoolkits`, so engine JS
edits do not persist): in `xttracking_scorm1.2.js`, `exitInteraction()` (called
on every page leave / quiz answer) issues many `LMSSetValue` calls but **never**
calls `LMSCommit`. `doLMSCommit()` is called **only** inside `finishTracking()`,
which is called **only** from `XTTerminate()` (Save Session / `onbeforeunload`).
SCORM 1.2 only persists `LMSSetValue` to the LMS backend on `LMSCommit`, so all
progress stayed in the API adapter's in-memory model until terminate. Worse,
`cmi.core.score.raw` and `cmi.core.lesson_status` are *set* only inside
`finishTracking()`, so even a mid-session commit would not update the grade.

**Fix** (content-level, no engine/vendoring change): a `script="..."` attribute
on the `<learningObject>` root in `source/data.xml` + `source/preview.xml`.
`script` is an **official, optional Nottingham root property** (wizard
`data.xwd` line 261: *"Add JavaScript to this project. The code will run after
the project interface has been set up but before any pages have loaded"*);
xenith.js injects it once globally via `$x_head.append('<script>' +
x_params.script + '</script>')` (line 2269). The script:

1. Defines `persist()` — replays the score/status half of `finishTracking()`
   (`cmi.core.lesson_status`, `cmi.core.score.raw/min/max`, `cmi.core.exit`,
   `cmi.suspend_data`) then calls `doLMSCommit()`, using the engine's own global
   `state` object (`state.getSuccessStatus()`, `state.getRawScore()`,
   `state.getVars()`). Guards on `state.initialised`, `state.scormmode ===
   'normal'`, `state.trackingmode !== 'none'`, `state.finished`, and the
   presence of `doLMSCommit`/`state.getSuccessStatus` so it is a no-op outside a
   live SCORM `normal` session (e.g. `play.php`, xAPI, noop tracking).
2. Wraps the global `XTExitPage` and `XTExitInteraction` so every page leave and
   quiz answer flushes immediately — the gradebook updates as the learner
   progresses.
3. A 30 s `setInterval` heartbeat as a safety net (idle learners, or LMS
   viewers that unload without events), and a `pagehide` listener as a backup
   flush if `onbeforeunload` does not fire.

**Why this is safe and durable**: it is content, so the release workflow
exports it as part of `data.xml`/`template.xml` with no engine change. The
editor round-trips it: `build_lo_data` (toolbox.js) loads **all** root
attributes including `script`, and `editor/upload.php` `process()` re-adds
**every** attribute via `addAttribute` (no filtering by wizard-declared names).
Verified by an editor open → Publish round-trip: `script` survived in
`data.xml` byte-for-byte (timestamp updated, attribute intact). `makeAbsolute`
only rewrites `FileLocation + '...'` media refs (absent from the script) and
`addLineBreaks` only applies to textinput/textarea types, so the JS is not
mangled. The script attribute value contains no XML-special characters (`&`,
`<`, `>`, `"` — single quotes only, `!== -1` instead of `>= 0`, nested `if`s
instead of `&&`), so it sits raw in the XML with no escaping concerns.

**Do not remove or empty the root `script` attribute** without a replacement —
re-introducing the terminate-only commit will silently revert to
"results only on Save". If the engine is ever patched upstream to commit on
`exitInteraction`, this `script` becomes redundant (harmless — its `persist()`
would just call `doLMSCommit` a second time, which is idempotent) and can be
dropped.

## Build version stamping (`{{BUILD_VERSION}}` placeholder)

So an operator can tell **which version is running** in an LMS, the SCORM
package carries a build stamp in two places:

1. **Visible in the player** — the About page (page 2) has a `Build` section
   with a line `<p><strong>Version:</strong> {{BUILD_VERSION}} …</p>`. The
   `{{BUILD_VERSION}}` token is a **placeholder** committed in `source/data.xml`
   + `source/preview.xml`.
2. **Machine-readable** — the release workflow adds a `VERSION.txt` (version,
   build timestamp, full commit SHA, source tree URL) to the zip root.

**Who substitutes the placeholder:**
- **Release workflow** (`.github/workflows/release.yml`): a `Compute build
  version` step derives `v<tag> (YYYY-MM-DD, commit <short>)` for release events
  (`github.ref_name` = tag) or `dev (…, workflow_dispatch)` for manual runs; an
  `Inject build version into course content` step `python3`-replaces
  `{{BUILD_VERSION}}` in `source/data.xml` + `source/preview.xml` **before** the
  XOT import, so the substituted value is what gets exported. The `Verify the
  package` step fails the build if `{{BUILD_VERSION}}` remains in the exported
  `template.xml`.
- **Preview workflow** (`.github/workflows/preview.yml`): a `Set preview build
  label` step substitutes `{{BUILD_VERSION}}` → `preview (PR #N, commit <short>)`
  before `render_preview.py`, so PR preview HTML shows a clean build line instead
  of the raw token.

**Why a placeholder (not a committed version):** the version is only known at
release time (the git tag), so it cannot be baked into committed source. The
placeholder keeps `source/data.xml` version-agnostic and is a valid, static
value that round-trips through the XOT editor (verified: a Publish cycle
preserves `{{BUILD_VERSION}}` intact — CKEditor does not mangle the braces).

**Do not remove the `{{BUILD_VERSION}}` placeholder** from the About page
without a replacement — the release workflow's verify step expects it to be
present before substitution and absent after, and that check guards against
silent version-stamping regressions.

## SCORM scoring (how the LMS grade is computed)

SCORM 1.2 reports **one** `cmi.core.score.raw` (0–100) and **one**
`cmi.core.lesson_status` for the whole package (SCO). Xerte's
`xttracking_scorm1.2.js` computes the single score as a **weighted average**
across all quiz pages, where each quiz's weight is its `trackingWeight`
attribute (default `1.0` when absent — read by `quiz.rlm`'s setup script and
passed to `XTSetPageType(..., trackingWeight)`). The `trackingMode` attribute
on the root controls which attempt is locked in:

| `trackingMode` | `trackingmode` | `scoremode` | effect |
|---|---|---|---|
| `full_first` | `full` | `first` | first completed attempt of each quiz counts |
| `full` | `full` | `last` | **last** completed attempt of each quiz counts (retries can improve) |
| `minimal_first` | `minimal` | `first` | completion only, first attempt |
| `minimal` | `minimal` | `last` | completion only, last attempt |
| `none` | `none` | — | no tracking |

This course uses `trackingMode="full"` (last attempt counts — the questions
are tricky and learners should not be trapped by a bad first attempt) and
`trackingWeight` 1/1/…/1/21 so the final comprehensive quiz is **75%** of the
LMS grade and the seven theme quizzes are **25%** in total, per `COURSE_SPEC.md`.

`cmi.core.lesson_status` is `incomplete` until **every** page in
`toCompletePages` is completed (all 48 pages are marked for completion — no
`unmarkForCompletion="true"`); it then becomes `passed`/`failed` against
`trackingPassed="80%"`. Some LMSs only display/record a grade once status
leaves `incomplete`, so learners must finish the final quiz and let the
package fire `LMSFinish` for the grade to post.

## How to make changes (workflow)

> Host port: the examples use `8081`; on this machine 8081 is taken by another
> service, so XOT runs on **`8088`** (`-p 8088:80`). Any free host port works —
> use it consistently. `docker ps` shows the mapped port.

1. `docker start xerte` (if stopped). `curl -s -o /dev/null -w '%{http_code}' http://localhost:8088/` → 200.
2. Sync preview to data so the editor opens with the latest published content:
   `docker exec xerte sh -c 'cp /var/www/xerte/USER-FILES/1-guest2-Nottingham/data.xml /var/www/xerte/USER-FILES/1-guest2-Nottingham/preview.xml; rm -f /var/www/xerte/USER-FILES/1-guest2-Nottingham/lockfile.txt'`.
3. `agent-browser open http://localhost:8088/index.php` then
   `agent-browser open http://localhost:8088/edithtml.php?template_id=1`
   (click "Delete lockfile and continue" if prompted).
4. Make edits via the UI (`snapshot -i` + `eval`; CKEditor via `setData`).
   See `AGENT_COURSE_GUIDE.md` §4. Author through the editor UI and Publish
   for content changes. The only legitimate out-of-band file ops are: (a) the
   `cp data.xml preview.xml` sync above, (b) `lo_data` attribute writes via
   `eval` (which go through the editor's own data model + Publish), and (c)
   direct attribute edits to `source/data.xml` + `source/preview.xml` for
   attributes the editor UI does not expose — notably `trackingWeight` (which
   the editor *does* round-trip safely; see convention 9 + "SCORM scoring").
   For (c), keep `data.xml` and `preview.xml` byte-identical and push both
   into the container as in step 4b below.
5. **Publish** (`eval` click the Publish button) — only needed for UI edits;
   skip for direct-attribute edits (already in `data.xml`).
6. **XOT validation (MANDATORY before merge — see convention 9):**
   - `curl -s -o /dev/null -w 'play=%{http_code}\n' http://localhost:8088/play.php?template_id=1` → 200.
   - Export a SCORM package (next step) and grep the exported `template.xml`
     to confirm `trackingMode`, `trackingWeight` (7×`1` + 1×`21`),
     `trackingPassed="80%"`, question count (45), and empty-option count (0).
   - If `play.php` is not 200 or the export is missing tracking attrs, the
     `data.xml` is not valid for XOT — do not merge.
7. **Re-export SCORM** (needs guest cookie — see guide §7) and update
   `course_backup/` (`cp` the zip + `docker exec xerte cat data.xml > course_backup/data.xml` + same for preview.xml).
8. Update `COURSE_VERIFICATION.md` if the change affects conformance.

### 4b. Pushing a direct `source/data.xml` edit into XOT (for `trackingWeight` etc.)

```bash
FOLDER=/var/www/xerte/USER-FILES/1-guest2-Nottingham
docker cp source/data.xml    "xerte:${FOLDER}/data.xml"
docker cp source/preview.xml "xerte:${FOLDER}/preview.xml"
docker exec xerte sh -c "chown www-data:www-data '${FOLDER}/data.xml' '${FOLDER}/preview.xml'; chmod 664 '${FOLDER}/data.xml' '${FOLDER}/preview.xml'; rm -f '${FOLDER}/lockfile.txt'"
docker exec xerte mariadb --socket=/run/mysqld/mysqld.sock -uroot -proot xerte -e "UPDATE templatedetails SET access_to_whom='Public' WHERE template_id=1;"
```
Then continue at step 6 (XOT validation).

## Re-export command (copy-paste)

```bash
COOKIE=/tmp/x.cookies
curl -s -c "$COOKIE" http://localhost:8088/index.php -o /dev/null
curl -sL -b "$COOKIE" -o Secure_code_development_scorm.zip \
  -w "export HTTP=%{http_code}, size=%{size_download} bytes\n" \
  "http://localhost:8088/website_code/php/scorm/export.php?scorm=true&template_id=1"
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
grep -oE 'trackingWeight="[0-9]+"' /tmp/c.xml   # 7x "1" + 1x "21"
grep -oE 'trackingMode="[a-z_]+"' /tmp/c.xml   # "full"
grep -oE 'delaySecs="0"' /tmp/c.xml | wc -l    # 27 (all bullets pages)
grep -c 'xPersistProgress' /tmp/c.xml        # 1 (SCORM autosave script present on root)
grep -oE 'unmarkForCompletion="true"' /tmp/c.xml | wc -l  # 1 (Welcome page)
# build version: in a release export {{BUILD_VERSION}} is substituted; in source/preview it is the placeholder
grep -oE 'Version:</strong> [^<&]*' /tmp/c.xml              # e.g. 'Version:</strong> v0.0.6 (...)'
grep -c '{{BUILD_VERSION}}' /tmp/c.xml                     # 0 in a release export (1 in committed source)
unzip -p Secure_code_development_scorm.zip VERSION.txt     # present in release builds
# empty options (must be 0):
python3 -c "import re,html as H;x=open('/tmp/c.xml').read();print(sum(1 for m in re.finditer(r'<option ([^>]*?)/>',x) if H.unescape(H.unescape(re.search(r'text=\"([^\"]*)\"',m.group(1)).group(1)).replace('<p>','').replace('</p>','').strip())==''))"
curl -s -o /dev/null -w "play=%{http_code}\n" http://localhost:8088/play.php?template_id=1   # 200
```
Then open `play.php` in a browser, walk a theme quiz and the final quiz
end-to-end (answer → Check → Next → complete → Restart) to confirm the UI works.

## Open / optional improvements (not requested; do not do unless asked)

- Convert the 27 Bullets content pages to Plain Text for "purer" page types
  (cosmetic only; current state renders fine with no auto-play).

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
