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
| `source/scorm_progress.js` | **Source of truth** for the root `script` attribute (progress autosave + resume repair). Compile with `tools/sync_root_script.py` after editing. |
| `tools/sync_root_script.py` | Compiles that file into `learningObject/@script` in `data.xml`/`preview.xml`; `--check` verifies they are in sync. |
| `tests/build_scorm_package.sh` | Builds a SCORM zip from a `data.xml` using a real XOT container (same path as the release workflow). |
| `tests/test_scorm_tracking.py` | Tracking tests: runs the exported package in headless Chromium against a mock SCORM 1.2 LMS. |

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

- **44 top-level pages** in `source/data.xml` (43 learner content/quiz pages + 1
  final **"Course complete"** page added after the final quiz so it is clear the
  training is over): front matter (4) → 7 themes (each: intro + classic item
  page(s) + agentic item page(s) + theme quiz) → back matter (4: secure-SDLC
  integration, mapping, glossary, references) → final quiz → Course complete.
  (Earlier docs/reports may say 43 or 48; the authoritative count is whatever
  is in `source/data.xml`.)
- **Content page types**: pages 1–8 are `text` (Plain Text); pages from Theme 2
  onward are `bullets` (Bullets/Timed Content) with **`delaySecs="0"`** so they
  do **not** auto-play (a deliberate fix — see "Conventions" below).
- **All 20 OWASP items** present: A01–A10 (classic) + ASI01–ASI10 (agentic),
  each with its own page, interleaved by theme.
- **Quizzes**: 7 theme quizzes + 1 final quiz, all real `<quiz>` nodes with
  nested `<question>` children. **45 scored questions total** (27 theme +
  18 final; see `COURSE_VERIFICATION.md`). Every question has ≥2 options
  and ≥1 `correct="true"`; **no empty option nodes**.
- **Option order is randomised per attempt**: every `<question>` carries
  `answerOrder="random"` (the Nottingham wizard's per-question "Answer Order"
  property; see `quiz.xwd` and `models_html5/quiz.html` line ~165). The HTML5
  player shuffles each question's options on quiz load/restart, and scoring is
  computed from the shuffled array so SCORM tracking stays correct. This
  removes the previous bias where the correct answer was frequently the first
  option (especially in the final quiz). The attribute is editor-declared, so
  the XOT HTML5 editor round-trips it natively (like `trackingWeight`).
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
   *"Generated with the assistance of an AI coding agent."*
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
10. **Option order must be randomised per attempt**: every `<question>` must
    carry `answerOrder="random"` (Nottingham wizard's per-question "Answer
    Order" property, `quiz.xwd`; honoured by `models_html5/quiz.html`). This
    shuffles each question's options on quiz load/restart and removes the
    pattern of the correct answer always being the first option. Scoring is
    computed from the shuffled array, so SCORM tracking is unaffected. When
    adding a new question, set `answerOrder="random"` on it. Keep `data.xml`
    and `preview.xml` byte-identical.
11. **Wrong-answer help on every question**: each `<question>` carries a
    `feedback` attribute holding a hint and an explanation, shown
    only to a learner who answered it wrong (see "Wrong-answer help" below).
    A new question needs one; the hint must not give the answer away, and
    neither field may refer to an option by letter or position, because
    `answerOrder="random"` shuffles them. Wrong-answer help is read on its
    own, so convention 2 does not carry across it: expand each acronym on
    first use **within the hint and within the explanation**, even where the
    same acronym is already expanded elsewhere on that page.

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
from `currActPage` over the content nodes (43 when this fix was designed;
44 now that a **Course complete** page follows the final quiz — the analysis
is identical, only the last `page_nr` shifts). So every content page's
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

**Trade-off** (with the Course complete page now present): the *last* content
node — the **Course complete** page (`page_nr == 44`), a static
acknowledgement page — is not in `toCompletePages` (there is no index 44), so
its *completion* is not tracked; this is harmless (it carries no score and no
interaction). The Final quiz (`page_nr == 43`) **is** now in
`toCompletePages`, so its completion is tracked, and its *score* is tracked
via its interactions and `trackingWeight="21"`. The Welcome page is no longer
"required" for completion, which is acceptable for an intro page. A proper
fix would be in the Xerte engine (`xenith.js`: build `toCompletePages` from
`page_nr` after the menu is inserted, or do not insert the menu into `x_pages`
for tracking); this content workaround is used because the release workflow
builds from the XOT engine and an engine patch would not persist across XOT
rebuilds.

**Do not remove `unmarkForCompletion="true"` from the Welcome page** without
a replacement fix — re-introducing the off-by-one will silently break LMS
completion reporting again.

## Root `script` attribute (progress autosave + resume repair)

> **The JavaScript lives in [`source/scorm_progress.js`](../source/scorm_progress.js),
> which is the source of truth.** It is compiled into the
> `learningObject/@script` attribute of `source/data.xml` and
> `source/preview.xml` by `python3 tools/sync_root_script.py`
> (`--check` verifies the XML is up to date; the tracking tests assert it too).
> Never hand-edit the attribute — ~400 lines of JavaScript on one XML line is
> not reviewable, and the compiler also enforces the "no `<`, `>`, `&`, `"`"
> rule that keeps the attribute round-tripping through the XOT editor unescaped.

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
4. Wraps `state.setVars` / `state.getVars` / `state.initTracking` to repair
   `cmi.suspend_data` in both directions and to carry quiz page scores across
   sessions — see "SCORM resume, completion and score tracking" below for why
   each wrapper exists. The wrappers are installed at injection time, which is
   **before** `XTInitialise()` calls `initTracking()` (xenith.js line 2267 vs
   2275), which is the only reason a content-level script can fix a crash that
   happens inside `initTracking`.

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
"results only on Save", and re-introduces the start-up crash below. If the
engine is ever patched upstream to commit on `exitInteraction`, the autosave
half becomes redundant (harmless — its `persist()` would just call
`doLMSCommit` a second time, which is idempotent); the resume-repair half stays
relevant until the engine's own `getVars()`/`setVars()` are fixed upstream.

## SCORM resume, completion and score tracking

Four problems were reported from a real LMS attempt. All four are behaviours of
`modules/xerte/scorm1.2/xttracking_scorm1.2.js`, which we cannot patch (the
release workflow rebuilds the engine from upstream XOT), so they are worked
around from the root `script` attribute. Each one has a test in
`tests/test_scorm_tracking.py` that fails without the fix.

### 1. Course fails to load — `Cannot read properties of null (reading 'page_nr')`

`getVars()` serialises the resume point as

```js
var sit = this.find(this.currentpageid);
jsonObj.interactions.push(sit);          // sit is null if currentpageid is ''
```

and `find()` returns `null` for a blank id. `currentpageid` **is** blank in two
ordinary situations:

- between leaving one page and entering the next — `exitInteraction()` sets
  `this.currentpageid = ""` when `ia_nr < 0` (i.e. on every `XTExitPage`), and
  the next `XTEnterPage` sets it again. Our autosave used to flush inside
  exactly that window, so it persisted `"interactions":[null]`;
- on a *revisit* to the built-in table of contents, where the engine skips
  `XTEnterPage` (xenith.js line ~3183) and `x_endPageTracking` skips
  `XTExitPage`, so a Save Session / unload on the contents page makes the
  engine's own `finishTracking()` write the same null.

On the next launch, `setVars()` reads `jsonSit.page_nr` off that `null` and
throws from inside `initTracking()` / `XTInitialise()`. The exception unwinds
`x_continueSetUp2`, so the player never renders a page at all — the learner sees
a blank course, which is exactly what was reported.

**Fix**: `state.getVars` is wrapped so an unresumable record is never written —
nulls are dropped, and if `currentpageid` does not resolve, the wrapper
substitutes the page currently on screen (or the most recent page in
`x_pageHistory`) and includes that interaction. `state.setVars` is wrapped so a
record written by an older build is healed on the way in, and
`state.initTracking` is wrapped so that even an unforeseen bad record costs the
learner their resume point, not the whole course.

### 2. Inconsistent saved-progress data (blank resume point, 43 vs 45)

Two separate things:

- The **blank resume point** (`currentid` / `currentpageid` empty) is the same
  root cause as (1) and is fixed by the same wrapper.
- **43 `completedPages` against 45 declared pages is correct, not a mismatch.**
  `nrpages` is `x_pageInfo.length` = 44 content pages **+ 1** for the
  table-of-contents page Xerte splices in at `x_pages[0]`. `completedPages` is
  sized from `markedPages`, which excludes the contents page and the Welcome
  page (`unmarkForCompletion="true"`, see the section above), giving
  43 = pages `page_nr` 1…43, i.e. Welcome through the final quiz. The
  "Course complete" page (`page_nr` 44) is deliberately not required.

What *is* a real bug is that `setVars()` restores `completedPages` verbatim, so
a learner who resumes into a build with a different number of tracked pages
keeps an array of the wrong length, and `getSuccessStatus()` walks that array:
a short array reports completion early, a long one blocks completion forever.
The wrapper now resizes `completedPages` to `state.toCompletePages.length`
(truncate extras, pad with `false`) and prefers the live `nrpages`,
`trackingmode`, `scoremode`, `page_timeout` and pass mark over the saved copies,
because the running package knows those better than the record does. Saved
`pagesViewed` / `pageHistory` entries that no longer exist are dropped, which
also removes a second crash path (`x_restorePagesViewed` writes
`x_pageInfo[i].viewed` without a bounds check).

### 3. Completion reachability with `trackingMode="full"`

Verified end to end rather than assumed: `test_full_walkthrough_reports_passed`
walks all 44 pages, answers all 45 questions, and asserts
`cmi.core.lesson_status="passed"` with `cmi.core.score.raw=100`;
`test_completion_survives_a_resume` does the same across two sessions.

For the record, "all pages required" is weaker than it sounds: a page counts as
complete when it is *left* after more than 100 ms (`exit()` ignores shorter
visits) and all of its interactions exist. A quiz page registers all of its
question interactions when the page loads, so visiting a quiz page is enough for
*completion*; answering is what produces the *score*. The pass mark
(`trackingPassed="80%"`) is applied to the weighted score only after all 43
marked pages are complete. The practical risk was never the page count — it was
(1) the crash and (2) the stale `completedPages` array, both fixed above.

### 4. Score not captured (`score.raw` 0 with interactions logged)

`getVars()` deliberately persists only the current page's interaction ("SCORM
1.2 only allows for 4kb of suspend data"), and `getdRawScore()` computes the
grade as a weighted average over the page interactions currently in memory. So
**every quiz page score is thrown away when a learner resumes**: a learner who
does theme quizzes on Monday and the final quiz on Tuesday gets a grade based on
Tuesday alone, and a learner who answers questions without finishing a quiz page
(no `XTSetPageScore` until the results screen) reports `score.raw=0` even though
`cmi.interactions.*` is full of answers. That is the reported combination of
"lesson_status incomplete, score.raw 0, interactions logged".

**Fix**: the `getVars` wrapper adds a compact `xtPages` list —
`[page_nr, score, weighting, nrinteractions, id]` per scored page — and the
`setVars` wrapper turns it back into page interactions, so `getdRawScore()` sees
the earlier quizzes again. A size guard keeps the record inside the SCORM 1.2
4096-character `suspend_data` limit by shedding, in order: old `pageHistory`
entries, `pageHistory`, `pagesViewed`, then `xtPages` (the tests assert the
limit is respected). Because `scoremode` is `last`, re-taking a quiz still
overwrites the remembered score, and a page never counted twice
(`findPage()` matches the first page-level entry per `page_nr`).

## Learner-facing progress (status panel, honest quiz ticks, progress bar)

**Symptom**: learners could not tell how far through the course they were or
whether they had done what completion requires. Two things misled them:

- the contents-page **tick means "opened"**, nothing more. `x_pageLoaded()`
  sets `x_pageInfo[i].viewed = true` the moment a page finishes loading and
  `XENITH.PAGEMENU.tickViewed()` removes the `notvisited` class from any viewed
  page; tracking never feeds into it, so a quiz ticks before a single question
  is answered;
- the **LMS shows 0% until the very end**. SCORM 1.2 has no progress field.
  `getSuccessStatus()` returns `incomplete` until every one of the 43 tracked
  pages has been *left* (after more than 100 ms), then `passed`/`failed`
  against the pass mark. Moodle's default SCORM grading method, "Learning
  objects", counts SCOs whose status is completed/passed, and this package is
  one SCO, so the grade is 0 then 1. See "Moodle settings" in the README.

The LMS side is structural (see the README for why SCORM 2004 and multi-SCO
were rejected), so the fix is to make the course itself honest. Three parts,
all content-level (no engine patch):

1. **Status panel** (`source/scorm_progress.js`, part 5). Every element with
   the class `xtStatusPanel` is filled with: required pages completed
   (`state.completedPages` against `state.toCompletePages`), the names of the
   pages still to visit (capped at 6), each quiz page's result or "not yet
   submitted", the weighted score so far against `state.lo_passed`, and the
   exact status `state.getSuccessStatus()` would report to the LMS, in plain
   language. Two placeholders exist: the root `menuText` attribute (shown in
   the text column of the contents page) and a `<div>` at the top of the
   **Course complete** page. The panel is refreshed from `x_pageLoaded`,
   `XENITH.PAGEMENU.tickViewed`, `XTExitPage`, `XTExitInteraction` and
   `XTSetPageScore` (all wrapped). Outside an LMS it says tracking is not
   active. `window.xtRefreshProgressUi()` re-renders it on demand.
2. **Quiz ticks mean "submitted"**. The engine never reads the page-level
   interaction's `complete` field, so the `XTSetPageScore` wrapper (the quiz
   results screen is its only caller) sets it to `true`, and it is persisted as
   a sixth element of each `xtPages` row (`1`/`0`) and restored by `setVars`.
   Records written before the flag existed have no `row[5]`; a non-zero score
   can only come from the results screen, so it is treated as submitted. After
   `tickViewed`, the tick of a quiz page that is viewed but not submitted is
   swapped for `fa-adjust` (a half-filled circle) with the class `xtPending`
   and the label "Opened, quiz not yet submitted"; it reverts on submission.
3. **Header progress bar** (Xerte's own, editor-supported): root attributes
   `progressBarType="header2"` ("below titles"; `header1`, "above titles",
   is inserted after the header logo icon, and this course has no logo, so
   jQuery's `insertAfter` on an empty set silently builds nothing),
   `progressSub="milestones"`,
   `progressBarPercentage="true"`, `progressBarTxt="{x}% of pages viewed"`,
   `progressBarSubLink="true"`, plus `milestone="true"` on each of the 8 quiz
   pages. It is viewed-based like the ticks, hence the label wording.

The Welcome page explains the three indicators; the Course complete page no
longer claims the result "has been recorded" unconditionally and points at the
panel instead.

**Deliberately not changed**: what "required" means. All 43 tracked pages
(Welcome through the final quiz) still count, including About, Mapping,
Glossary and References. Exempting a page needs care: because of the
off-by-one described under "SCORM completion bug fix", `unmarkForCompletion`
on page *N* actually exempts page *N-1*; the clean route is for the root script
to rebuild `state.toCompletePages` from the live page list before
`XTInitialise`, and the tests' `TRACKED_PAGES` would follow. Also unchanged:
the engine's pass check is `getdScaledScore() > lo_passed / 100`, strictly
greater, so a score of exactly 80% reports `failed` (Moodle applies no mastery
override because the Xerte manifest declares no `adlcp:masteryscore`).

Tests: `test_status_panel_tells_the_learner_what_is_left`,
`test_quiz_tick_means_submitted_not_opened`,
`test_older_records_infer_submission_from_the_score`,
`test_header_progress_bar_counts_viewed_pages`, and the panel assertions at the
end of `test_full_walkthrough_reports_passed`.

## Wrong-answer help (hint + explanation on every question)

A learner who picked the wrong option used to see nothing but *"Your answer is
incorrect"*, so there was nothing to learn from and nothing to revise before
the restart. All 45 questions now carry a hint (what to think about, and which
theme to revisit) and an explanation (why the right answer is right, and where
useful why the tempting distractor is not), shown only when the answer was
wrong.

The text lives in the question's own `feedback` attribute, the quiz wizard's
*General Feedback* field (`quiz.xwd`), so the XOT editor exposes it as a normal
per-question text area and round-trips it. The value carries the same
double-escaped HTML as `prompt` and `text`:

```xml
<question ... feedback="&lt;p&gt;&lt;strong&gt;Hint:&lt;/strong&gt; … &lt;/p&gt;&lt;p&gt;&lt;strong&gt;Why:&lt;/strong&gt; … &lt;/p&gt;&#10;">
```

It needs the root script because `models_html5/quiz.html` renders that
attribute on every submitted answer, right or wrong. After grading, the model
fills three fixed slots (`#topFeedback`, `#middleFeedback`, `#bottomFeedback`)
in the order the question's `feedbackPos` gives, one letter per slot: `G` is
the question's own feedback, `A` the selected option's, `C` the right/wrong
line. That defaults to `GAC`, so ours lands in `#topFeedback`. Part 6 of
`source/scorm_progress.js` wraps `quiz.showFeedBackandTrackResults`, re-wrapped
from `x_pageLoaded` because the model object is rebuilt for every quiz page,
and empties that slot again when `quiz.myProgress[quiz.currentQ] === true`.

If upstream ever renames that call the wrapper does nothing and the help shows
on correct answers as well, which loses nothing. A change to the slot order
would be worse, because the wrapper would clear whatever else landed in that
slot. So `helpSlot` follows the engine's own `feedbackPos` rule rather than
assuming the first slot: an *absent* attribute means `GAC`, while an empty one
leaves the engine no slot letters at all, so there is no G slot to clear.

The per-option `feedback` field was the other candidate and was not used. It
says nothing to a learner who gets a *Multiple Answer* question wrong by
under-selecting, because every option they ticked was a correct one, and it
would repeat the same paragraph on each wrong option.

Tracking is unaffected. `XTExitInteraction` is handed `trackData.feedback`,
which is built from the *option* `feedback` values, and those are all still
empty, so the SCORM interaction records are untouched.

Tests: `test_wrong_answer_gets_a_hint_and_an_explanation` (a wrong answer is
given both, a correct one is not, across two quiz pages) and
`test_every_question_carries_wrong_answer_help` (all 45 questions have it, so a
question added later cannot silently ship without one). Reviewers can read the
text in the PR preview, which `tools/render_preview.py` renders under each
question. A question added later needs a `feedback` value in the same shape, or
that second test fails.

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
   - **Tracking tests (MANDATORY if you touched `scorm_progress.js`, tracking
     attributes, page order or quizzes):**
     ```bash
     python3 tools/sync_root_script.py --check
     git clone --depth 1 -b docker-container \
       https://github.com/RichardoC/xerteonlinetoolkits.git xote   # once
     tests/build_scorm_package.sh source/data.xml source/preview.xml out/course.zip
     python3 tests/test_scorm_tracking.py out/course.zip           # all must pass
     ```
     These build the package in a throwaway XOT container and drive the real
     exported package in headless Chromium against a mock SCORM 1.2 LMS. CI runs
     the same thing on every PR (`.github/workflows/test.yml`).
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
grep -oE '<question' /tmp/c.xml | wc -l           # 45 (27 theme + 18 final)
grep -oE 'answerOrder="random"' /tmp/c.xml | wc -l  # 45 (every question shuffles options per attempt)
grep -oE 'Hint:' /tmp/c.xml | wc -l            # 45 (wrong-answer help on every question)
grep -oE 'trackingPassed="[^"]*"' /tmp/c.xml   # 80%
grep -oE 'judge="true"' /tmp/c.xml | wc -l     # 8
grep -oE 'trackingWeight="[0-9]+"' /tmp/c.xml   # 7x "1" + 1x "21"
grep -oE 'trackingMode="[a-z_]+"' /tmp/c.xml   # "full"
grep -oE 'delaySecs="0"' /tmp/c.xml | wc -l    # 27 (all bullets pages)
grep -c 'xPersistProgress' /tmp/c.xml        # 1 (SCORM autosave script present on root)
grep -c '__xtProgress' /tmp/c.xml            # 1 (resume-repair wrappers present on root)
grep -oE 'unmarkForCompletion="true"' /tmp/c.xml | wc -l  # 1 (Welcome page)
grep -oE 'name="Course complete"' /tmp/c.xml | wc -l  # 1 (final "Course complete" page after the final quiz)
# build version: in a release export {{BUILD_VERSION}} is substituted; in source/preview it is the placeholder
grep -oE 'Version:</strong> [^<&]*' /tmp/c.xml              # e.g. 'Version:</strong> v0.0.6 (...)'
grep -c '{{BUILD_VERSION}}' /tmp/c.xml                     # 0 in a release export (1 in committed source)
unzip -p Secure_code_development_scorm.zip VERSION.txt     # present in release builds
# empty options (must be 0):
python3 -c "import re,html as H;x=open('/tmp/c.xml').read();print(sum(1 for m in re.finditer(r'<option ([^>]*?)/>',x) if H.unescape(H.unescape(re.search(r'text=\"([^\"]*)\"',m.group(1)).group(1)).replace('<p>','').replace('</p>','').strip())==''))"
curl -s -o /dev/null -w "play=%{http_code}\n" http://localhost:8088/play.php?template_id=1   # 200
# root script is the compiled source, and tracking still behaves:
python3 tools/sync_root_script.py --check
python3 tests/test_scorm_tracking.py Secure_code_development_scorm.zip   # all pass
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
