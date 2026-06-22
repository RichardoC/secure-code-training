# Restore guide — "Secure code development" course

This documents how to restore the course from the backups in `course_backup/`
if the running Xerte instance loses the project or the container is wiped.

## What's backed up (in `course_backup/`)

| File | What it is |
|---|---|
| `data.xml` | The **published** project content — what `play.php` and the SCORM export read. This is the source of truth for the course. |
| `preview.xml` | The editor's working copy (kept in sync with `data.xml`). Restore this too so the editor opens showing all pages. |
| `Secure_code_development_scorm.zip` | The final **SCORM 1.2** export (13 MB, one SCO, 80% pass mark). You can upload this directly to an LMS without restoring the Xerte project at all. |

The course has **no uploaded media** (the `media/` folder only contains the
default `readme.txt`), so there are no media files to restore.

## Where the live project lives (for reference)

- **Container**: `xerte` (image tag `xerte`), port **8081** (was 8080; the host port mapping is set by `-p 8081:80`), named volumes
  `xerte-data` (MariaDB) and `xerte-files` (`/var/www/xerte/USER-FILES`).
- **Project folder on disk**:
  `/var/www/xerte/USER-FILES/1-guest2-Nottingham/`
  - `data.xml` — published content (read by `play.php` and SCORM export)
  - `preview.xml` — editor working copy
  - `media/` — uploaded media (empty here)
  - `data.xml.N` / `preview.xml.N` / `*.json.N` — Xerte's internal numbered
    backups/snapshots (created automatically on save/publish; you can ignore
    these when restoring — they're not required).
- **Database rows** (MariaDB, database `xerte`):
  - `templatedetails`: `template_id=1, template_type_id=5, template_name='Secure_code_development', creator_id=1, access_to_whom='Public'`
    (`template_type_id=5` = the Nottingham template, framework `xerte`.)
  - `templaterights`: `template_id=1, user_id=1, role='creator', folder=1`
    (`user_id=1` = `guest2`, the default Guest user.)

## Prerequisites

- The `xerte` Docker container running on port 8080. If it was removed, start it
  again (the named volumes `xerte-data` and `xerte-files` preserve data across
  `docker stop`/`start`; only `docker volume rm` or `docker rm -f` + removing
  volumes wipes them):

  ```bash
  docker start xerte          # if it exists but is stopped
  # OR, if the container was removed but volumes kept:
  docker run -d --name xerte -p 8081:80 \
    -v xerte-data:/var/lib/mysql \
    -v xerte-files:/var/www/xerte/USER-FILES \
    -e XERTE_FRESHCLAM_ON_START=false \
    xerte
  # Wait ~25s for first-run provisioning, then check:
  curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8081/
  ```

- `docker` and `curl` on the host. The backups are in
  `/Users/robosan/gitclones/xerteonlinetoolkits/course_backup/` (adjust the path
  if you copied them elsewhere).

---

## Scenario A — the project still exists (folder `1-guest2-Nottingham` present)

Use this if the container is running and the project folder still exists but the
content is missing/corrupted and you want to put the backed-up content back.

1. Copy the backed-up XML into the container, removing any lockfile:

   ```bash
   docker cp course_backup/data.xml    xerte:/var/www/xerte/USER-FILES/1-guest2-Nottingham/data.xml
   docker cp course_backup/preview.xml xerte:/var/www/xerte/USER-FILES/1-guest2-Nottingham/preview.xml
   docker exec xerte sh -c 'rm -f /var/www/xerte/USER-FILES/1-guest2-Nottingham/lockfile.txt'
   ```

2. Fix ownership/permissions so Apache (www-data) can read/write:

   ```bash
   docker exec xerte sh -c 'chown www-data:www-data /var/www/xerte/USER-FILES/1-guest2-Nottingham/data.xml /var/www/xerte/USER-FILES/1-guest2-Nottingham/preview.xml; chmod 664 /var/www/xerte/USER-FILES/1-guest2-Nottingham/data.xml /var/www/xerte/USER-FILES/1-guest2-Nottingham/preview.xml'
   ```

3. Verify it plays and exports:

   ```bash
   curl -s -o /dev/null -w "play=%{http_code}\n" "http://localhost:8081/play.php?template_id=1"
   # expect play=200
   ```

   Open `http://localhost:8081/play.php?template_id=1` in a browser to confirm
   all 48 pages and the quizzes render.

The editor will load the restored `preview.xml` (clear the lockfile warning if
prompted): `http://localhost:8081/edithtml.php?template_id=1`.

---

## Scenario B — the project was deleted or the volumes were wiped

Use this if the `1-guest2-Nottingham` folder no longer exists (e.g. the project
was deleted in Xerte, or `docker volume rm xerte-files` was run). You recreate
the empty project, then restore the content into it.

### B1. Make sure the Nottingham template is registered

If the DB was wiped and reprovisioned, Xerte re-creates the built-in templates
on startup, so the Nottingham template (template_type_id=5) should already
exist. Confirm:

```bash
docker exec xerte sh -c 'mariadb --socket=/run/mysqld/mysqld.sock -uroot -proot xerte -e "SELECT template_type_id, template_framework, template_name FROM originaltemplatesdetails WHERE template_name=\"Nottingham\";"'
# expect: 5  xerte  Nottingham
```

If the row is missing, the container did not provision correctly — re-run the
container and wait for "Provisioning complete" in `docker logs xerte`.

### B2. Recreate the project (returns a new template_id)

Guest auto-login means no credentials are needed. Create the project with a
single POST:

```bash
COOKIE=/tmp/x.cookies
curl -s -c "$COOKIE" http://localhost:8081/index.php -o /dev/null
RESP=$(curl -s -b "$COOKIE" -c "$COOKIE" -X POST \
  -d "templatename=Nottingham&tutorialname=Secure code development" \
  http://localhost:8081/website_code/php/templates/new_template.php)
echo "Create response: $RESP"   # e.g. "1,1280, 768" — the first number is the template_id
NEW_ID=$(echo "$RESP" | cut -d, -f1)
echo "New template_id: $NEW_ID"
```

This creates a folder `/var/www/xerte/USER-FILES/<NEW_ID>-guest2-Nottingham/`
with a fresh empty `data.xml` and `preview.xml`. Note the `<NEW_ID>`.

### B3. Restore the content

The folder name is `<NEW_ID>-guest2-Nottingham` (e.g. `2-guest2-Nottingham`).
Copy the backed-up XML into it:

```bash
NEW_ID=2   # replace with the id from B2
FOLDER="/var/www/xerte/USER-FILES/${NEW_ID}-guest2-Nottingham"
docker cp course_backup/data.xml    "xerte:${FOLDER}/data.xml"
docker cp course_backup/preview.xml "xerte:${FOLDER}/preview.xml"
docker exec xerte sh -c "chown www-data:www-data '${FOLDER}/data.xml' '${FOLDER}/preview.xml'; chmod 664 '${FOLDER}/data.xml' '${FOLDER}/preview.xml'; rm -f '${FOLDER}/lockfile.txt'"
```

### B4. Make it viewable (Public) and verify

Newly created projects default to Private. Set it Public so `play.php` works
without a login (matching the backed-up state):

```bash
docker exec xerte sh -c "mariadb --socket=/run/mysqld/mysqld.sock -uroot -proot xerte -e \"UPDATE templatedetails SET access_to_whom='Public' WHERE template_id=${NEW_ID};\""
curl -s -o /dev/null -w "play=%{http_code}\n" "http://localhost:8081/play.php?template_id=${NEW_ID}"
# expect play=200
```

### B5. Open the editor and Publish once

Open `http://localhost:8081/edithtml.php?template_id=${NEW_ID}` in a browser
(click "Delete lockfile and continue" if prompted). Confirm the page tree shows
all 48 pages. Click **Publish** once so Xerte stamps its internal state from the
restored `preview.xml` into `data.xml` and regenerates its numbered backups.

---

## Scenario C — you only need the SCORM package (no Xerte restore needed)

If you just want to deliver the course to an LMS, you do **not** need to restore
the Xerte project at all. Upload the backed-up SCORM package directly to the
LMS:

- File: `course_backup/Secure_code_development_scorm.zip`
- Format: SCORM 1.2, one SCO (`scormRLO.htm`), 80% pass mark, LMS score
  reporting via `apiwrapper_1.2.js` + `xttracking_scorm1.2.js`.

The LMS will import it as a single SCORM 1.2 activity.

---

## Re-exporting SCORM after a restore (Scenarios A/B)

Once the project is restored and `play.php?template_id=<ID>` returns 200, you
can re-export a fresh SCORM zip (a guest session cookie is required):

```bash
COOKIE=/tmp/x.cookies
curl -s -c "$COOKIE" http://localhost:8081/index.php -o /dev/null
curl -sL -b "$COOKIE" -o Secure_code_development_scorm.zip \
  -w "export HTTP=%{http_code}, size=%{size_download} bytes\n" \
  "http://localhost:8081/website_code/php/scorm/export.php?scorm=true&template_id=<ID>"
# replace <ID> with 1 (Scenario A) or the NEW_ID from B2
unzip -l Secure_code_development_scorm.zip | head   # expect imsmanifest.xml, scormRLO.htm, ...
```

## Verifying a restored/exported package

Quick checks that the content is intact:

```bash
# extract the project data from the zip (Nottingham stores it as template.xml)
unzip -p Secure_code_development_scorm.zip template.xml > /tmp/check.xml
grep -c "Trial MCQ" /tmp/check.xml                 # expect 0 (trial removed)
grep -oE "<question" /tmp/check.xml | wc -l        # expect 41 (23 theme + 18 final)
grep -oE "trackingPassed=\"[^\"]*\"" /tmp/check.xml # expect trackingPassed="80%"
grep -c "Final comprehensive quiz" /tmp/check.xml  # expect 1
# all 20 OWASP items present:
for i in "Broken Access Control" "Injection" "Cryptographic Failures" "Security Misconfiguration" \
         "Insecure Design" "Authentication Failures" "Software Supply Chain Failures" \
         "Software or Data Integrity Failures" "Security Logging and Alerting Failures" \
         "Mishandling of Exceptional Conditions" "Agent Goal Hijack" "Tool Misuse" \
         "Identity and Privilege Abuse" "Agentic Supply Chain" "Unexpected Code Execution" \
         "Memory" "Insecure Inter-Agent Communication" "Cascading Failures" \
         "Human-Agent Trust" "Rogue Agents"; do
  grep -qi "$i" /tmp/check.xml && echo "OK  $i" || echo "MISSING  $i"
done
```

## Notes / gotchas

- **Folder naming**: the on-disk folder is `<template_id>-guest2-Nottingham`.
  If you recreate the project (Scenario B) the new `template_id` will likely
  differ from 1 — use the new id everywhere (`play.php`, `edithtml.php`, the
  export URL, the DB update).
- **`data.xml` vs `preview.xml`**: `play.php` and SCORM export read `data.xml`.
  The editor reads/writes `preview.xml` and copies it to `data.xml` on
  **Publish**. Restoring both keeps them in sync; if you only restore `data.xml`,
  open the editor and Publish once to regenerate `preview.xml` from it.
- **Lockfile**: if you see "This project is currently locked" when opening the
  editor, click "Delete lockfile and continue to editor", or
  `docker exec xerte rm -f /var/www/xerte/USER-FILES/<ID>-guest2-Nottingham/lockfile.txt`.
- **Guest user**: the project is owned by `guest2` (user_id=1). Guest auto-login
  is on by default, so no login is needed to view/edit/export.
- **Numbered `.N` files** (`data.xml.1`, `preview.json.N`, etc.) are Xerte's own
  rolling snapshots — you do not need to back up or restore them; they are
  regenerated as you edit/publish.
- **Volumes**: `docker stop xerte` / `docker start xerte` keeps everything.
  `docker rm -f xerte` keeps the volumes (so the project survives) unless you
  also run `docker volume rm xerte-data xerte-files`.
