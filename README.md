# Secure code development — training course

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-blue.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

## Why?

Many organisations have a need for initial security training, and an 
[LMS](https://en.wikipedia.org/wiki/Learning_management_system) that accepts 
SCORM. This means that they can show their auditor(s) for SOC2 and ISO27001
that they're providing relevant training for secure coding practices, and now
AI agents.
This course is an attempt to do this publicly so multiple organisations can 
collaborate at making this training useful, rather than just toil for compliance.

## What?

A SCORM 1.2 e-learning course on secure code development, interleaving the
**OWASP Top 10:2025** (classic application security) with the **OWASP Top 10
for Agentic Applications 2026** (AI-agent security). It is organised into seven
themes, each with a quiz, plus a final comprehensive quiz. The audience is
engineers building software with agents and engineers building agents.

This repository holds the **course content, spec, and deliverable** — not the
Xerte Online Toolkits (XOT) software itself. The XOT CMS runs from a separate
repo (see [Run the CMS](#run-the-cms)).

## License

This course content is licensed under **Creative Commons Attribution-ShareAlike
4.0 International (CC BY-SA 4.0)** — see [LICENSE](LICENSE). The ShareAlike
clause is required by the source *OWASP Top 10 for Agentic Applications 2026*
(CC BY-SA 4.0). It is a derivative work: changes were made, and it is **not
endorsed by OWASP**. Full attribution is in [Sources and license](#sources-and-license)
and on the course's About/References pages.

## Repository contents

```
secure-code-training/
├── README.md                 # this file
├── COMMIT_MESSAGE.md         # suggested initial commit message (credits model + harness)
├── .github/workflows/
│   ├── preview.yml           # on PR: renders a readable HTML preview for reviewers
│   └── release.yml           # on release: builds the SCORM zip and attaches it
├── tools/
│   └── render_preview.py     # renders source/data.xml → preview/index.html
├── docs/                     # all documentation
│   ├── COURSE_SPEC.md        # the full page-by-page spec (source of truth for content)
│   ├── COURSE_VERIFICATION.md# verification of the export against the spec
│   ├── PROJECT_CONTEXT.md    # project-specific context for contributors/bots
│   ├── AGENT_COURSE_GUIDE.md # general guidance for authoring in the Xerte editor
│   └── RESTORE_GUIDE.md      # how to restore/import the course into a fresh XOT
└── source/                   # Xerte project source (to edit inside the CMS)
    ├── data.xml              # published content (what plays / exports)
    └── preview.xml           # editor working copy
```

- **The SCORM zip is NOT committed.** It is built by the
  [release workflow](.github/workflows/release.yml) from `source/data.xml` using
  a real XOT instance, and attached to the GitHub **Release**. To get the
  deliverable, publish a release (or run the workflow manually) and download the
  `Secure_code_development_scorm.zip` asset. If you only want to deliver the
  course, upload that asset to your LMS.
- **`source/data.xml`** + **`source/preview.xml`** are the Xerte project
  content, for editing the course inside a running XOT instance and
  re-exporting (see [Edit & re-export](#edit-and-re-export-the-course)).

## Pull-request previews

Every PR runs the [preview workflow](.github/workflows/preview.yml), which
renders `source/data.xml` into a single readable HTML page (all pages + quizzes,
correct answers marked ✓) using [`tools/render_preview.py`](tools/render_preview.py)
and uploads it as the **`course-preview`** artifact, then comments on the PR
with a summary (page/question counts, pass mark, any empty options) and a link
to the artifact. Reviewers download the artifact and open `index.html` to read
the new content version without running Xerte.

## Run the CMS

The XOT CMS is not vendored here. It lives in the `docker-container` branch of
the XOT repo:

- **Repo**: https://github.com/RichardoC/xerteonlinetoolkits
- **Branch**: `docker-container`
- **Image tag**: `xerte` (built from that branch's `Dockerfile`)

Build the image once, then run it with persistent named volumes:

```bash
git clone -b docker-container https://github.com/RichardoC/xerteonlinetoolkits.git
cd xerteonlinetoolkits
docker build -t xerte .

docker run -d --name xerte -p 8081:80 \
  -v xerte-data:/var/lib/mysql \
  -v xerte-files:/var/www/xerte/USER-FILES \
  -e XERTE_FRESHCLAM_ON_START=false \
  xerte

# wait ~25s for first-run provisioning, then:
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8081/   # expect 200
```

Guest auth is on by default — visit `http://localhost:8081/` and you are
auto-logged-in as `guest2` (no login form). The course is owned by `guest2`.

> The host port (8081 above) can be any free port; use it consistently.
> `docker stop xerte` / `docker start xerte` preserves everything (named
> volumes). `docker rm -f xerte` + `docker volume rm xerte-data xerte-files`
> wipes it.

## Import / restore the course into XOT

Full instructions are in [`docs/RESTORE_GUIDE.md`](docs/RESTORE_GUIDE.md). The
short version for a fresh instance:

```bash
# 1. Create the (empty) project and note the returned template_id
COOKIE=/tmp/x.cookies
curl -s -c "$COOKIE" http://localhost:8081/index.php -o /dev/null
curl -s -b "$COOKIE" -c "$COOKIE" -X POST \
  -d "templatename=Nottingham&tutorialname=Secure code development" \
  http://localhost:8081/website_code/php/templates/new_template.php
#   -> response like "1,1280, 768"; the first number is the template_id

# 2. Copy the source content into the new project folder and fix perms
ID=1   # replace with the template_id from step 1
FOLDER="/var/www/xerte/USER-FILES/${ID}-guest2-Nottingham"
docker cp source/data.xml    "xerte:${FOLDER}/data.xml"
docker cp source/preview.xml "xerte:${FOLDER}/preview.xml"
docker exec xerte sh -c "chown www-data:www-data '${FOLDER}/data.xml' '${FOLDER}/preview.xml'; chmod 664 '${FOLDER}/data.xml' '${FOLDER}/preview.xml'; rm -f '${FOLDER}/lockfile.txt'"

# 3. Make it viewable and verify
docker exec xerte sh -c "mariadb --socket=/run/mysqld/mysqld.sock -uroot -proot xerte -e \"UPDATE templatedetails SET access_to_whom='Public' WHERE template_id=${ID};\""
curl -s -o /dev/null -w "play=%{http_code}\n" "http://localhost:8081/play.php?template_id=${ID}"   # expect 200
```

Then open `http://localhost:8081/edithtml.php?template_id=${ID}` (the HTML5
editor — **not** `/edit.php`, which is the legacy Flash editor), confirm the
page tree shows all 48 pages, and click **Publish** once so XOT stamps its
internal state.

## Edit and re-export the course

1. Start XOT and import the course as above (or `docker start xerte` if the
   project already exists in the volumes).
2. Sync the editor's working copy to the latest published content:
   `docker exec xerte sh -c 'cp /var/www/xerte/USER-FILES/<ID>-guest2-Nottingham/data.xml /var/www/xerte/USER-FILES/<ID>-guest2-Nottingham/preview.xml; rm -f /var/www/xerte/USER-FILES/<ID>-guest2-Nottingham/lockfile.txt'`
3. Open the editor at `/edithtml.php?template_id=<ID>` and make changes. See
   [`docs/AGENT_COURSE_GUIDE.md`](docs/AGENT_COURSE_GUIDE.md) for the authoring
   workflow (page types, quizzes, CKEditor, gotchas) and
   [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) for the conventions
   specific to this course.
4. **Publish** (only Publish writes `data.xml`, which is what plays/exports).
5. Update `source/data.xml` and `source/preview.xml` from the running instance (this is what gets committed and what the release workflow builds the SCORM package from):
   ```bash
   docker exec xerte cat /var/www/xerte/USER-FILES/<ID>-guest2-Nottingham/data.xml    > source/data.xml
   docker exec xerte cat /var/www/xerte/USER-FILES/<ID>-guest2-Nottingham/preview.xml > source/preview.xml
   ```
6. (Optional, local sanity) Re-export SCORM to verify the build:
   ```bash
   COOKIE=/tmp/x.cookies
   curl -s -c "$COOKIE" http://localhost:8081/index.php -o /dev/null
   curl -sL -b "$COOKIE" -o /tmp/Secure_code_development_scorm.zip \
     "http://localhost:8081/website_code/php/scorm/export.php?scorm=true&template_id=<ID>"
   unzip -l /tmp/Secure_code_development_scorm.zip | head
   ```
7. Commit the updated `source/`, `tools/`, and any doc changes. **Do not commit
   the SCORM zip** — it is built by the release workflow and is in `.gitignore`.
   Open a PR; the preview workflow will render the new content for reviewers.
8. When the PR is merged and you want to publish, create a GitHub **Release**;
   the release workflow builds the SCORM zip and attaches it to the release.

## Content conventions (read before editing)

These are binding on this derivative work — see
[`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) for the full list:

- **License**: the course is **CC BY-SA 4.0** (required by the Agentic PDF's
  ShareAlike clause). Keep the attribution, "changes were made", "not endorsed
  by OWASP", and provenance notices on the About and References pages.
- **Acronyms**: expand on first use per page, e.g. `TOCTOU (Time-of-check to
  time-of-use)`.
- **Quizzes**: full descriptive names in question stems (never "What causes
  A01" — OWASP renumbers between releases); no free-text questions; no empty
  answer options; questions nested under their `<quiz>` node.
- **No auto-playing text**: content pages show all content at once (Plain Text,
  or Bullets with `delaySecs="0"`).
- **Incident callouts** must be self-contained for learners who haven't read the
  OWASP docs; incident references include hyperlinked sources.

## Verification

After any change, re-export and run the checks in
[`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md#verification-checklist-run-after-any-change)
(question count, pass mark, no empty options, `play.php` returns 200) and walk a
quiz end-to-end in `play.php` (answer → Check → Next → complete → Restart).

## Sources and license

This course is a derivative work based on:
- **OWASP Top 10 for Agentic Applications 2026** — OWASP Gen AI Security
  Project, Agentic Security Initiative, https://genai.owasp.org —
  **CC BY-SA 4.0**
- **OWASP Top 10:2025** — OWASP Top 10 Team, 2021–2025,
  https://owasp.org/Top10/2025/ — **CC BY 3.0**

The course is licensed **CC BY-SA 4.0**. Changes were made; it is not endorsed
by OWASP.
