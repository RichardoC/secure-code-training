#!/usr/bin/env python3
"""Compile source/scorm_progress.js into the learningObject/@script attribute.

The Nottingham template's root "script" property (wizard data.xwd) is a single
XML attribute, which is a terrible place to maintain ~400 lines of JavaScript.
So source/scorm_progress.js is the source of truth and this tool inlines it
into source/data.xml and source/preview.xml.

    python3 tools/sync_root_script.py            # write the attribute
    python3 tools/sync_root_script.py --check    # verify it is up to date

"Compiling" means: strip comments and collapse whitespace to one line. That is
required, not cosmetic - XML attribute-value normalisation turns newlines into
spaces, which would make a // comment swallow the rest of the script.

The compiled text must not contain <, >, & or " so it can sit raw in the XML
attribute with no escaping, which is what makes it survive a round trip through
the XOT editor and the SCORM export unchanged. That is checked here.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "source" / "scorm_progress.js"
TARGETS = [ROOT / "source" / "data.xml", ROOT / "source" / "preview.xml"]

FORBIDDEN = {"<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;"}
ATTR_RE = re.compile(r'(<learningObject\b[^>]*?\sscript=")([^"]*)(")', re.DOTALL)


def compile_script(js: str) -> str:
    """Strip comments and collapse the script to a single line."""
    js = re.sub(r"/\*.*?\*/", " ", js, flags=re.DOTALL)
    js = re.sub(r"(?m)//.*$", "", js)
    js = re.sub(r"\s+", " ", js).strip()
    return js


def check_compiled(compiled: str, source: str = "") -> list[str]:
    """Return a list of problems with the compiled one-liner."""
    problems = []
    # Comment stripping is naive: a /* or */ that appears inside a string
    # literal would silently delete everything up to the next one, and
    # `node --check` would still accept the result. Every function the source
    # defines must survive into the output.
    for name in re.findall(r"\bfunction\s+(\w+)\s*\(", source):
        if f"function {name}(" not in compiled:
            problems.append(
                f"function {name}() disappeared during compilation - a comment "
                "marker inside a string literal can silently delete code"
            )
    for char in FORBIDDEN:
        if char in compiled:
            problems.append(
                f"compiled script contains {char!r}, which would need XML escaping "
                f"({FORBIDDEN[char]}); rewrite the source to avoid it"
            )
    if "//" in compiled:
        problems.append("compiled script still contains '//' (a line comment or a URL)")
    if "\n" in compiled:
        problems.append("compiled script is not a single line")
    if not compiled.startswith("(function"):
        problems.append("compiled script does not start with '(function'")
    if shutil.which("node"):
        proc = subprocess.run(
            ["node", "--check", "-"], input=compiled, text=True, capture_output=True
        )
        if proc.returncode != 0:
            problems.append(f"node --check rejected the compiled script: {proc.stderr.strip()}")
    return problems


def replace_attribute(xml: str, compiled: str, path: Path) -> str:
    match = ATTR_RE.search(xml)
    if not match:
        sys.exit(f"{path}: no script=\"...\" attribute found on <learningObject>")
    return xml[: match.start(2)] + compiled + xml[match.end(2) :]


def current_attribute(xml: str, path: Path) -> str:
    match = ATTR_RE.search(xml)
    if not match:
        sys.exit(f"{path}: no script=\"...\" attribute found on <learningObject>")
    return match.group(2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit non-zero if the XML is out of date",
    )
    args = parser.parse_args()

    source = SOURCE.read_text(encoding="utf-8")
    compiled = compile_script(source)
    problems = check_compiled(compiled, source)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    print(f"{SOURCE.relative_to(ROOT)} compiles to {len(compiled)} characters")

    stale = []
    for target in TARGETS:
        xml = target.read_text(encoding="utf-8")
        if current_attribute(xml, target) == compiled:
            print(f"{target.relative_to(ROOT)}: up to date")
            continue
        if args.check:
            stale.append(target)
            continue
        target.write_text(replace_attribute(xml, compiled, target), encoding="utf-8")
        print(f"{target.relative_to(ROOT)}: script attribute updated")

    if stale:
        names = ", ".join(str(t.relative_to(ROOT)) for t in stale)
        print(
            f"ERROR: {names} out of date - run 'python3 tools/sync_root_script.py'",
            file=sys.stderr,
        )
        return 1

    first = TARGETS[0].read_bytes()
    for target in TARGETS[1:]:
        if target.read_bytes() != first:
            print(
                f"ERROR: {target.relative_to(ROOT)} differs from "
                f"{TARGETS[0].relative_to(ROOT)}; they must stay byte-identical",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
