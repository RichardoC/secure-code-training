#!/usr/bin/env bash
# Build a SCORM 1.2 package from a Xerte data.xml using a real XOT container.
#
# This is the same import/export path the release workflow uses, kept as a
# script so the tracking tests can run against a genuinely exported package
# rather than a hand-assembled one.
#
# Usage:
#   tests/build_scorm_package.sh <data.xml> <preview.xml> <out.zip> [http-port]
#
# Environment:
#   XOTE_DIR   checkout of the XOT docker-container branch, used only if the
#              'xerte' image does not exist yet (default: ./xote)
#   KEEP_XOT   set to 1 to leave the container running for debugging
set -euo pipefail

DATA_XML=${1:?usage: build_scorm_package.sh <data.xml> <preview.xml> <out.zip> [port]}
PREVIEW_XML=${2:?missing preview.xml}
OUT_ZIP=${3:?missing output zip path}
PORT=${4:-8099}
XOTE_DIR=${XOTE_DIR:-xote}
CONTAINER=xerte-test-$$
COOKIE=$(mktemp)

cleanup() {
  if [ "${KEEP_XOT:-0}" = "1" ]; then
    echo "KEEP_XOT=1, leaving container $CONTAINER on port $PORT"
    return
  fi
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -f "$COOKIE"
}
trap cleanup EXIT

if ! docker image inspect xerte >/dev/null 2>&1; then
  if [ ! -d "$XOTE_DIR" ]; then
    echo "No 'xerte' image and no XOT checkout at $XOTE_DIR." >&2
    echo "Clone it first:" >&2
    echo "  git clone --depth 1 -b docker-container https://github.com/RichardoC/xerteonlinetoolkits.git $XOTE_DIR" >&2
    exit 1
  fi
  echo "==> Building the xerte image from $XOTE_DIR (slow, once per machine)"
  docker build -t xerte "$XOTE_DIR"
fi

echo "==> Starting XOT ($CONTAINER) on port $PORT"
docker run -d --name "$CONTAINER" -p "$PORT:80" \
  -e XERTE_FRESHCLAM_ON_START=false \
  xerte >/dev/null

for _ in $(seq 1 90); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" || echo 000)
  if [ "$code" = "200" ]; then break; fi
  sleep 2
done
code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" || echo 000)
if [ "$code" != "200" ]; then
  echo "XOT did not come up (HTTP $code)" >&2
  docker logs "$CONTAINER" 2>&1 | tail -30 >&2
  exit 1
fi
echo "    XOT is up"

echo "==> Creating the project and importing the course"
curl -s -c "$COOKIE" "http://localhost:$PORT/index.php" -o /dev/null
RESP=$(curl -s -b "$COOKIE" -c "$COOKIE" -X POST \
  -d "templatename=Nottingham&tutorialname=Secure code development" \
  "http://localhost:$PORT/website_code/php/templates/new_template.php")
ID=$(echo "$RESP" | cut -d, -f1)
if ! [ "$ID" -gt 0 ] 2>/dev/null; then
  echo "Unexpected new_template.php response: $RESP" >&2
  exit 1
fi
FOLDER="/var/www/xerte/USER-FILES/${ID}-guest2-Nottingham"
docker cp "$DATA_XML" "$CONTAINER:${FOLDER}/data.xml"
docker cp "$PREVIEW_XML" "$CONTAINER:${FOLDER}/preview.xml"
docker exec "$CONTAINER" sh -c "chown www-data:www-data '${FOLDER}/data.xml' '${FOLDER}/preview.xml'; chmod 664 '${FOLDER}/data.xml' '${FOLDER}/preview.xml'; rm -f '${FOLDER}/lockfile.txt'"
docker exec "$CONTAINER" sh -c "mariadb --socket=/run/mysqld/mysqld.sock -uroot -proot xerte -e \"UPDATE templatedetails SET access_to_whom='Public' WHERE template_id=${ID};\""

play=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/play.php?template_id=${ID}")
echo "    play.php returned HTTP $play"
if [ "$play" != "200" ]; then
  echo "play.php did not return 200 - XOT rejected this data.xml" >&2
  exit 1
fi

echo "==> Exporting SCORM 1.2 to $OUT_ZIP"
mkdir -p "$(dirname "$OUT_ZIP")"
curl -sL -b "$COOKIE" -o "$OUT_ZIP" \
  -w "    export HTTP=%{http_code}, size=%{size_download} bytes\n" \
  "http://localhost:$PORT/website_code/php/scorm/export.php?scorm=true&template_id=${ID}"
unzip -l "$OUT_ZIP" >/dev/null
echo "    package built"
