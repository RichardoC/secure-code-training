# Guidance: Build a multi-page Xerte course with browser automation

For **another agent** that will use a browser-automation CLI to create a full
multi-page course in the **Xerte Online Toolkits (XOT)** instance running in the
local Docker container, and export it as **one SCORM 1.2 package**.

This guide is derived from reading the XOT source **and** from actually building
and exporting a 48-page course ("Secure code development"). It corrects several
assumptions that look reasonable but fail in practice. **Read it fully before
driving the browser.**

---

## TL;DR (what actually works)

1. Start the Docker container with persistent named volumes (see §1).
2. **Pick the right template up front** — this is the single most important
   decision (§2). For a course **with quizzes and LMS score reporting**, use the
   **Xerte (Nottingham)** learning-object template, **not** the Bootstrap "site"
   template (which has no native quiz/scoring page types). For a text/content
   site with no quizzes, the site template is fine.
3. Create the project with a single curl POST (§2.3) to get a known
   `template_id`.
4. Drive the **HTML5 editor** at **`/edithtml.php?template_id=<id>`** — **not**
   `/edit.php` (which loads a legacy Flash editor that browser automation cannot
   drive) (§3).
5. Use a **fast browser CLI** (e.g. `agent-browser`) with **accessibility-tree
   snapshots + `eval`**, not a heavyweight MCP/vision loop. The HTML5 editor has
   good ARIA roles and is fully drivable from text snapshots **without vision**
   (§3, §4).
6. Author pages through the UI: Insert menu → category → page type → insert
   position; set fields via `CKEDITOR.instances[<id>].setData()` (§4).
7. **Publish** before verifying/exporting — only Publish writes `data.xml`,
   which is what `play.php` and SCORM export read (§5).
8. Export SCORM via curl **with a guest session cookie** (§7).
9. Verify the export's `template.xml` (the Nottingham content file) against your
   spec (§8).

> Key corrections from earlier versions of this guide: (a) `/edit.php` is Flash —
> use `/edithtml.php`; (b) the Bootstrap site template has no quizzes/scoring —
> use Nottingham for courses; (c) Playwright MCP round-trips through a vision
> model are painfully slow and time out — use a direct browser CLI with text
> snapshots; (d) the editor's ARIA roles are actually good — vision is not
> required.

---

## 1. Start the instance (persistent)

The image is tagged `xerte`. Use **named volumes** so the course survives
container restarts/recreates. The host port can be anything (8080, 8081, …) —
use whatever is free and use it consistently everywhere.

```bash
docker rm -f xerte 2>/dev/null
docker volume create xerte-data 2>/dev/null
docker volume create xerte-files 2>/dev/null

docker run -d --name xerte -p 8081:80 \
  -v xerte-data:/var/lib/mysql \
  -v xerte-files:/var/www/xerte/USER-FILES \
  -e XERTE_FRESHCLAM_ON_START=false \
  xerte
```

Wait ~25 s for first-run provisioning, then verify:
```bash
docker ps --filter name=xerte --format '{{.Status}}'        # Up
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8081/
docker logs xerte 2>&1 | grep -E '\[xerte\]|Provisioning complete' | tail
```

Notes:
- **Guest auth** is on by default → anyone visiting is auto-logged-in as
  `guest2` (user_id=1). No login form. Fine locally.
- **ClamAV** scans uploads by default; disable with
  `-e XERTE_ENABLE_CLAMAV=false` if scans slow you down.
- Persistence: `xerte-data` (MariaDB), `xerte-files` (`USER-FILES/`).
  `docker stop`/`start` keeps everything. `docker rm -f` + `docker volume rm`
  wipes it.
- Logs/DB: `docker logs -f xerte`; `docker exec xerte sh -c 'mariadb
  --socket=/run/mysqld/mysqld.sock -uroot -proot xerte -e "<SQL>"'`.

---

## 2. Choose the template and create the project

### 2.1 Template choice (decide first)

XOT ships three template modules: `site` (Bootstrap, responsive, content-only),
`xerte` (Nottingham — interactive learning objects with quiz/MCQ/question page
types and SCORM 1.2 score tracking), and `decision`.

| Need | Template | `templatename` for creation | Editor |
|---|---|---|---|
| Content pages only, no quizzes | Bootstrap site | `site` | HTML5 (jQuery/CKEditor) |
| **Quizzes + LMS score reporting** | **Xerte Nottingham** | **`Nottingham`** | **HTML5** (`/edithtml.php`) |
| Decision-tree scenarios | decision | `decision` | (HTML5) |

**For a course with assessment, use Nottingham.** It has native page types:
Multiple Choice Question (`mcq`), Quiz (`quiz` — groups `<question>` children),
Matching Texts, Category, Hotspot, Slider, Gap Fill, and a project-level
**Tracking** property (`trackingMode`, `trackingPassed`) that wires SCORM 1.2
score reporting. The Bootstrap site template has **none** of these.

### 2.2 Land on the workspace
`http://localhost:<PORT>/index.php` (Guest auto-login). 3-pane jQuery-UI layout.

### 2.3 Create the project via curl (recommended — gives a known template_id)
```bash
COOKIE=/tmp/x.cookies
curl -s -c "$COOKIE" http://localhost:<PORT>/index.php -o /dev/null
curl -s -b "$COOKIE" -c "$COOKIE" -X POST \
  -d "templatename=Nottingham&tutorialname=My Course" \
  http://localhost:<PORT>/website_code/php/templates/new_template.php
# response: "<template_id>,1280, 768"
```
This creates `USER-FILES/<id>-guest2-Nottingham/` with a fresh empty `data.xml`
and `preview.xml`. `templatename` must match a `template_name` in
`originaltemplatesdetails` (e.g. `Nottingham`, `site`). Project name allows
letters/digits/underscore/space; spaces → `_` in the stored name and folder.

---

## 3. Opening the editor — use /edithtml.php, NOT /edit.php

- **`/edit.php?template_id=<id>` loads a legacy Flash SWF editor** (`wizard.swf`
  via SWFObject). Browser automation **cannot drive Flash**. Do not use it.
- **`/edithtml.php?template_id=<id>` loads the HTML5 editor** — jQuery-UI +
  jsTree (`#treeview`) + CKEditor. This is what you want.
- Always visit `/index.php` **first** to establish the guest session, then
  navigate to `/edithtml.php`. If you open `/edithtml.php` without a session you
  get "Session ID not set".
- If a **lockfile warning** appears ("This project is currently locked…"),
  click **"Delete lockfile and continue to editor"**, or
  `docker exec xerte rm -f /var/www/xerte/USER-FILES/<id>-guest2-Nottingham/lockfile.txt`.
  Lockfiles are left behind when an editor session is interrupted; they're safe
  to clear.

### Editor anatomy (Nottingham, `/edithtml.php`)
- **Left**: page tree (jsTree `#treeview`, root `learningObject`). Nodes =
  pages (text/bullets/mcq/quiz) → child nodes (quiz `<question>` → `<option>`).
- **Right**: properties/toolbox panel for the selected node, rendered from the
  wizard (`modules/xerte/parent_templates/Nottingham/wizards/en-GB/data.xwd`).
  Fields are CKEditor instances (`textinput_0`, `textarea_1`, …), dropdowns
  (`select_2`, …), checkboxes (`input[name="correct"]`), NumericSteppers, etc.
- **Top-right**: **Play** and **Publish** buttons.
- The editor's data model lives in `window.lo_data` (keyed by jsTree node id),
  with `.attributes` (the XML attributes) and `.data` (children). On **Publish**
  it serialises `lo_data` → `preview.xml` and copies to `data.xml`.

---

## 4. Driving the editor with a browser CLI

**Do not use a Playwright-MCP-through-a-vision-model loop.** Each round-trip is
slow and large authoring runs time out. Use a direct browser CLI such as
**`agent-browser`** (`/opt/homebrew/bin/agent-browser`, Chrome via CDP). It keeps
the browser open across commands and gives:

- `agent-browser open <url>` / `snapshot -i` (interactive accessibility tree
  with `@eN` refs) / `click <sel|@ref>` / `type` / `fill` / `eval "<js>"` /
  `screenshot` / `get text|title|url` / `close --all`.
- The HTML5 editor has **good ARIA roles** (treeitem, combobox, textbox, button,
  checkbox). `snapshot -i` + `eval` is enough — **vision is not required**.

### 4.1 The core loop
```bash
agent-browser open http://localhost:<PORT>/index.php
agent-browser open http://localhost:<PORT>/edithtml.php?template_id=<ID>
agent-browser snapshot -i          # see the tree + properties
agent-browser eval "<js>"          # select nodes, set fields, click buttons
```
Refs go stale after any DOM change; prefer CSS selectors and `eval` over stale
refs. `dialog accept` handles JS `confirm()` dialogs (or override:
`window.confirm=function(){return true}`).

### 4.2 Adding a content page (verified sequence)
The add-page menu is a nested jQuery-UI flyout: **Insert → category → page type
→ insert position (Before / After / At end)**.
```bash
agent-browser click '[title="Insert"]'                 # toolbar Insert button
agent-browser click '.Text.ui-corner-all'              # Text category
agent-browser click '.Plain.Text.ui-corner-all'        # Plain Text page type
# the "Insert New Plain Text" flyout has buttons #insert_button_before/_after/_at_end
agent-browser eval "document.getElementById('insert_button_at_end').click()"
# new page selected; set title + body:
agent-browser eval "CKEDITOR.instances['textinput_0'].setData('Page Title'); CKEDITOR.instances['textinput_0'].fire('change')"
agent-browser eval "CKEDITOR.instances['textarea_1'].setData('<p>HTML body</p>'); CKEDITOR.instances['textarea_1'].fire('change')"
```
**CRITICAL — CKEditor content only persists if set via `CKEDITOR.instances[<id>].setData(html)`
followed by `.fire('change')`.** Setting `innerHTML` on the iframe body or
`fill`/`type` on the textbox does **not** sync to the editor's data model and
will be lost on Publish. For long/quoted HTML, base64-encode it and decode in
JS: `setData(decodeURIComponent(escape(atob('<b64>'))))`.

> **Avoid the "Bullets / Timed Content" page type for static content.** It
> reveals paragraphs on a timer (`delaySecs`) and shows Play/Next buttons —
> learners find the auto-play annoying. Use **Plain Text** for static content.
> If you must use Bullets, set `delaySecs="0"` (via `lo_data`, see §4.5) to show
> all content at once.

### 4.3 Adding a Quiz with nested questions (verified sequence)
A `quiz` node only accepts `question` children; an `mcq` is a standalone scored
page. To build a quiz with grouped questions:
1. Add the Quiz page: Insert → Interactivity → Quiz → At end (or After a
   selected node). Set its title via `textinput_0`.
2. Select the Quiz node in the tree. The **New Question** button
   (`#add_question`) appears.
3. For each question: `eval document.getElementById('add_question').click()`;
   set the **question prompt** via `CKEDITOR.instances['textarea_1'].setData()`
   (textarea_1 is the prompt while the question is selected); set **Question
   Type** via the `select_2` dropdown (Single Answer / Multiple Answer); add
   options with `eval document.getElementById('add_option').click()` once each;
   for **each option**, set its text via `CKEDITOR.instances['textarea_1'].setData()`
   (textarea_1 rebinds to the option text when an option is selected), set the
   label via `input[name="name"]` (A/B/C/D), and mark the correct one(s) by
   clicking `input[name="correct"]`.
   - **Reliable option-setting pattern**: after each `add_option` click, the
     new option is auto-selected, so set its text/label/correct **immediately**,
     before clicking `add_option` again. Do not try to select option nodes by
     id afterwards — the selection rebinding is unreliable.
   - To uncheck a wrongly-checked correct box: click `input[name="correct"]`
     again (it's a toggle).
4. **Empty option nodes break the quiz** (the results/restart logic can fail).
   Never leave an option with empty `text`/`name`. If you over-added options,
   delete the extras via `jQuery('#treeview').jstree(true).delete_node(id)`.
5. The quiz **Restart** button calls `startQs()` and works once the quiz is
   complete — but only if there are no malformed/empty options.

### 4.4 Setting project-level properties (title, navigation, tracking, pass mark)
Select the root `learningObject` node. Set:
- **Project Title** via `textinput_0`.
- **Navigation** dropdown → "Menu with page controls" (learners get a contents
  menu + next/back).
- **Tracking**: the pass mark is the **Tracking** optional property on the root
  (`trackingPassed="80%"`), set via the property panel. `trackingMode` defaults
  to `full_first`. There is **no per-quiz weighting UI** in Nottingham; the LMS
  receives the aggregate score across all scored interactions. (A 25/75
  theme/final weighting would require custom JS in the SCO — not exposed in the
  editor.)

### 4.5 Changing attributes the UI widget won't allow (e.g. delaySecs=0)
Some property widgets clamp values (e.g. the Bullets "Delay (secs)"
NumericStepper has `min="1"`, so you can't set 0 via the UI). You can set the
underlying attribute directly in the editor's data model and Publish:
```bash
agent-browser eval "window.lo_data['<nodeId>'].attributes.delaySecs='0'"
# or batch over all bullets nodes:
agent-browser eval "var ld=window.lo_data,c=0; for(var k in ld){var a=ld[k]&&ld[k].attributes; if(a&&a.nodeName==='bullets'&&a.delaySecs!=='0'){a.delaySecs='0';c++}}; c"
agent-browser eval "Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()==='Publish').click()"
```
This is the editor's own data model (not a raw `data.xml` edit) and is the
legitimate way to set values the property widget restricts. Always Publish
afterwards so it writes through to `data.xml`.

To find a node's id by visible text:
```bash
agent-browser eval "var \$j=jQuery('#treeview').jstree(true); var all=\$j.get_json('#',{flat:true}); var n=null; for(var i=0;i<all.length;i++){var d=document.createElement('div'); d.innerHTML=all[i].text||''; if(d.textContent.trim().indexOf('PAGE TITLE')===0){n=all[i];break}}; n.id"
```

### 4.6 Deleting / moving nodes
```bash
agent-browser eval "window.confirm=function(){return true}; jQuery('#treeview').jstree(true).delete_node('<id>')"
agent-browser eval "jQuery('#treeview').jstree(true).move_node('<id>','<targetId>','after')"
```

---

## 5. Saving: Preview vs Publish (important)

- The editor edits **`preview.xml`**. **Publish** serialises `lo_data` to
  `preview.xml` and copies it to **`data.xml`**.
- `play.php` and **SCORM export read `data.xml`**. So always **Publish** before
  verifying or exporting.
- The editor loads `preview.xml` on open. If `preview.xml` and `data.xml` get
  out of sync (e.g. someone edited `data.xml` out-of-band), the editor will
  show the `preview.xml` content and a subsequent Publish can **overwrite**
  `data.xml` with the older `preview.xml`. Keep them in sync:
  `docker exec xerte cp <folder>/data.xml <folder>/preview.xml`.
- Auto-save also writes numbered snapshots (`data.xml.N`, `preview.xml.N`,
  `*.json.N`); ignore these — they're rolling backups, not required for restore.

---

## 6. Verify it plays

```bash
curl -s -o /dev/null -w "play=%{http_code}\n" "http://localhost:<PORT>/play.php?template_id=<ID>"
```
Or open `play.php?template_id=<ID>` in the browser and walk the Table of
Contents. The Nottingham player is a JS app; content renders inline (not in
iframes). Quiz pages show Check/Next/Restart buttons; complete a quiz to confirm
scoring + restart work.

---

## 7. Export as a single SCORM 1.2 package

**The export endpoint requires a guest session cookie** — a bare curl returns 0
bytes. Establish the session first:
```bash
COOKIE=/tmp/x.cookies
curl -s -c "$COOKIE" http://localhost:<PORT>/index.php -o /dev/null
curl -sL -b "$COOKIE" -o course_scorm.zip \
  -w "export HTTP=%{http_code}, size=%{size_download} bytes\n" \
  "http://localhost:<PORT>/website_code/php/scorm/export.php?scorm=true&template_id=<ID>"
```
Inspect:
```bash
unzip -l course_scorm.zip | head
# Expect: imsmanifest.xml, scormRLO.htm, apiwrapper_1.2.js, xttracking_scorm1.2.js,
#         models_html5/{text,mcq,quiz,bullets,menu}.html, common_html5/...
unzip -p course_scorm.zip imsmanifest.xml | grep -oE 'schemaversion>[^<]*|scormtype="[a-z]*"'
# Expect: schemaversion>1.2  and  scormtype="sco"
```
Nottingham stores the project content as **`template.xml`** inside the zip (not
`data.xml`). Verify content from the export with:
```bash
unzip -p course_scorm.zip template.xml > /tmp/exported.xml
```
SCORM 1.2 score reporting: `xttracking_scorm1.2.js` calls `LMSInitialize` →
`LMSSetValue(cmi.core.score.raw)` + `cmi.core.lesson_status` → `LMSCommit`. The
pass mark comes from `trackingPassed` on the root. Each scored quiz/MCQ needs
`judge="true"` (set by default on quiz/mcq pages).

---

## 8. Verify the export against your spec

Quick checks (against `template.xml` extracted from the zip):
```bash
unzip -p course_scorm.zip template.xml > /tmp/check.xml
grep -oE '<question' /tmp/check.xml | wc -l     # total scored questions
grep -oE 'trackingPassed="[^"]*"' /tmp/check.xml   # pass mark
grep -oE 'judge="true"' /tmp/check.xml | wc -l     # scored quizzes
# empty options (break quizzes): should be 0
python3 -c "import re,html as H; x=open('/tmp/check.xml').read(); print(sum(1 for m in re.finditer(r'<option ([^>]*?)/>',x) if H.unescape(H.unescape(re.search(r'text=\"([^\"]*)\"',m.group(1)).group(1)).replace('<p>','').replace('</p>','').strip())==''))"
```
Also walk the course in `play.php` and complete at least one quiz to confirm
Check/Next/Restart work and the score is reported.

---

## 9. Gotchas (all hit during the real build)

- **`/edit.php` is Flash; use `/edithtml.php`.** This is the #1 time-sink if you
  assume the guide's old "open `/edit.php`" still applies.
- **Playwright MCP + vision model is too slow** for a 40+ page course and times
  out. Use `agent-browser` (or equivalent) with text snapshots + `eval`.
- **CKEditor content must be set via `CKEDITOR.instances[<id>].setData()` +
  `.fire('change')`**, or it silently won't persist. This is the #2 time-sink.
- **Bullets page auto-plays** (timed reveal). Use Plain Text, or set
  `delaySecs="0"` via `lo_data`.
- **Quiz nesting**: `quiz` accepts only `question` children (not `mcq`). Add
  questions with the **New Question** button while the Quiz node is selected.
  Standalone MCQs after an empty "quiz" page load badly and feel inconsistent —
  nest them properly.
- **Empty option nodes break quiz results/restart.** Delete any option with
  empty text/name.
- **preview.xml vs data.xml**: keep in sync; Publish writes both. An out-of-sync
  preview.xml can overwrite published content on the next Publish.
- **Lockfiles** are left by interrupted editor sessions; clear them.
- **SCORM export needs a guest cookie** (bare curl → 0 bytes).
- **No per-quiz weighting UI** in Nottingham; LMS gets the aggregate score.
- **Ampersands in titles** are stored as `&amp;amp;` in `name=` attributes but
  render correctly in the player — don't "fix" them.
- **`access_to_whom`**: new projects are Private; set `Public` in the DB if
  `play.php` should work without login:
  `docker exec xerte sh -c "mariadb ... -e \"UPDATE templatedetails SET access_to_whom='Public' WHERE template_id=<ID>;\""`.

---

## 10. Reference facts

- **Templates**: Nottingham (framework `xerte`, `template_type_id=5`, quizzes +
  SCORM scoring); site (framework `site`, content-only); decision.
- **Project folder**: `USER-FILES/<template_id>-guest2-<template_name>/`
  → `data.xml`, `preview.xml`, `media/`, plus numbered snapshots.
- **Default user**: `guest2` (user_id=1).
- **Key URLs** (replace `<PORT>` and `<ID>`):
  - Workspace: `/index.php`
  - **HTML5 editor**: `/edithtml.php?template_id=<ID>` (use this)
  - Flash editor: `/edit.php?template_id=<ID>` (do NOT use)
  - Play: `/play.php?template_id=<ID>`
  - SCORM export: `/website_code/php/scorm/export.php?scorm=true&template_id=<ID>`
  - Create project: `POST /website_code/php/templates/new_template.php`
    with `templatename=<name>&tutorialname=<title>`
- **Editor internals**: jsTree `#treeview`; data model `window.lo_data`
  (keyed by node id, `.attributes` + `.data`); CKEditor instances
  `textinput_0` (title), `textarea_1` (body/prompt/option-text depending on
  selected node), `textarea_2` (mcq prompt); New Question button
  `#add_question`; New Answer button `#add_option`; Correct checkbox
  `input[name="correct"]`; Insert position buttons
  `#insert_button_before/_after/_at_end`.
- **DB tables**: `templatedetails` (projects: template_id, template_name,
  template_type_id, access_to_whom, creator_id), `templaterights`,
  `originaltemplatesdetails` (template registry: template_type_id,
  template_framework, template_name), `logindetails`, `folderdetails`.
- **Wizard** (page types + properties):
  `modules/xerte/parent_templates/Nottingham/wizards/en-GB/data.xwd`.
