#!/usr/bin/env python3
"""Behavioural tests for the SCORM 1.2 tracking of an exported course package.

These run the *real* exported package (real XOT engine, real template.xml) in
headless Chromium against a mock SCORM 1.2 LMS API, so they exercise the same
code path that runs in a learner's LMS.

    python3 tests/test_scorm_tracking.py path/to/Secure_code_development_scorm.zip
    python3 tests/test_scorm_tracking.py <zip> --test resume   # substring filter

Every test is written against a behaviour that was reported from a real LMS
attempt; see docs/PROJECT_CONTEXT.md ("SCORM resume, completion and score
tracking") for the analysis behind each one.
"""

from __future__ import annotations

import argparse
import functools
import glob
import http.server
import json
import socketserver
import sys
import tempfile
import threading
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

# The course structure the tests assert against. page_nr is the index into the
# engine's x_pages array, which includes the table-of-contents page at 0, so
# page_nr = (index of the page in data.xml) + 1.
MENU_PAGE = 0                   # the table of contents Xerte inserts at x_pages[0]
FIRST_CONTENT_PAGE = 1          # "Welcome & how to use this course"
LAST_CONTENT_PAGE = 44          # "Course complete"
LAST_TRACKED_PAGE = 43          # final quiz; the last page is not marked
TRACKED_PAGES = 43              # len(state.toCompletePages)
NR_PAGES = 45                   # 44 content pages + the table of contents
THEME1_QUIZ = 9
QUIZ_PAGES = [9, 15, 21, 24, 30, 35, 38, 43]
QUESTIONS = 45                  # <question> nodes across the 8 quizzes
SUSPEND_LIMIT = 4096            # SCORM 1.2 cmi.suspend_data

# A minimal but honest SCORM 1.2 API. Records everything so tests can assert on
# what the package actually sent, including every intermediate suspend_data.
#
# It is installed on the top window only, because that is where a real LMS puts
# it: apiwrapper_1.2.js declares its own `var API = null` in the SCO's window,
# so the SCO always finds the adapter by walking up to its parent.
MOCK_API = """
(function () {
    if (window !== window.top) { return; }
    var store = %s;
    var lms = {
        log: [], suspends: [], commits: 0, initialised: false, finished: false,
        afterFinish: [], alerts: []
    };
    var maxInteraction = -1;
    window.__lms = lms;
    lms.get = function (key) { return store[key]; };
    lms.all = function () { return store; };
    window.API = {
        LMSInitialize: function () { lms.initialised = true; return 'true'; },
        LMSFinish: function () { lms.finished = true; return 'true'; },
        LMSGetValue: function (key) {
            if (key === 'cmi.interactions._count') { return String(maxInteraction + 1); }
            if (store[key] === undefined) { return ''; }
            return String(store[key]);
        },
        LMSSetValue: function (key, value) {
            store[key] = String(value);
            lms.log.push([key, String(value)]);
            if (lms.finished) { lms.afterFinish.push(key); }
            var m = /^cmi\\.interactions\\.(\\d+)\\./.exec(key);
            if (m) { maxInteraction = Math.max(maxInteraction, Number(m[1])); }
            if (key === 'cmi.suspend_data') { lms.suspends.push(String(value)); }
            return 'true';
        },
        LMSCommit: function () { lms.commits++; return 'true'; },
        LMSGetLastError: function () { return '0'; },
        LMSGetErrorString: function () { return 'No error'; },
        LMSGetDiagnostic: function () { return ''; }
    };
})();
"""

DEFAULT_CMI = {
    "cmi.core.student_id": "test-learner",
    "cmi.core.student_name": "Learner, Test",
    "cmi.core.lesson_location": "",
    "cmi.core.credit": "credit",
    "cmi.core.lesson_status": "not attempted",
    "cmi.core.entry": "ab-initio",
    "cmi.core.total_time": "0000:00:00.00",
    "cmi.core.lesson_mode": "normal",
    "cmi.core.exit": "",
    "cmi.core.score._children": "raw,min,max",
    "cmi.core.score.raw": "",
    "cmi.core.score.min": "",
    "cmi.core.score.max": "",
    "cmi.suspend_data": "",
    "cmi.launch_data": "",
    "cmi.comments": "",
    "cmi.objectives._children": "id,score,status",
    "cmi.objectives._count": "0",
    "cmi.student_data._children": "mastery_score,max_time_allowed,time_limit_action",
    "cmi.student_data.mastery_score": "",
    "cmi.interactions._children": (
        "id,objectives,time,type,correct_responses,weighting,student_response,"
        "result,latency"
    ),
}

SELECT_CORRECT_OPTIONS = """
() => {
    const inputs = window.jQuery('#optionHolder input');
    let picked = 0;
    inputs.each(function () {
        const correct = window.jQuery(this).data('correct');
        if (correct === 'true' || correct === true) {
            window.jQuery(this).prop('checked', true).trigger('change');
            picked++;
        }
    });
    return {options: inputs.length, picked: picked};
}
"""

# Options are shuffled per attempt, so a wrong answer has to be chosen by its
# correct flag rather than by position.
SELECT_A_WRONG_OPTION = """
() => {
    const inputs = window.jQuery('#optionHolder input');
    let picked = 0;
    inputs.each(function () {
        if (picked) { return; }
        const correct = window.jQuery(this).data('correct');
        if (correct !== 'true' && correct !== true) {
            window.jQuery(this).prop('checked', true).trigger('change');
            picked++;
        }
    });
    return {options: inputs.length, picked: picked};
}
"""

# What the learner is left looking at once a question has been marked.
FEEDBACK_SHOWN = """
() => ({
    help: window.jQuery('#topFeedback').text().trim(),
    verdict: window.jQuery('#bottomFeedback').text().trim(),
    marking: window.jQuery('#feedbackGroup').attr('class') || ''
})
"""


# The SCO always runs inside a frame in an LMS; reproduce that.
LMS_SHELL = """<!doctype html>
<html><head><meta charset="utf-8"><title>Mock LMS</title></head>
<body style="margin:0">
<iframe id="sco" name="sco" src="scormRLO.htm"
        style="width:100vw;height:100vh;border:0"></iframe>
</body></html>
"""
SHELL_NAME = "mock-lms.html"


class Server:
    """Serve the unpacked package over HTTP (file:// breaks XHR of template.xml)."""

    def __init__(self, directory: Path):
        (directory / SHELL_NAME).write_text(LMS_SHELL, encoding="utf-8")
        handler = functools.partial(QuietHandler, directory=str(directory))
        self.httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/{SHELL_NAME}"

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D102 - silence the request log
        pass


class Session:
    """One SCO launch: the mock LMS shell page plus the course in its frame."""

    def __init__(self, page, url: str):
        self.page = page
        self.url = url
        self.page_errors: list[str] = []
        self.console_errors: list[str] = []
        self.dialogs: list[str] = []
        page.on("pageerror", lambda e: self.page_errors.append(str(e)))
        page.on(
            "console",
            lambda m: self.console_errors.append(m.text) if m.type == "error" else None,
        )
        page.on("dialog", self._on_dialog)

    def _on_dialog(self, dialog):
        self.dialogs.append(dialog.message)
        dialog.dismiss()

    @property
    def sco(self):
        frame = self.page.frame(name="sco")
        assert frame is not None, "the course frame is gone"
        return frame

    def open(self) -> None:
        self.page.goto(self.url, wait_until="domcontentloaded")
        self.page.wait_for_selector("#sco")
        self.sco.wait_for_function(
            "() => typeof x_currentPage !== 'undefined' && x_currentPage !== -1"
            " && typeof state !== 'undefined' && state.initialised",
            timeout=45000,
        )
        self.page.wait_for_timeout(300)
        assert not self.unfound_api(), (
            f"the course did not find the mock LMS API: {self.dialogs[:2]}"
        )

    def unfound_api(self) -> bool:
        return any("API" in message for message in self.dialogs)

    # --- inspection -------------------------------------------------------
    def lms(self, expression: str):
        return self.page.evaluate(f"() => {expression}")

    def cmi(self, key: str):
        return self.page.evaluate("k => window.__lms.get(k)", key)

    def suspends(self) -> list[str]:
        return self.page.evaluate("() => window.__lms.suspends")

    def current_page(self) -> int:
        return self.sco.evaluate("() => x_currentPage")

    def completed_pages(self) -> list[bool]:
        return self.sco.evaluate("() => state.completedPages")

    def status(self) -> str:
        return self.sco.evaluate("() => state.getSuccessStatus()")

    def raw_score(self) -> float:
        return float(self.sco.evaluate("() => state.getRawScore()"))

    def page_scores(self) -> dict:
        return self.sco.evaluate(
            "() => { const out = {};"
            " state.interactions.forEach(function (it) {"
            "   if (it.ia_nr === -1 && Number(it.weighting) !== 0) {"
            "     out[String(it.page_nr)] = [Number(it.score), Number(it.weighting)]; } });"
            " return out; }"
        )

    def visible_text(self) -> str:
        return self.sco.inner_text("body")

    # --- driving ----------------------------------------------------------
    def goto(self, page_nr: int, dwell: int = 300) -> None:
        self.sco.evaluate("n => x_changePage(n, true)", page_nr)
        self.sco.wait_for_function(
            "n => x_currentPage === n && x_pageInfo[n].built !== false",
            arg=page_nr,
            timeout=20000,
        )
        # the engine ignores page visits shorter than 100ms (exit() returns false)
        self.page.wait_for_timeout(dwell)

    def answer_quiz(self, correctly: bool = True) -> int:
        """Answer every question on the current quiz page through the UI."""
        questions = self.sco.evaluate(
            "() => (typeof quiz !== 'undefined' && quiz.questions) ? quiz.questions.length : 0"
        )
        assert questions, "not on a quiz page"
        for index in range(questions):
            self.sco.wait_for_selector("#optionHolder input", timeout=15000)
            if correctly:
                picked = self.sco.evaluate(SELECT_CORRECT_OPTIONS)
                assert picked["picked"], f"no correct option found for question {index}"
            else:
                self.sco.evaluate(
                    "() => window.jQuery('#optionHolder input').first()"
                    ".prop('checked', true).trigger('change')"
                )
            self.sco.evaluate("() => window.jQuery('#checkBtn').trigger('click')")
            self.page.wait_for_timeout(150)
            # Next moves on, and on the last question it is what shows the
            # results, which is where the quiz reports its score (XTSetPageScore)
            self.sco.evaluate("() => window.jQuery('#nextBtn').trigger('click')")
            self.page.wait_for_timeout(150)
        assert self.sco.evaluate("() => quiz.currentQ") == questions, (
            "the quiz did not reach its results screen, so it reported no score"
        )
        return questions

    def answer_question(self, correctly: bool) -> dict:
        """Answer the question now on screen and return the feedback shown."""
        self.sco.wait_for_selector("#optionHolder input", timeout=15000)
        picked = self.sco.evaluate(
            SELECT_CORRECT_OPTIONS if correctly else SELECT_A_WRONG_OPTION
        )
        assert picked["picked"], f"no option to pick: {picked}"
        self.sco.evaluate("() => window.jQuery('#checkBtn').trigger('click')")
        self.page.wait_for_timeout(300)
        return self.sco.evaluate(FEEDBACK_SHOWN)

    def next_question(self) -> None:
        self.sco.evaluate("() => window.jQuery('#nextBtn').trigger('click')")
        self.page.wait_for_timeout(200)

    def terminate(self) -> None:
        self.sco.evaluate("() => XTTerminate()")
        self.page.wait_for_timeout(200)


class Harness:
    def __init__(self, package: Path, browser, server: Server):
        self.package = package
        self.browser = browser
        self.server = server

    @contextmanager
    def session(self, cmi: dict | None = None):
        data = dict(DEFAULT_CMI)
        data.update(cmi or {})
        context = self.browser.new_context(viewport={"width": 1280, "height": 900})
        context.add_init_script(MOCK_API % json.dumps(data))
        page = context.new_page()
        session = Session(page, self.server.url)
        try:
            yield session
        finally:
            context.close()

    def resumed(self, suspend_data: str, extra: dict | None = None):
        cmi = {
            "cmi.core.entry": "resume",
            "cmi.core.lesson_status": "incomplete",
            "cmi.suspend_data": suspend_data,
        }
        cmi.update(extra or {})
        return self.session(cmi)


# --------------------------------------------------------------------------
# helpers shared by the tests
# --------------------------------------------------------------------------

def corrupt_record(completed: int = TRACKED_PAGES) -> str:
    """The suspend_data shape reported from the affected learner's attempt.

    The engine writes exactly this when getVars() runs while currentpageid is
    blank: a null in the interactions array and no resume point.
    """
    return json.dumps(
        {
            "currentid": "",
            "currentpageid": "",
            "trackingmode": "full",
            "scoremode": "last",
            "nrpages": NR_PAGES,
            "pages_visited": 6,
            "completedPages": [True] * 5 + [False] * (completed - 5),
            "duration_previous_attempts": 0,
            "lo_type": "interactive",
            "lo_passed": 80,
            "page_timout": 0,
            "lo_completed": "unknown",
            "interactions": [None],
            "pageHistory": [1, 2, 3, 4, 5],
            "pagesViewed": [0, 1, 2, 3, 4, 5],
        }
    )


def parse_suspends(raw: list[str]) -> list[dict]:
    out = []
    for entry in raw:
        if not entry:
            continue
        out.append(json.loads(entry))
    return out


def panel_text(s: Session, page_nr: int) -> str:
    """The 'Your progress' panel rendered on the given (already built) page."""
    return s.sco.inner_text(f"#x_page{page_nr} .xtStatusPanel")


def lms_status_shown(s: Session, page_nr: int) -> str:
    return s.sco.get_attribute(f"#x_page{page_nr} .xtLmsStatus", "data-status")


UNTICKED_PAGES = """
() => {
    const out = [];
    const offset = XENITH.PAGEMENU.menuPage ? 1 : 0;
    window.jQuery('#x_page0 .menuItem').each(function () {
        if (window.jQuery(this).find('i.notvisited').length) {
            out.push(x_normalPages[window.jQuery(this).data('pageIndex') + offset]);
        }
    });
    return out;
}
"""

VIEWED_PAGES = """
() => {
    const out = [];
    x_pageInfo.forEach(function (p, i) { if (p.viewed === true) { out.push(i); } });
    return out;
}
"""

PENDING_QUIZ_TICKS = """
() => {
    const out = [];
    const offset = XENITH.PAGEMENU.menuPage ? 1 : 0;
    window.jQuery('#x_page0 .menuItem').each(function () {
        if (window.jQuery(this).find('i.xtPending').length) {
            out.push(x_normalPages[window.jQuery(this).data('pageIndex') + offset]);
        }
    });
    return out;
}
"""


MILESTONE_MARKERS = """
() => window.jQuery('#x_headerProgress .progressMarker').map(function () {
    return {complete: window.jQuery(this).hasClass('complete'), title: this.getAttribute('title')};
}).get()
"""


def milestone_markers(s: Session) -> list[dict]:
    """The header progress bar's milestone markers, in order: complete flag and title."""
    return s.sco.evaluate(MILESTONE_MARKERS)


def pending_quiz_ticks(s: Session) -> list[int]:
    """Page indexes whose contents-page tick is the 'quiz not yet submitted' marker."""
    return s.sco.evaluate(PENDING_QUIZ_TICKS)


def unticked_pages(s: Session) -> list[int]:
    """Page indexes the contents page still shows as never visited."""
    return s.sco.evaluate(UNTICKED_PAGES)


def viewed_pages(s: Session) -> list[int]:
    """Page indexes the engine currently considers viewed."""
    return s.sco.evaluate(VIEWED_PAGES)


def assert_resumable(record: dict, where: str) -> None:
    interactions = record.get("interactions")
    assert isinstance(interactions, list), f"{where}: interactions is not a list"
    for item in interactions:
        assert item is not None, (
            f"{where}: saved an interactions array containing null - resuming from "
            "this record throws \"Cannot read properties of null (reading 'page_nr')\""
        )
        assert isinstance(item.get("page_nr"), int), f"{where}: interaction without page_nr"
    ids = [item["id"] for item in interactions]
    resume = record.get("currentpageid")
    assert resume, f"{where}: no resume point saved (currentpageid is blank)"
    assert resume in ids, f"{where}: resume point {resume!r} is not in the saved interactions"


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


@test
def test_package_sanity(h: Harness):
    """The exported package carries the tracking configuration we expect."""
    with zipfile.ZipFile(h.package) as zf:
        template = zf.read("template.xml").decode("utf-8")
    assert 'trackingMode="full"' in template, "trackingMode is not 'full'"
    assert 'trackingPassed="80%"' in template, "pass mark is not 80%"
    assert template.count("<question") == 45, (
        f"expected 45 questions, found {template.count('<question')}"
    )
    assert 'unmarkForCompletion="true"' in template, "Welcome page is no longer unmarked"
    assert "xPersistProgress" in template, "root progress script is missing"
    assert 'progressBarType="header2"' in template, "header progress bar is not enabled"
    assert template.count('milestone="true"') == len(QUIZ_PAGES), (
        "every quiz page should be a progress-bar milestone"
    )
    assert template.count("xtStatusPanel") >= 3, (
        "expected the status panel placeholder in the menu text, on the Course "
        "complete page and in the script"
    )
    compiled = (ROOT / "source" / "scorm_progress.js")
    if compiled.exists():
        # the attribute in the package must be the compiled source, not a hand-edit
        sys.path.insert(0, str(ROOT / "tools"))
        from sync_root_script import compile_script  # noqa: PLC0415

        expected = compile_script(compiled.read_text(encoding="utf-8"))
        assert expected in template, (
            "the package's script attribute is not the compiled source/scorm_progress.js "
            "- run python3 tools/sync_root_script.py"
        )


@test
def test_fresh_launch_tracks_first_page(h: Harness):
    """A fresh launch initialises tracking and marks the first page complete."""
    with h.session() as s:
        s.open()
        assert s.current_page() == MENU_PAGE, (
            f"a fresh launch should open the contents page, got {s.current_page()}"
        )
        assert len(s.completed_pages()) == TRACKED_PAGES, (
            f"expected {TRACKED_PAGES} tracked pages, got {len(s.completed_pages())}"
        )
        assert s.lms("window.__lms.initialised") is True, "LMSInitialize was not called"
        s.goto(FIRST_CONTENT_PAGE)
        s.goto(FIRST_CONTENT_PAGE + 1)
        assert s.completed_pages()[0] is True, "leaving the Welcome page did not mark it complete"
        assert s.lms("window.__lms.commits") > 0, "no progress was committed to the LMS"
        assert not s.page_errors, f"page errors: {s.page_errors}"


@test
def test_saved_progress_is_always_resumable(h: Harness):
    """Every committed suspend_data must be safe to resume from.

    Regression test for the reported crash: the engine serialises the resume
    point as find(currentpageid), which is null between leaving one page and
    entering the next, so it used to persist "interactions":[null].
    """
    with h.session() as s:
        s.open()
        for page_nr in range(FIRST_CONTENT_PAGE + 1, FIRST_CONTENT_PAGE + 5):
            s.goto(page_nr)
        s.terminate()
        records = parse_suspends(s.suspends())
        assert records, "nothing was written to cmi.suspend_data"
        for index, record in enumerate(records):
            assert_resumable(record, f"suspend_data write #{index + 1}")
            assert len(record["completedPages"]) == TRACKED_PAGES, (
                f"suspend_data write #{index + 1}: completedPages has "
                f"{len(record['completedPages'])} entries, expected {TRACKED_PAGES}"
            )
        for raw in s.suspends():
            assert len(raw) <= SUSPEND_LIMIT, (
                f"suspend_data is {len(raw)} characters, over the SCORM 1.2 "
                f"{SUSPEND_LIMIT} character limit"
            )


@test
def test_loads_with_corrupt_resume_record(h: Harness):
    """The reported failure: a null in interactions must not stop the course."""
    with h.resumed(corrupt_record()) as s:
        s.open()
        assert not any("page_nr" in e for e in s.page_errors), (
            f"start-up threw on the saved record: {s.page_errors}"
        )
        assert not s.page_errors, f"page errors: {s.page_errors}"
        text = s.visible_text()
        assert "Secure code development" in text, "the course title did not render"
        assert len(text) > 200, f"the course rendered almost nothing: {len(text)} characters"
        assert len(s.completed_pages()) == TRACKED_PAGES, (
            "completed pages were lost while healing the record"
        )
        assert s.completed_pages()[:5] == [True] * 5, "restored progress was discarded"


@test
def test_blank_resume_point_still_loads(h: Harness):
    """A record with a blank resume point starts at the beginning, not an error."""
    record = json.loads(corrupt_record())
    record["interactions"] = []
    with h.resumed(json.dumps(record)) as s:
        s.open()
        assert not s.page_errors, f"page errors: {s.page_errors}"
        assert s.current_page() == MENU_PAGE, (
            f"expected to start at the contents page, got {s.current_page()}"
        )


@test
def test_terminate_on_the_contents_page_is_resumable(h: Harness):
    """Saving from the table of contents must still produce a resumable record.

    The engine skips XTEnterPage on a revisit to the contents page, so
    currentpageid is still blank from the last page exit and finishTracking()
    serialises a null interaction.
    """
    with h.session() as s:
        s.open()
        s.goto(4)
        s.goto(MENU_PAGE)
        s.terminate()
        suspend = s.cmi("cmi.suspend_data")
    assert_resumable(json.loads(suspend), "record saved from the contents page")
    with h.resumed(suspend) as s:
        s.open()
        assert not s.page_errors, f"resuming that record failed: {s.page_errors}"


@test
def test_out_of_range_pages_viewed_is_dropped(h: Harness):
    """A record naming pages this build does not have must not stop start-up.

    x_restorePagesViewed() writes x_pageInfo[i].viewed with no bounds check, so
    a record from a build with more pages throws during setVars().
    """
    with h.session() as s:
        s.open()
        s.goto(3)
        s.terminate()
        record = json.loads(s.cmi("cmi.suspend_data"))
    record["pagesViewed"] = [0, 1, 2, 3, 99]
    record["pageHistory"] = [1, 2, 3, 120]
    with h.resumed(json.dumps(record)) as s:
        s.open()
        assert not s.page_errors, f"page errors: {s.page_errors}"
        viewed = s.sco.evaluate(
            "() => x_pageInfo.filter(function (p) { return p.viewed; }).length"
        )
        assert viewed >= 3, f"restored page ticks were lost: {viewed}"


@test
def test_resume_point_from_a_removed_page_is_dropped(h: Harness):
    """A record naming a page index this build does not have must still load.

    The same blank course as a null interaction, one step later: XTStartPage
    hands the saved page_nr to the player, which indexes x_pageInfo without a
    bounds check. This is what a learner sees when pages are removed from the
    course between their attempts.
    """
    with h.session() as s:
        s.open()
        s.goto(3)
        s.terminate()
        record = json.loads(s.cmi("cmi.suspend_data"))

    entry = record["interactions"][0]
    entry["page_nr"] = 60
    entry["page_ref"] = 61
    entry["id"] = "urn:x-xerte:p-61:A_page_from_an_older_build"
    record["currentpageid"] = entry["id"]
    with h.resumed(json.dumps(record)) as s:
        s.open()
        assert not s.page_errors, f"start-up threw on a stale resume point: {s.page_errors}"
        assert s.current_page() == MENU_PAGE, (
            f"expected to fall back to the contents page, got {s.current_page()}"
        )
        assert len(s.completed_pages()) == TRACKED_PAGES, "progress was lost"


@test
def test_nothing_is_saved_after_lms_finish(h: Harness):
    """Once the SCO has called LMSFinish, the autosave must stay quiet.

    The engine never sets state.finished, so the guard on it does nothing:
    onbeforeunload runs XTTerminate and the later pagehide autosaved again,
    which a conformant LMS rejects with error 301.
    """
    with h.session() as s:
        s.open()
        s.goto(2)
        s.terminate()
        assert s.lms("window.__lms.finished") is True, "LMSFinish was not called"
        # the browser fires pagehide after onbeforeunload; the heartbeat can also land
        s.sco.evaluate("() => window.dispatchEvent(new Event('pagehide'))")
        s.sco.evaluate("() => window.xPersistProgress()")
        s.page.wait_for_timeout(200)
        late = s.lms("window.__lms.afterFinish")
        assert late == [], f"wrote to the LMS after LMSFinish: {late}"


@test
def test_mid_page_save_records_the_page_as_exited(h: Harness):
    """A save taken mid-page must persist the resume entry as exited.

    finishTracking's own records do. The engine only calls reenter() for an
    'exited' interaction, so a record saved as 'entered' kept its old start
    timestamp and the next session's first page exit reported a duration
    spanning the gap between sessions.
    """
    with h.session() as s:
        s.open()
        s.goto(5)
        s.sco.evaluate("() => window.xPersistProgress()")
        raw = s.cmi("cmi.suspend_data")
        record = json.loads(raw)
        entry = next(i for i in record["interactions"] if i["id"] == record["currentpageid"])
        assert entry["state"] == "exited", (
            f"resume entry was saved as {entry['state']!r}, so the next session's "
            "first page exit would report a duration spanning the gap"
        )
        assert s.sco.evaluate("() => state.find(state.currentpageid).state") == "entered", (
            "the live interaction was mutated; only the saved copy may differ"
        )

    with h.resumed(raw) as s:
        s.open()
        assert s.current_page() == 5, f"expected to resume on page 5, got {s.current_page()}"


@test
def test_stale_completed_pages_are_resized(h: Harness):
    """completedPages from a different build must be resized, not trusted.

    getSuccessStatus() walks the saved array, so a short one can report
    completion early and a long one can block completion forever. Built from a
    genuine record so this tests only the resizing.
    """
    with h.session() as s:
        s.open()
        # answer a quiz so the record is 'interactive' and its status is meaningful
        s.goto(THEME1_QUIZ)
        s.answer_quiz()
        s.goto(THEME1_QUIZ + 1)
        s.terminate()
        genuine = s.cmi("cmi.suspend_data")

    short = json.loads(genuine)
    short["completedPages"] = [True] * 20
    with h.resumed(json.dumps(short)) as s:
        s.open()
        assert len(s.completed_pages()) == TRACKED_PAGES, (
            f"a 20-entry completedPages was not resized to {TRACKED_PAGES}: "
            f"{len(s.completed_pages())}"
        )
        assert s.status() == "incomplete", (
            "a short completedPages array reported completion for an unfinished course"
        )

    long = json.loads(genuine)
    long["completedPages"] = [True] * 60
    with h.resumed(json.dumps(long)) as s:
        s.open()
        assert len(s.completed_pages()) == TRACKED_PAGES, (
            f"a 60-entry completedPages was not resized to {TRACKED_PAGES}: "
            f"{len(s.completed_pages())}"
        )
        assert s.status() != "incomplete", (
            "an over-long completedPages array blocked completion"
        )


@test
def test_oversized_progress_is_trimmed_not_broken(h: Harness):
    """A record that would not fit sheds page history, never scores or completion.

    cmi.suspend_data is capped at 4096 characters in SCORM 1.2, and page history
    grows with every page a learner visits. When the record would not fit, the
    oldest history goes first; the resume point, completion and quiz scores stay.
    """
    with h.session() as s:
        s.open()
        for page_nr in QUIZ_PAGES:
            s.goto(page_nr, dwell=160)
            s.answer_quiz()
        s.goto(20, dwell=160)
        # a learner who has wandered far more than the record could ever hold
        s.sco.evaluate(
            "n => { x_pageHistory = [];"
            " for (var i = 0; i < n; i++) { x_pageHistory.push(1 + (i % 44)); } }",
            5000,
        )
        s.sco.evaluate("() => window.xPersistProgress()")
        raw = s.cmi("cmi.suspend_data")
        assert len(raw) <= SUSPEND_LIMIT, (
            f"suspend_data is {len(raw)} characters, over the SCORM 1.2 "
            f"{SUSPEND_LIMIT} character limit"
        )
        record = json.loads(raw)
        assert_resumable(record, "trimmed record")
        assert len(record["completedPages"]) == TRACKED_PAGES, "completion was shed"
        remembered = {row[0] for row in record.get("xtPages", [])}
        assert remembered == set(QUIZ_PAGES), (
            f"quiz scores were shed before page history: kept {sorted(remembered)}"
        )
        assert len(record.get("pageHistory", [])) <= 20, (
            f"page history was not trimmed: {len(record.get('pageHistory', []))} entries"
        )

    with h.resumed(raw) as s:
        s.open()
        assert not s.page_errors, f"the trimmed record did not resume: {s.page_errors}"
        assert s.raw_score() == 100, (
            f"score after resuming from the trimmed record is {s.raw_score()}, expected 100"
        )


@test
def test_resume_returns_to_the_saved_page(h: Harness):
    """A normal save/resume cycle puts the learner back where they were."""
    with h.session() as s:
        s.open()
        s.goto(12)
        s.terminate()
        suspend = s.cmi("cmi.suspend_data")
    record = json.loads(suspend)
    assert_resumable(record, "record saved at terminate")
    with h.resumed(suspend) as s:
        s.open()
        assert s.current_page() == 12, f"expected to resume on page 12, got {s.current_page()}"
        assert not s.page_errors, f"page errors: {s.page_errors}"


@test
def test_quiz_score_is_reported(h: Harness):
    """Finishing a quiz reports a score and per-question interactions."""
    with h.session() as s:
        s.open()
        s.goto(THEME1_QUIZ)
        answered = s.answer_quiz()
        assert answered == 4, f"Theme 1 quiz should have 4 questions, got {answered}"
        s.goto(THEME1_QUIZ + 1)
        scores = s.page_scores()
        assert str(THEME1_QUIZ) in scores, "the quiz page recorded no score"
        assert scores[str(THEME1_QUIZ)][0] == 100, (
            f"all-correct quiz scored {scores[str(THEME1_QUIZ)][0]}, expected 100"
        )
        assert s.raw_score() == 100, f"cmi.core.score.raw would be {s.raw_score()}, expected 100"
        assert float(s.cmi("cmi.core.score.raw")) == 100, (
            f"the LMS was sent score.raw={s.cmi('cmi.core.score.raw')}"
        )
        interactions = s.lms(
            "window.__lms.log.filter(e => /^cmi\\.interactions\\.\\d+\\.id$/.test(e[0])).length"
        )
        assert interactions >= 4, f"only {interactions} interactions were logged"


@test
def test_quiz_scores_survive_a_resume(h: Harness):
    """Quiz scores must not be lost when a learner comes back in a new session.

    The engine persists only the current page's interaction, so page scores were
    dropped on resume and cmi.core.score.raw fell back to 0 for a learner with
    plenty of logged interactions.
    """
    with h.session() as s:
        s.open()
        s.goto(THEME1_QUIZ)
        s.answer_quiz()
        s.goto(THEME1_QUIZ + 1)
        assert s.raw_score() == 100, f"in-session score.raw is {s.raw_score()}, expected 100"
        s.terminate()
        suspend = s.cmi("cmi.suspend_data")

    with h.resumed(suspend) as s:
        s.open()
        scores = s.page_scores()
        assert str(THEME1_QUIZ) in scores, (
            "the Theme 1 quiz score was lost on resume - the LMS grade would drop to 0"
        )
        assert scores[str(THEME1_QUIZ)][0] == 100, (
            f"restored quiz score is {scores[str(THEME1_QUIZ)][0]}, expected 100"
        )
        assert scores[str(THEME1_QUIZ)][1] == 1, "restored quiz weighting is wrong"
        assert s.raw_score() == 100, (
            f"after resuming, score.raw would be {s.raw_score()} instead of 100"
        )
        # and it is reported to the LMS without the learner redoing anything
        s.goto(THEME1_QUIZ + 2)
        assert float(s.cmi("cmi.core.score.raw")) == 100, (
            f"resumed session reported score.raw={s.cmi('cmi.core.score.raw')}"
        )


@test
def test_weighted_score_across_two_sessions(h: Harness):
    """The final quiz is 75% of the grade even if it is answered in a later session."""
    with h.session() as s:
        s.open()
        s.goto(THEME1_QUIZ)
        s.answer_quiz(correctly=False)
        s.goto(THEME1_QUIZ + 1)
        first_score = s.raw_score()
        s.terminate()
        suspend = s.cmi("cmi.suspend_data")

    with h.resumed(suspend) as s:
        s.open()
        s.goto(43)
        s.answer_quiz()
        s.goto(LAST_CONTENT_PAGE)
        score = s.raw_score()
    # theme quiz weight 1 (scored `first_score`), final quiz weight 21 (scored 100)
    expected = round((first_score * 1 + 100 * 21) / 22, 2)
    assert abs(score - expected) < 0.5, (
        f"weighted score across sessions is {score}, expected about {expected} "
        f"(theme quiz {first_score} at weight 1, final quiz 100 at weight 21)"
    )


@test
def test_full_walkthrough_reports_passed(h: Harness):
    """A learner who works through every page and quiz completes and passes.

    Guards the completion path end to end: all 43 marked pages, the 80% pass
    mark, and the weighted score.
    """
    with h.session() as s:
        s.open()
        for page_nr in range(FIRST_CONTENT_PAGE, LAST_CONTENT_PAGE + 1):
            s.goto(page_nr, dwell=160)
            if page_nr in QUIZ_PAGES:
                s.answer_quiz()
        # leaving the last tracked page is what completes the course
        s.goto(LAST_TRACKED_PAGE, dwell=160)
        s.goto(LAST_CONTENT_PAGE, dwell=160)
        completed = s.completed_pages()
        missing = [i for i, done in enumerate(completed) if not done]
        assert not missing, (
            f"pages still incomplete after visiting everything: toCompletePages indexes {missing}"
        )
        assert s.status() == "passed", f"lesson status is {s.status()!r}, expected 'passed'"
        assert s.raw_score() == 100, f"score.raw is {s.raw_score()}, expected 100"
        # the Course complete page reports the same thing the LMS was told
        shown = panel_text(s, LAST_CONTENT_PAGE)
        assert f"Required pages completed: {TRACKED_PAGES} of {TRACKED_PAGES}" in shown, shown
        assert "LMS status: Passed" in shown, shown
        assert lms_status_shown(s, LAST_CONTENT_PAGE) == "passed"
        assert "not yet submitted" not in shown, shown
        s.terminate()
        assert s.cmi("cmi.core.lesson_status") == "passed", (
            f"the LMS was told lesson_status={s.cmi('cmi.core.lesson_status')!r}"
        )
        assert float(s.cmi("cmi.core.score.raw")) == 100, (
            f"the LMS was told score.raw={s.cmi('cmi.core.score.raw')!r}"
        )
        assert s.lms("window.__lms.finished") is True, "LMSFinish was not called"
        assert not s.page_errors, f"page errors: {s.page_errors}"
        # the fullest record the course can produce still has to fit and resume
        records = s.suspends()
        biggest = max(len(raw) for raw in records)
        assert biggest <= SUSPEND_LIMIT, (
            f"the largest suspend_data write is {biggest} characters, over the "
            f"SCORM 1.2 {SUSPEND_LIMIT} character limit"
        )
        final = json.loads(records[-1])
        assert_resumable(final, "record saved at the end of the course")
        remembered = {row[0] for row in final.get("xtPages", [])}
        assert remembered == set(QUIZ_PAGES), (
            f"the finished record remembers scores for {sorted(remembered)}, "
            f"expected all quiz pages {QUIZ_PAGES}"
        )


@test
def test_completion_survives_a_resume(h: Harness):
    """Progress from a first session still counts towards completion later."""
    with h.session() as s:
        s.open()
        for page_nr in range(FIRST_CONTENT_PAGE, 20):
            s.goto(page_nr, dwell=160)
            if page_nr in QUIZ_PAGES:
                s.answer_quiz()
        s.terminate()
        suspend = s.cmi("cmi.suspend_data")
        first_half = [i for i, done in enumerate(s.completed_pages()) if done]

    with h.resumed(suspend) as s:
        s.open()
        restored = [i for i, done in enumerate(s.completed_pages()) if done]
        assert restored == first_half, (
            f"completed pages changed across the resume: {first_half} -> {restored}"
        )
        for page_nr in range(20, LAST_CONTENT_PAGE + 1):
            s.goto(page_nr, dwell=160)
            if page_nr in QUIZ_PAGES:
                s.answer_quiz()
        s.goto(LAST_TRACKED_PAGE, dwell=160)
        s.goto(LAST_CONTENT_PAGE, dwell=160)
        missing = [i for i, done in enumerate(s.completed_pages()) if not done]
        assert not missing, f"course did not complete across two sessions; missing {missing}"
        assert s.status() == "passed", f"lesson status is {s.status()!r}, expected 'passed'"


# --------------------------------------------------------------------------


@test
def test_status_panel_tells_the_learner_what_is_left(h: Harness):
    """The contents page shows required-page progress and the status the LMS holds.

    Reported problem: learners could not tell how far through the course they
    were or whether they had done what completion requires. Ticks only meant
    "opened" and SCORM 1.2 gives the LMS nothing but incomplete/passed/failed.
    """
    with h.session() as s:
        s.open()
        shown = panel_text(s, MENU_PAGE)
        assert f"Required pages completed: 0 of {TRACKED_PAGES}" in shown, shown
        assert "LMS status: Incomplete" in shown, shown
        assert lms_status_shown(s, MENU_PAGE) == "incomplete"
        assert "Theme 1 Quiz: not yet submitted" in shown, shown
        assert "Final comprehensive quiz: not yet submitted" in shown, shown
        assert "Pass mark: 80%" in shown, shown
        s.goto(FIRST_CONTENT_PAGE)
        s.goto(FIRST_CONTENT_PAGE + 1)
        s.goto(MENU_PAGE)
        # both pages were left after more than 100ms, so both count
        shown = panel_text(s, MENU_PAGE)
        assert f"Required pages completed: 2 of {TRACKED_PAGES}" in shown, shown
        # the pages still owed are named, decoded from their XML names
        assert "Still to visit:" in shown, shown
        assert "Welcome" not in shown.split("Still to visit:")[1], shown
        assert "Theme 1: Access Control, Authentication & Identity" in shown, shown
        assert "and " in shown and " more" in shown, f"long list was not truncated: {shown}"
        assert not s.page_errors, f"page errors: {s.page_errors}"


@test
def test_wrong_answer_gets_a_hint_and_an_explanation(h: Harness):
    """Getting a question wrong tells the learner why, and what to revisit.

    The help is authored on the question itself, which the quiz model renders
    on every submitted answer. Only a learner who got it wrong needs it, so
    the block is cleared again when the answer was right.
    """
    with h.session() as s:
        s.open()
        s.goto(THEME1_QUIZ)
        before = s.sco.evaluate(FEEDBACK_SHOWN)
        assert before["help"] == "", f"help shown before answering: {before}"
        wrong = s.answer_question(correctly=False)
        assert "incorrectFeedback" in wrong["marking"], wrong
        assert wrong["help"].startswith("Hint:"), f"no hint on a wrong answer: {wrong}"
        assert "Why:" in wrong["help"], f"no explanation on a wrong answer: {wrong}"
        s.next_question()
        right = s.answer_question(correctly=True)
        # "correctFeedback" is a substring of "incorrectFeedback", so match exactly
        assert right["marking"].split() == ["correctFeedback"], right
        assert right["help"] == "", f"a correct answer should not be given help: {right}"
        # clearing the help must not take the correct/incorrect line with it
        assert right["verdict"], f"the verdict was cleared too: {right}"
        # a second quiz page rebuilds the model object, which has to be re-wrapped
        s.goto(QUIZ_PAGES[1])
        again = s.answer_question(correctly=False)
        assert again["help"].startswith("Hint:"), f"not re-wrapped on a later quiz: {again}"
        s.next_question()
        still = s.answer_question(correctly=True)
        assert still["help"] == "", f"help not cleared on a later quiz: {still}"
        assert not s.page_errors, f"page errors: {s.page_errors}"


@test
def test_every_question_carries_wrong_answer_help(h: Harness):
    """No question is left without a hint and an explanation.

    The text lives in the course XML, so a question added later would silently
    have none: walk the parsed project and check all 45 of them.
    """
    with h.session() as s:
        s.open()
        walk = s.sco.evaluate(
            "() => { const out = []; let checked = 0;"
            " window.jQuery(x_pages).each(function () {"
            "   if (this.nodeName !== 'quiz') { return; }"
            "   window.jQuery(this).children('question').each(function () {"
            "     checked++;"
            "     const fb = this.getAttribute('feedback') || '';"
            "     if (fb.indexOf('Hint:') === -1 || fb.indexOf('Why:') === -1) {"
            "       out.push(this.getAttribute('name')); } }); });"
            " return {checked: checked, missing: out}; }"
        )
        # without this the walk finding nothing at all would pass silently
        assert walk["checked"] == QUESTIONS, f"walked {walk['checked']} questions, expected {QUESTIONS}"
        assert walk["missing"] == [], f"questions without a hint and explanation: {walk['missing']}"
        assert not s.page_errors, f"page errors: {s.page_errors}"


@test
def test_quiz_tick_means_submitted_not_opened(h: Harness):
    """A quiz that has been opened but not submitted gets a distinct marker.

    The engine ticks a page the moment it loads. For quiz pages that is
    misleading, so the tick is replaced until the quiz reports its score, and
    the 'submitted' flag has to survive a resume like the score does.
    """
    with h.session() as s:
        s.open()
        assert pending_quiz_ticks(s) == [], "nothing has been opened yet"
        s.goto(THEME1_QUIZ)
        s.goto(MENU_PAGE)
        assert pending_quiz_ticks(s) == [THEME1_QUIZ], (
            f"an opened, unsubmitted quiz should be marked pending: {pending_quiz_ticks(s)}"
        )
        assert "Theme 1 Quiz: not yet submitted" in panel_text(s, MENU_PAGE)
        s.goto(THEME1_QUIZ)
        s.answer_quiz()
        s.goto(MENU_PAGE)
        assert pending_quiz_ticks(s) == [], "a submitted quiz should have a normal tick"
        assert "Theme 1 Quiz: 100%" in panel_text(s, MENU_PAGE), panel_text(s, MENU_PAGE)
        s.terminate()
        saved = s.suspends()[-1]
        rows = {row[0]: row for row in json.loads(saved)["xtPages"]}
        assert rows[THEME1_QUIZ][5] == 1, f"submitted flag not persisted: {rows[THEME1_QUIZ]}"
        assert not s.page_errors, f"page errors: {s.page_errors}"
    with h.resumed(saved) as s:
        s.open()
        s.goto(MENU_PAGE)
        assert pending_quiz_ticks(s) == [], "the submitted flag was lost on resume"
        assert "Theme 1 Quiz: 100%" in panel_text(s, MENU_PAGE), panel_text(s, MENU_PAGE)
        assert milestone_markers(s)[0]["complete"] is True, "the quiz milestone was not lit on resume"
        assert not s.page_errors, f"page errors: {s.page_errors}"


@test
def test_older_records_infer_submission_from_the_score(h: Harness):
    """A record written before the submitted flag existed still shows a scored quiz as done."""
    record = corrupt_record()
    record_obj = json.loads(record)
    record_obj["interactions"] = []
    # five-element row, as written by builds before the submitted flag existed
    record_obj["xtPages"] = [[THEME1_QUIZ, 75, 1, 4, f"urn:x-xerte:p-{THEME1_QUIZ + 1}"]]
    record_obj["pagesViewed"] = [0, THEME1_QUIZ]
    with h.resumed(json.dumps(record_obj)) as s:
        s.open()
        s.goto(MENU_PAGE)
        assert THEME1_QUIZ not in pending_quiz_ticks(s), "a scored quiz was shown as unsubmitted"
        assert "Theme 1 Quiz: 75%" in panel_text(s, MENU_PAGE), panel_text(s, MENU_PAGE)


@test
def test_viewed_pages_survive_a_save_and_resume(h: Harness):
    """Ticks and the progress bar must still mean something after a resume.

    Both read `x_pageInfo[i].viewed`, which is session state: it survives only
    through the engine's `pagesViewed` field in the saved record
    (`x_pagesViewed()` -> `state.pagesViewed` -> `cmi.suspend_data` ->
    `setVars` -> `x_restorePagesViewed()`). A learner who saves, leaves and
    comes back to an empty progress bar and no ticks has lost that round trip.
    The two halves are asserted separately so a failure names which one broke.
    """
    seen = [FIRST_CONTENT_PAGE, FIRST_CONTENT_PAGE + 1, FIRST_CONTENT_PAGE + 2]
    with h.session() as s:
        s.open()
        for page_nr in seen:
            s.goto(page_nr)
        s.terminate()
        saved = s.suspends()[-1]
        record = json.loads(saved)
        # save side
        assert "pagesViewed" in record, (
            f"the saved record has no pagesViewed, so nothing can be restored: {sorted(record)}"
        )
        missing = [p for p in seen if p not in record["pagesViewed"]]
        assert not missing, f"visited pages missing from pagesViewed: {missing}"
        assert not s.page_errors, f"page errors: {s.page_errors}"
    # restore side
    with h.resumed(saved) as s:
        s.open()
        restored = viewed_pages(s)
        lost = [p for p in seen if p not in restored]
        assert not lost, f"pages lost their viewed flag on resume: {lost} (restored {restored})"
        s.goto(MENU_PAGE)
        label = s.sco.inner_text("#x_headerProgress .pbTxt")
        assert not label.startswith("0%"), f"progress bar empty after a resume: {label}"
        still_unticked = [p for p in seen if p in unticked_pages(s)]
        assert not still_unticked, f"contents-page ticks lost on resume: {still_unticked}"
        assert not s.page_errors, f"page errors: {s.page_errors}"


@test
def test_viewed_pages_survive_a_resume_late_in_the_course(h: Harness):
    """The same round trip for a learner who has actually done the work.

    `pagesViewed` is the second thing `fitBudget` sheds when the record will
    not fit `cmi.suspend_data`, ahead of the quiz scores, so the ticks and the
    progress bar are the first learner-visible casualty of a record that has
    grown. A learner saves after a real session, not after three pages.
    """
    walked = list(range(FIRST_CONTENT_PAGE, 36))
    with h.session() as s:
        s.open()
        for page_nr in walked:
            s.goto(page_nr, dwell=120)
            if page_nr in QUIZ_PAGES:
                s.answer_quiz()
        s.terminate()
        saved = s.suspends()[-1]
        record = json.loads(saved)
        assert len(saved) <= SUSPEND_LIMIT, f"record is {len(saved)} characters"
        assert "pagesViewed" in record, (
            f"pagesViewed was shed from a {len(saved)} character record: kept {sorted(record)}"
        )
        assert not s.page_errors, f"page errors: {s.page_errors}"
    with h.resumed(saved) as s:
        s.open()
        restored = viewed_pages(s)
        lost = [p for p in walked if p not in restored]
        assert not lost, f"pages lost their viewed flag on resume: {lost}"
        s.goto(MENU_PAGE)
        label = s.sco.inner_text("#x_headerProgress .pbTxt")
        assert not label.startswith("0%"), f"progress bar empty after a resume: {label}"
        assert not s.page_errors, f"page errors: {s.page_errors}"


@test
def test_header_progress_bar_counts_viewed_pages(h: Harness):
    """The header progress bar is on, labelled honestly, with a marker per quiz."""
    with h.session() as s:
        s.open()
        assert s.sco.locator("#x_headerProgress").count() == 1, "no header progress bar"
        label = s.sco.inner_text("#x_headerProgress .pbTxt")
        assert label.startswith("0%") and "of pages viewed" in label, label
        assert s.sco.locator("#x_headerProgress .progressMarker").count() == len(QUIZ_PAGES), (
            "expected one progress marker per quiz page"
        )
        s.goto(FIRST_CONTENT_PAGE)
        s.goto(FIRST_CONTENT_PAGE + 1)
        label = s.sco.inner_text("#x_headerProgress .pbTxt")
        assert not label.startswith("0%"), f"progress bar did not move: {label}"
        # a quiz milestone lights when the quiz is submitted, not when it is opened
        s.goto(THEME1_QUIZ)
        s.goto(MENU_PAGE)
        markers = milestone_markers(s)
        assert [m["complete"] for m in markers] == [False] * len(QUIZ_PAGES), (
            f"opening a quiz lit its milestone: {markers}"
        )
        assert "Theme 1 Quiz" in markers[0]["title"], markers[0]
        assert "not yet submitted" in markers[0]["title"], markers[0]
        s.goto(THEME1_QUIZ)
        s.answer_quiz()
        s.goto(MENU_PAGE)
        markers = milestone_markers(s)
        assert [m["complete"] for m in markers] == [True] + [False] * (len(QUIZ_PAGES) - 1), (
            f"submitting Theme 1 Quiz should light only its milestone: {markers}"
        )
        assert markers[0]["title"].endswith("Complete"), markers[0]
        assert not s.page_errors, f"page errors: {s.page_errors}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="exported SCORM 1.2 zip")
    parser.add_argument("--test", default="", help="only run tests matching this substring")
    parser.add_argument("--headed", action="store_true", help="show the browser")
    args = parser.parse_args()

    if not args.package.exists():
        print(f"no such package: {args.package}", file=sys.stderr)
        return 2

    selected = [t for t in TESTS if args.test in t.__name__]
    if not selected:
        print(f"no tests match {args.test!r}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        unpacked = Path(tmp) / "package"
        with zipfile.ZipFile(args.package) as zf:
            zf.extractall(unpacked)
        if not (unpacked / "scormRLO.htm").exists():
            print("package does not contain scormRLO.htm", file=sys.stderr)
            return 2

        server = Server(unpacked)
        failures = []
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=not args.headed,
                    executable_path=chromium_path(),
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
                harness = Harness(args.package, browser, server)
                for fn in selected:
                    name = fn.__name__.replace("test_", "", 1)
                    started = time.time()
                    try:
                        fn(harness)
                    except AssertionError as exc:
                        failures.append((name, str(exc)))
                        print(f"FAIL {name} ({time.time() - started:.1f}s)\n     {exc}")
                    except Exception as exc:  # noqa: BLE001 - report and continue
                        failures.append((name, f"{type(exc).__name__}: {exc}"))
                        print(f"ERROR {name} ({time.time() - started:.1f}s)\n     {exc}")
                    else:
                        print(f"PASS {name} ({time.time() - started:.1f}s)")
                browser.close()
        finally:
            server.stop()

    print()
    print(f"{len(selected) - len(failures)}/{len(selected)} passed")
    for name, message in failures:
        first = message.splitlines()[0] if message.strip() else "(assertion without a message)"
        print(f"  - {name}: {first}")
    return 1 if failures else 0


def chromium_path() -> str | None:
    """Use Playwright's own browser if present, else a preinstalled Chromium."""
    for pattern in (
        "/opt/pw-browsers/chromium-*/chrome-linux*/chrome",
        "/opt/pw-browsers/chromium/chrome-linux*/chrome",
    ):
        found = sorted(glob.glob(pattern))
        if found:
            return found[-1]
    return None


if __name__ == "__main__":
    sys.exit(main())
