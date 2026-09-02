/*
 * Root "script" property for the "Secure code development" Xerte project.
 *
 * THIS FILE IS THE SOURCE OF TRUTH. It is compiled (comments stripped,
 * whitespace collapsed) into the learningObject/@script attribute of
 * source/data.xml and source/preview.xml by tools/sync_root_script.py.
 * Never hand-edit that attribute: edit this file and re-run
 *
 *     python3 tools/sync_root_script.py
 *
 * Xerte injects the attribute once, after the interface has been set up and
 * BEFORE XTInitialise() runs (xenith.js, x_continueSetUp2). Because the
 * tracking options (nrpages, toComplete, tracking-mode, objective_passed) are
 * set earlier still, in x_projectDataLoaded, this script can see both the live
 * page structure and the LMS suspend data before the engine parses it.
 *
 * It works around four behaviours of modules/xerte/scorm1.2/
 * xttracking_scorm1.2.js that we cannot patch, because the release workflow
 * rebuilds the engine from upstream XOT on every build:
 *
 *  1. getVars() serialises the resume point as this.find(this.currentpageid)
 *     and pushes the result into the interactions array without checking it.
 *     currentpageid is blank between leaving one page and entering the next
 *     (exitInteraction clears it) and on a revisit to the table of contents,
 *     so find() returns null and the saved record contains
 *     "interactions":[null]. On the next launch, setVars() reads
 *     jsonSit.page_nr off that null and throws
 *     "Cannot read properties of null (reading 'page_nr')" from inside
 *     initTracking / XTInitialise, which stops the course from rendering at
 *     all. We repair records on the way out (never write an unresumable
 *     record) and on the way in (heal records written by an older build), and
 *     we make initTracking non-fatal as a backstop. A resume point naming a
 *     page this build does not have blanks the course the same way, one step
 *     later: XTStartPage hands page_nr to the player, which indexes
 *     x_pageInfo without a bounds check, so those entries are dropped too.
 *
 *  2. completedPages is restored verbatim from the saved record, so a learner
 *     who resumes into a build with a different number of tracked pages keeps
 *     an array of the wrong length. getSuccessStatus() walks that array, so a
 *     short one can report completion early and a long one can block it
 *     forever. We resize it to state.toCompletePages.length, and likewise
 *     prefer the live nrpages / tracking mode / pass mark over saved copies.
 *
 *  3. getVars() persists only the current page's interaction ("SCORM 1.2 only
 *     allows for 4kb of suspend data"), so every quiz page score is lost when
 *     a learner resumes. getdRawScore() then averages only the quiz pages
 *     visited in the current session, which is why cmi.core.score.raw can sit
 *     at 0 for a learner with plenty of logged interactions. We persist a
 *     compact per-quiz-page score list (xtPages) and restore it as page
 *     interactions, with a size guard so the record stays inside the 4096
 *     character suspend_data limit.
 *
 *  4. state.finished is never set by the engine, so the guard against saving
 *     after LMSFinish does not work: onbeforeunload runs XTTerminate, and the
 *     later pagehide would autosave again, which a conformant LMS rejects and
 *     which loses a page-history entry finishTracking has already dropped. We
 *     track termination ourselves.
 *
 * It also keeps the original job of this script: committing progress to the
 * LMS as the learner goes, because the engine only calls doLMSCommit() from
 * finishTracking(), i.e. on Save Session / unload.
 *
 * CONSTRAINT: the compiled one-liner is stored raw in an XML attribute, so it
 * must not contain < > & or " characters (tools/sync_root_script.py enforces
 * this). Use === / !== / indexOf() instead of ordering comparisons, nested ifs
 * instead of &&, and single-quoted strings. Line comments are stripped, but
 * attribute-value normalisation turns newlines into spaces, so never rely on
 * // comments surviving.
 */
(function () {
    if (typeof window === 'undefined') { return; }
    if (window.__xtProgress) { return; }
    window.__xtProgress = true;

    /* SCORM 1.2 guarantees 4096 characters of cmi.suspend_data; leave headroom. */
    var MAX_SUSPEND = 4000;
    var HEARTBEAT_MS = 30000;
    var HISTORY_KEEP = 12;

    function isArray(v) {
        return Object.prototype.toString.call(v) === '[object Array]';
    }

    function overBudget(str) {
        /* str.length greater than MAX_SUSPEND, without using an ordering operator */
        return str.substr(MAX_SUSPEND).length !== 0;
    }

    function round2(v) {
        var n = Number(v);
        if (isNaN(n)) { return 0; }
        return Math.round(n * 100) / 100;
    }

    function pagesKnown() {
        if (typeof x_pageInfo === 'undefined') { return false; }
        return isArray(x_pageInfo);
    }

    /* Is this page index part of the package we are running right now? */
    function livePage(idx) {
        if (typeof idx !== 'number') { return false; }
        if (typeof x_pageInfo === 'undefined') { return false; }
        if (!isArray(x_pageInfo)) { return false; }
        return x_pageInfo[idx] !== undefined;
    }

    function livePages(list) {
        if (!isArray(list)) { return undefined; }
        return list.filter(function (v) { return livePage(v); });
    }

    /* An interaction we are willing to write to, or read from, suspend data. */
    function usable(it) {
        if (!it) { return false; }
        if (typeof it.page_nr !== 'number') { return false; }
        if (typeof it.id !== 'string') { return false; }
        return it.id !== '';
    }

    function isPageEntry(it) {
        return it.ia_nr === -1;
    }

    function scored(it) {
        if (!isPageEntry(it)) { return false; }
        return Number(it.weighting) !== 0;
    }

    /* A page-level interaction shaped the way ScormInteractionTracking.setVars
       expects, used to put a remembered quiz page score back into state. */
    function pageEntry(pageNr, score, weighting, nrinteractions, id) {
        var now = (new Date()).toISOString();
        return {
            page_nr: pageNr,
            page_ref: pageNr + 1,
            ia_nr: -1,
            ia_ref: 0,
            ia_type: 'numeric',
            ia_name: '',
            state: 'exited',
            start: now,
            end: now,
            count: 1,
            duration: 0,
            nrinteractions: nrinteractions,
            weighting: weighting,
            score: score,
            result: 'unknown',
            complete: false,
            correctOptions: [],
            correctAnswers: [],
            correctfeedback: '',
            learnerOptions: [],
            learnerAnswers: [],
            answerfeedback: '',
            id: id,
            idx: -1
        };
    }

    /* Drop nulls and duplicates; one page-level entry per page at most. */
    function keepUsable(list) {
        var kept = [];
        var pages = [];
        if (isArray(list)) {
            list.forEach(function (it) {
                if (!usable(it)) { return; }
                if (pagesKnown()) {
                    if (!livePage(it.page_nr)) { return; }
                }
                if (isPageEntry(it)) {
                    if (pages.indexOf(it.page_nr) !== -1) { return; }
                    pages.push(it.page_nr);
                }
                kept.push(it);
            });
        }
        return kept;
    }

    function pageNrsOf(list) {
        var pages = [];
        list.forEach(function (it) {
            if (isPageEntry(it)) { pages.push(it.page_nr); }
        });
        return pages;
    }

    function idsOf(list) {
        return list.map(function (it) { return it.id; });
    }

    /* completedPages must line up with the pages this build asks for. */
    function normaliseCompleted(saved) {
        var out = [];
        if (isArray(saved)) {
            out = saved.map(function (v) { return v === true; });
        }
        var need = 0;
        if (typeof state !== 'undefined') {
            if (state) {
                if (isArray(state.toCompletePages)) { need = state.toCompletePages.length; }
            }
        }
        if (need === 0) { return out; }
        out = out.slice(0, need);
        while (out.length !== need) { out.push(false); }
        return out;
    }

    /* Values the running package knows better than the saved record does. */
    function adoptLive(obj) {
        if (typeof state === 'undefined') { return; }
        if (!state) { return; }
        if (typeof state.nrpages === 'number') {
            if (state.nrpages !== 0) { obj.nrpages = state.nrpages; }
        }
        if (typeof state.trackingmode === 'string') { obj.trackingmode = state.trackingmode; }
        if (typeof state.scoremode === 'string') { obj.scoremode = state.scoremode; }
        if (typeof state.page_timeout === 'number') { obj.page_timeout = state.page_timeout; }
        if (typeof state.lo_passed === 'number') {
            if (state.lo_passed !== -1) { obj.lo_passed = state.lo_passed; }
        }
    }

    /* ---- reading: heal whatever the LMS gives us ---- */

    function repairIncoming(str) {
        var obj = JSON.parse(str);
        if (!obj) { return str; }
        var kept = keepUsable(obj.interactions);
        var pages = pageNrsOf(kept);
        if (isArray(obj.xtPages)) {
            obj.xtPages.forEach(function (row) {
                if (!isArray(row)) { return; }
                if (typeof row[0] !== 'number') { return; }
                if (typeof row[4] !== 'string') { return; }
                if (pages.indexOf(row[0]) !== -1) { return; }
                if (!livePage(row[0])) { return; }
                pages.push(row[0]);
                kept.push(pageEntry(row[0], round2(row[1]), Number(row[2]), Number(row[3]), row[4]));
            });
        }
        delete obj.xtPages;
        obj.interactions = kept;
        if (kept.filter(scored).length !== 0) { obj.lo_type = 'interactive'; }
        if (typeof obj.currentid !== 'string') { obj.currentid = ''; }
        if (typeof obj.currentpageid !== 'string') { obj.currentpageid = ''; }
        if (idsOf(kept).indexOf(obj.currentpageid) === -1) { obj.currentpageid = ''; }
        obj.completedPages = normaliseCompleted(obj.completedPages);
        obj.pageHistory = livePages(obj.pageHistory);
        obj.pagesViewed = livePages(obj.pagesViewed);
        adoptLive(obj);
        return JSON.stringify(obj);
    }

    /* ---- writing: never save a record we could not resume from ---- */

    function pageEntryFor(st, pageNr) {
        if (typeof st.findPage !== 'function') { return null; }
        if (typeof pageNr !== 'number') { return null; }
        return st.findPage(pageNr);
    }

    /* The engine blanks currentpageid on page exit, so fall back to the page
       being shown, then to the most recent page in the history. */
    function resumeEntry(st) {
        var sit = null;
        if (typeof x_currentPage !== 'undefined') { sit = pageEntryFor(st, x_currentPage); }
        if (sit) { return sit; }
        if (typeof x_pageHistory !== 'undefined') {
            if (isArray(x_pageHistory)) {
                x_pageHistory.forEach(function (p) {
                    var candidate = pageEntryFor(st, p);
                    if (candidate) { sit = candidate; }
                });
            }
        }
        return sit;
    }

    /* a copy, so live engine state is never touched */
    function asExited(entry) {
        var copy = JSON.parse(JSON.stringify(entry));
        copy.state = 'exited';
        return copy;
    }

    function quizScoreRows(st) {
        var rows = [];
        if (!isArray(st.interactions)) { return rows; }
        st.interactions.forEach(function (it) {
            if (!usable(it)) { return; }
            if (!scored(it)) { return; }
            rows.push([it.page_nr, round2(it.score), Number(it.weighting), Number(it.nrinteractions), it.id]);
        });
        return rows;
    }

    /* Shed the least valuable data until the record fits suspend_data. */
    function fitBudget(obj, rows) {
        if (rows.length !== 0) { obj.xtPages = rows; }
        var str = JSON.stringify(obj);
        if (!overBudget(str)) { return str; }
        if (isArray(obj.pageHistory)) {
            obj.pageHistory = obj.pageHistory.slice(-HISTORY_KEEP);
            str = JSON.stringify(obj);
            if (!overBudget(str)) { return str; }
        }
        delete obj.pageHistory;
        str = JSON.stringify(obj);
        if (!overBudget(str)) { return str; }
        delete obj.pagesViewed;
        str = JSON.stringify(obj);
        if (!overBudget(str)) { return str; }
        delete obj.xtPages;
        return JSON.stringify(obj);
    }

    function repairOutgoing(str, st) {
        var obj = JSON.parse(str);
        if (!obj) { return str; }
        var kept = keepUsable(obj.interactions);
        var ids = idsOf(kept);
        if (typeof obj.currentpageid !== 'string') { obj.currentpageid = ''; }
        if (ids.indexOf(obj.currentpageid) === -1) {
            obj.currentpageid = '';
            var sit = resumeEntry(st);
            if (sit) {
                obj.currentpageid = sit.id;
                if (pageNrsOf(kept).indexOf(sit.page_nr) === -1) { kept.push(sit); }
            }
        }
        obj.interactions = kept.map(function (it) {
            if (it.id === obj.currentpageid) { return asExited(it); }
            return it;
        });
        obj.completedPages = normaliseCompleted(obj.completedPages);
        obj.pageHistory = livePages(obj.pageHistory);
        obj.pagesViewed = livePages(obj.pagesViewed);
        return fitBudget(obj, quizScoreRows(st));
    }

    /* ---- autosave ---- */

    var terminated = false;

    function persist() {
        try {
            if (terminated) { return; }
            if (typeof state === 'undefined') { return; }
            if (!state) { return; }
            if (!state.initialised) { return; }
            if (state.finished) { return; }
            if (state.trackingmode === 'none') { return; }
            if (state.scormmode !== 'normal') { return; }
            if (typeof doLMSCommit !== 'function') { return; }
            if (typeof state.getSuccessStatus !== 'function') { return; }
            var status = state.getSuccessStatus();
            setValue('cmi.core.lesson_status', status);
            if (typeof x_pageHistory !== 'undefined') {
                if (isArray(x_pageHistory)) {
                    /* the page being shown is restored via currentpageid, so
                       drop it from the history copy as finishTracking does */
                    state.pageHistory = x_pageHistory.slice(0, -1);
                }
            }
            if (typeof x_pagesViewed === 'function') { state.pagesViewed = x_pagesViewed(); }
            var susp = state.getVars();
            if (status === 'incomplete') { setValue('cmi.core.exit', 'suspend'); }
            else { setValue('cmi.core.exit', ''); }
            setValue('cmi.suspend_data', susp);
            var supported = getValue('cmi.core.score._children');
            setValue('cmi.core.score.raw', state.getRawScore());
            if (supported.indexOf('min') !== -1) { setValue('cmi.core.score.min', state.getMinScore()); }
            if (supported.indexOf('max') !== -1) { setValue('cmi.core.score.max', state.getMaxScore()); }
            doLMSCommit();
        } catch (e) { }
    }

    window.xPersistProgress = persist;

    /* ---- installation ---- */

    function resetResume(st) {
        st.interactions = [];
        st.currentid = '';
        st.currentpageid = '';
        st.completedPages = normaliseCompleted(st.completedPages);
    }

    function wrapState() {
        if (typeof state === 'undefined') { return; }
        if (!state) { return; }
        if (state.__xtWrapped) { return; }
        if (typeof state.setVars !== 'function') { return; }
        if (typeof state.getVars !== 'function') { return; }
        state.__xtWrapped = true;
        var origSetVars = state.setVars;
        state.setVars = function (str) {
            var safe = str;
            try { safe = repairIncoming(str); } catch (e) { safe = str; }
            try { return origSetVars.call(this, safe); }
            catch (e) { resetResume(this); }
        };
        var origGetVars = state.getVars;
        state.getVars = function () {
            var raw = origGetVars.call(this);
            try { return repairOutgoing(raw, this); } catch (e) { return raw; }
        };
        if (typeof state.initTracking === 'function') {
            var origInit = state.initTracking;
            state.initTracking = function () {
                try { return origInit.call(this); } catch (e) { resetResume(this); }
            };
        }
    }

    /* Must be wrapped synchronously: xenith assigns window.onbeforeunload =
       XTTerminate just after injecting this script, and would otherwise capture
       the unwrapped function. */
    function wrapTerminate() {
        if (typeof window.XTTerminate !== 'function') { return; }
        var orig = window.XTTerminate;
        window.XTTerminate = function () {
            terminated = true;
            return orig.apply(this, arguments);
        };
    }

    function wrapGlobal(name) {
        if (typeof window[name] !== 'function') { return; }
        var orig = window[name];
        window[name] = function () {
            var result = orig.apply(this, arguments);
            persist();
            return result;
        };
    }

    var installTries = 0;

    function install() {
        var ready = false;
        if (typeof state !== 'undefined') {
            if (state) {
                if (state.initialised) { ready = true; }
            }
        }
        if (!ready) {
            /* give up rather than poll forever where there is no tracking */
            installTries = installTries + 1;
            if (installTries !== 150) { setTimeout(install, 200); }
            return;
        }
        /* flush on every page leave and every answered question */
        wrapGlobal('XTExitPage');
        wrapGlobal('XTExitInteraction');
        /* safety net for idle learners and viewers that unload silently */
        setInterval(persist, HEARTBEAT_MS);
    }

    /* must happen before XTInitialise calls initTracking */
    wrapState();
    wrapTerminate();
    if (typeof window.addEventListener === 'function') {
        window.addEventListener('pagehide', persist);
    }
    install();
})();
