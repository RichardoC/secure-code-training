# Course verification report — "Secure code development"

Verification of the exported SCORM 1.2 package against `COURSE_SPEC.md`.
Source inspected: `template.xml` inside `Secure_code_development_scorm.zip`
(identical to `course_backup/data.xml`, 122,637 bytes).

## Backups saved
- `course_backup/Secure_code_development_scorm.zip` (13 MB, SCORM 1.2)
- `course_backup/data.xml` (project content, 122,637 bytes)
- `course_backup/preview.xml`

## SCORM package validity ✅
- `imsmanifest.xml`: schema `ADL SCORM`, schemaversion `1.2`, one SCO
  (`adlcp:scormtype="sco"`, href `scormRLO.htm`), title "Secure code development".
- Tracking files present: `apiwrapper_1.2.js`, `xttracking_scorm1.2.js`
  → reports `cmi.core.score.raw`, `cmi.core.lesson_status`, interactions to LMS.
- 2,546 files, 13 MB. Project title "Secure code development", navigation
  "Menu with Page Controls".

## Spec conformance

### Pages (48 present, in spec order) ✅
1 Welcome · 2 About/licensing/provenance · 3 (Trial MCQ — see deviations) ·
4 Intro to secure code dev · 5 How OWASP Top 10 works ·
Theme 1 (intro, A01, A07, ASI03, quiz) ·
Theme 2 (intro, A05, ASI01, ASI02, ASI05, quiz + 4 standalone MCQs) ·
Theme 3 (intro, A03, A08, ASI04, ASI06, quiz) ·
Theme 4 (intro, A04, quiz) ·
Theme 5 (intro, A02, A06, A10, ASI08, quiz) ·
Theme 6 (intro, ASI07, ASI09, ASI10, quiz) ·
Theme 7 (intro, A09, quiz) ·
Back matter (Putting it together, Mapping, Glossary, References) ·
Final comprehensive quiz.

### All 20 OWASP items present ✅
A01–A10 (classic) and ASI01–ASI10 (agentic) all present with correct titles.

### 7 themes + final quiz ✅
Theme 1–7 intros and quizzes present; Final comprehensive quiz present.

### Back matter ✅
Putting it together (secure SDLC + threat modelling), Mapping & cross-references,
Glossary/abbreviations, References & further reading — all present.

### Licensing / attribution / provenance ✅ (all on About + References pages)
CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0); both OWASP sources
attributed (Agentic 2026 / genai.owasp.org / CC BY-SA 4.0; Top 10:2025 /
owasp.org/Top10/2025/ / CC BY 3.0); "changes were made"; "not endorsed by OWASP";
provenance (pi v0.79.8, models glm-5.2 and kimi k2.7-coder).

### Acronym expansions ✅ (sample all present)
IDOR (Insecure Direct Object Reference), RCE (Remote Code Execution),
TOCTOU (Time-of-check to time-of-use), MCP (Model Context Protocol),
AIBOM (AI Bill of Materials), SBOM (Software Bill of Materials),
HITL (Human-in-the-Loop), NHI (Non-Human Identity), MITM (Man-in-the-Middle),
RAG (Retrieval-Augmented Generation).

### Pass mark ✅
`trackingPassed="80%"` set on the project.

### Quiz naming convention ✅
No "What causes A01"-style questions; all 29 question prompts use full
descriptive names. No free-text questions (all selection-based).

### Quizzes & correct answers ✅
- Theme 1 Quiz: 4 Q (single, multi-response, T/F, single) — correct flags set.
- Theme 2: 4 standalone MCQs (Q1 single ✅, Q2 T/F ✅, Q3 multi-response ✅, Q4 single ✅).
- Theme 3 Quiz: 4 Q — correct flags set.
- Theme 4 Quiz: 3 Q — correct flags set.
- Theme 5 Quiz: 5 Q (incl. multi-response) — correct flags set.
- Theme 6 Quiz: 4 Q — correct flags set.
- Theme 7 Quiz: 3 Q — correct flags set.
- Final comprehensive quiz: 6 Q (incl. multi-response) — correct flags set.
Total: 29 nested questions + 4 standalone MCQs + 1 trial MCQ.

## Re-verification after fixes (final state)

Two fixes applied per user request, then re-exported:

1. **Trial MCQ page removed** ✅ — 0 occurrences in the export. (Was a leftover
   trial question; the same question remains in Theme 1 Quiz and the Final quiz.)
2. **Final comprehensive quiz expanded from 6 to 18 questions** ✅ — covers all
   themes with single-answer, multiple-response, and true/false items; correct
   answers verified on all 18. Total questions now 41 (23 theme + 18 final).
3. **Per-quiz weighting + last-attempt scoring applied** ✅ — `trackingWeight`
   added to every `<quiz>` (7 theme quizzes `="1"`, final `="21"` → final is
   75% of the LMS grade, themes 25%), and root `trackingMode` changed from
   `full_first` to `full` so the **last** attempt of each quiz counts (learners
   can retry tricky questions without being trapped by a bad first attempt).
   Nottingham has no UI for `trackingWeight`; it is set directly on
   `source/data.xml` + `source/preview.xml`. **Validated through XOT**
   (2026-06-30): pushed into a running XOT instance, `play.php` returned 200,
   the HTML5 editor opened and loaded `trackingWeight` into `lo_data`, a
   Publish round-trip preserved all 8 `trackingWeight` values in `data.xml`,
   and the SCORM export carried `trackingMode="full"` + `trackingWeight`
   1×7 + 21 into `template.xml`. See `PROJECT_CONTEXT.md` § "SCORM scoring"
   and convention 9 (XOT validation is now mandatory before merge).

Remaining minor deviations (not requested to fix):

- **Theme 2 quiz questions are standalone MCQ pages**, not nested under the
  Theme 2 Quiz node (Nottingham's `quiz` only accepts `question` children;
  nesting failed for Theme 2). Functionally equivalent — still scored and
  SCORM-tracked. Structural deviation from other themes' nested pattern.
- **Content page type**: item pages from Theme 2 onward are "Bullets / Timed
  Content" pages rather than "Plain Text". Cosmetic only — rich HTML renders
  correctly in the player (verified).

## Final SCORM export
`Secure_code_development_scorm.zip` (13 MB, SCORM 1.2, one SCO,
`scormRLO.htm`, `apiwrapper_1.2.js` + `xttracking_scorm1.2.js` for LMS scoring,
`trackingPassed="80%"`, `trackingMode="full"`, per-quiz `trackingWeight`
1×7 + 21). Backups in `course_backup/`. The course now fulfills
the specification in all major respects.

## LMS completion fix (post-0.0.3)

**Problem reported on LMS **: the 0.0.3 release reported
**0% completion** to the LMS even though the learner finished every quiz.
A HAR capture showed `cmi.core.score.raw` was sent (75, then 100) but
`cmi.core.lesson_status` was never reported as `passed`/`completed`/`failed`,
and `cmi.core.suspend_data.completedPages` was `[false, true, true, …]` —
index 0 (the first content page, "Welcome") was never marked complete.

**Root cause**: a Xerte Nottingham off-by-one between `toCompletePages`
(built from `currActPage` over the 43 content nodes, before the built-in
Table-of-Contents menu page is inserted as `x_pages[0]`) and `page_nr` (used
by `exitInteraction`, which is `currActPage + 1` for every content page
because the menu takes `page_nr == 0`). `completedPages[0]` could only be set
by exiting the menu (which never happens), so `getSuccessStatus()` always
returned `'incomplete'`. Full analysis in `PROJECT_CONTEXT.md` § "SCORM
completion bug fix".

**Fix applied**: `unmarkForCompletion="true"` on the Welcome page
(`linkID="PG1781882348053"`) in `source/data.xml` + `source/preview.xml`,
shifting `toCompletePages` to `[1,2,…,42]` so it aligns with the content
pages' `page_nr`. Verified locally with a SCORM 1.2 mock API harness: a
completed run now sends `cmi.core.lesson_status="passed"` (+ `exit`,
`score.raw`, `score.min`, `score.max`, `session_time`).

**Pending (convention 9 — MANDATORY before merge)**: push the updated
`source/data.xml` + `source/preview.xml` into a running XOT instance,
confirm `play.php` returns 200, export a SCORM package, and grep the exported
`template.xml` to confirm `unmarkForCompletion="true"` is present on the
Welcome page and the question count / `trackingWeight` / `trackingPassed` /
empty-option count are unchanged. Then re-test on LMS that a
completed attempt reports `lesson_status=passed` and a non-zero grade.
