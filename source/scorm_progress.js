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
 * Finally it gives the learner an honest view of that tracking state, which
 * the engine does not: the table-of-contents tick only means a page has been
 * opened (x_pageLoaded sets x_pageInfo[i].viewed), and SCORM 1.2 gives the
 * LMS nothing but the incomplete/passed/failed flag, so Moodle shows 0% until
 * the very end. So this script
 *
 *  5. marks a quiz page as "submitted" (page interaction .complete, a field
 *     the engine never reads) when the quiz reports its score, persists that
 *     flag in xtPages, swaps the menu tick of an opened-but-unsubmitted quiz
 *     for a half-filled circle, lights a quiz milestone on the header
 *     progress bar only once that quiz is submitted (the engine lights a
 *     milestone as soon as its page is viewed), and fills every element
 *     with the class
 *     xtStatusPanel (one is in the menu text, one on the Course complete
 *     page) with the required-page count, the pages still to do, each quiz
 *     result, the weighted score and the exact status the LMS holds.
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
    function pageEntry(pageNr, score, weighting, nrinteractions, id, complete) {
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
            complete: complete === true,
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

    /* Was this remembered quiz page submitted? Records written before the
       flag existed have no row[5]; a non-zero score can only come from the
       results screen, so treat it as submitted. */
    function submittedRow(row) {
        if (row[5] === 1) { return true; }
        return round2(row[1]) !== 0;
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
                kept.push(pageEntry(row[0], round2(row[1]), Number(row[2]), Number(row[3]), row[4], submittedRow(row)));
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
            rows.push([it.page_nr, round2(it.score), Number(it.weighting), Number(it.nrinteractions), it.id, it.complete === true ? 1 : 0]);
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

    /* ---- learner-facing progress: quiz ticks and the status panel ---- */

    var PENDING_LABEL = 'Opened, quiz not yet submitted';
    var VIEWED_LABEL = 'Viewed';
    var LIST_CAP = 6;

    function trackingActive() {
        if (typeof state === 'undefined') { return false; }
        if (!state) { return false; }
        if (!state.initialised) { return false; }
        if (typeof state.scormmode === 'string') {
            if (state.scormmode !== 'normal') { return false; }
        }
        if (typeof state.getSuccessStatus !== 'function') { return false; }
        if (typeof state.findPage !== 'function') { return false; }
        if (!isArray(state.toCompletePages)) { return false; }
        return state.toCompletePages.length !== 0;
    }

    function pageType(idx) {
        if (!livePage(idx)) { return ''; }
        return String(x_pageInfo[idx].type);
    }

    function pageViewed(idx) {
        if (!livePage(idx)) { return false; }
        return x_pageInfo[idx].viewed === true;
    }

    /* page names are stored HTML-escaped; render them as text */
    function pageName(idx) {
        var raw = '';
        if (typeof x_pages !== 'undefined') {
            if (x_pages) {
                if (x_pages[idx]) {
                    if (typeof x_pages[idx].getAttribute === 'function') {
                        raw = x_pages[idx].getAttribute('name') || '';
                    }
                }
            }
        }
        var holder = document.createElement('div');
        holder.innerHTML = raw;
        return holder.textContent || raw;
    }

    function quizPages() {
        var out = [];
        if (!pagesKnown()) { return out; }
        x_pageInfo.forEach(function (info, idx) {
            if (pageType(idx) === 'quiz') { out.push(idx); }
        });
        return out;
    }

    /* A quiz counts as submitted once XTSetPageScore has run for it (the
       results screen), in this session or a remembered one. */
    function quizSubmitted(idx) {
        if (!trackingActive()) { return false; }
        var sit = state.findPage(idx);
        if (!sit) { return false; }
        return sit.complete === true;
    }

    function quizPending(idx) {
        if (pageType(idx) !== 'quiz') { return false; }
        if (!pageViewed(idx)) { return false; }
        return !quizSubmitted(idx);
    }

    function quizScore(idx) {
        var sit = state.findPage(idx);
        if (!sit) { return 0; }
        return Math.round(Number(sit.score));
    }

    function markSubmitted(pageNr) {
        if (!trackingActive()) { return; }
        var sit = state.findPage(pageNr);
        if (sit) { sit.complete = true; }
    }

    function menuOffset() {
        if (typeof XENITH === 'undefined') { return 0; }
        if (!XENITH.PAGEMENU) { return 0; }
        return XENITH.PAGEMENU.menuPage === true ? 1 : 0;
    }

    function setPending(icon, pending) {
        if (pending) {
            if (icon.classList.contains('xtPending')) { return; }
            icon.classList.add('xtPending');
            icon.classList.add('fa-adjust');
            icon.classList.remove('fa-x-tick-circle');
            icon.setAttribute('aria-label', PENDING_LABEL);
            icon.setAttribute('title', PENDING_LABEL);
            icon.setAttribute('aria-hidden', 'false');
            return;
        }
        if (!icon.classList.contains('xtPending')) { return; }
        icon.classList.remove('xtPending');
        icon.classList.remove('fa-adjust');
        icon.classList.add('fa-x-tick-circle');
        icon.setAttribute('aria-label', VIEWED_LABEL);
        icon.removeAttribute('title');
    }

    /* Runs after XENITH.PAGEMENU.tickViewed: every table of contents in the
       DOM (menu page, sidebar, dialog) gets its quiz ticks corrected. */
    function fixTicks() {
        if (typeof jQuery !== 'function') { return; }
        if (typeof x_normalPages === 'undefined') { return; }
        if (!isArray(x_normalPages)) { return; }
        var offset = menuOffset();
        jQuery('.menuItem').each(function () {
            var pos = jQuery(this).data('pageIndex');
            if (typeof pos !== 'number') { return; }
            var idx = x_normalPages[pos + offset];
            if (typeof idx !== 'number') { return; }
            var icon = this.querySelector('i.viewTick');
            if (!icon) { return; }
            setPending(icon, quizPending(idx));
        });
    }

    /* ---- header progress bar: quiz milestones light on submission ---- */

    var MILESTONE_PENDING = ' (Quiz not yet submitted)';
    var MILESTONE_DONE = ': Complete';

    /* the pages the engine gave a progress marker, in marker order */
    function milestonePages() {
        var out = [];
        if (!pagesKnown()) { return out; }
        if (typeof x_pages === 'undefined') { return out; }
        if (!x_pages) { return out; }
        x_pageInfo.forEach(function (info, idx) {
            if (info.type === 'menu') { return; }
            if (info.standalone === true) { return; }
            if (!x_pages[idx]) { return; }
            if (typeof x_pages[idx].getAttribute !== 'function') { return; }
            if (x_pages[idx].getAttribute('milestone') === 'true') { out.push(idx); }
        });
        return out;
    }

    function setMarker(marker, done, label) {
        var item = jQuery(marker);
        if (done) { item.addClass('complete'); } else { item.removeClass('complete'); }
        if (typeof item.button === 'function') {
            try { item.button({ label: label }); } catch (e) { }
        }
        item.attr('title', label);
    }

    /* Runs after XENITH.PROGRESSBAR.update, which marks a milestone complete
       as soon as its page has been viewed. A quiz milestone should mean the
       quiz was submitted, like the menu tick. */
    function fixMilestones() {
        if (typeof jQuery !== 'function') { return; }
        var markers = jQuery('#x_headerProgress .progressMarker');
        if (markers.length === 0) { return; }
        milestonePages().forEach(function (idx, i) {
            if (pageType(idx) !== 'quiz') { return; }
            var marker = markers.get(i);
            if (!marker) { return; }
            var title = jQuery(marker).data('title');
            if (typeof title !== 'string') { return; }
            if (quizSubmitted(idx)) { setMarker(marker, true, title + MILESTONE_DONE); }
            else { setMarker(marker, false, title + MILESTONE_PENDING); }
        });
    }

    function el(tag, text) {
        var node = document.createElement(tag);
        if (text !== undefined) { node.textContent = text; }
        return node;
    }

    function joinNames(list) {
        var shown = list.slice(0, LIST_CAP);
        var rest = list.slice(LIST_CAP).length;
        var text = shown.join('; ');
        if (rest !== 0) { text = text + '; and ' + rest + ' more'; }
        return text;
    }

    function requiredSummary() {
        var done = 0;
        var missing = [];
        state.toCompletePages.forEach(function (pageNr, j) {
            if (state.completedPages[j] === true) { done = done + 1; }
            else { missing.push(pageName(pageNr)); }
        });
        return { done: done, total: state.toCompletePages.length, missing: missing };
    }

    function statusText(status, score, passMark, unsubmitted) {
        if (status === 'passed') {
            return 'Passed. The LMS has been told you passed this course with ' + score + '%.';
        }
        if (status === 'failed') {
            return 'Not passed. Every required page is done, but your score of ' + score + '% is below the ' + passMark + '% pass mark. Retake the quizzes; your last attempt is the one that counts.';
        }
        if (status === 'completed') {
            return 'Completed without a score. Every required page is done but no quiz has been submitted, so the LMS has no result for you. Submit the quizzes to be graded.';
        }
        var text = 'Incomplete. The LMS shows this course as incomplete (0%) until every required page has been visited';
        if (unsubmitted !== 0) { text = text + ' and every quiz submitted'; }
        return text + '. Use the list above to find what is left.';
    }

    function buildPanel(panel) {
        while (panel.firstChild) { panel.removeChild(panel.firstChild); }
        panel.appendChild(el('h3', 'Your progress'));
        if (!trackingActive()) {
            panel.appendChild(el('p', 'Progress tracking is not active in this view. Launch the course from your LMS to have your progress recorded.'));
            return;
        }
        var req = requiredSummary();
        var pages = el('p');
        pages.appendChild(el('strong', 'Required pages completed: ' + req.done + ' of ' + req.total + '.'));
        if (req.missing.length === 0) {
            pages.appendChild(document.createTextNode(' Every required page has been visited.'));
        } else {
            pages.appendChild(document.createTextNode(' Still to visit: ' + joinNames(req.missing) + '. A page counts once you have opened it and moved on.'));
        }
        panel.appendChild(pages);
        var quizzes = quizPages();
        var unsubmitted = 0;
        if (quizzes.length !== 0) {
            var list = el('ul');
            quizzes.forEach(function (idx) {
                var item = el('li');
                var name = pageName(idx);
                if (quizSubmitted(idx)) {
                    item.textContent = name + ': ' + quizScore(idx) + '%';
                } else {
                    unsubmitted = unsubmitted + 1;
                    item.textContent = name + ': not yet submitted';
                    item.className = 'xtQuizPending';
                }
                list.appendChild(item);
            });
            panel.appendChild(list);
        }
        var passMark = Math.round(Number(state.lo_passed));
        var score = Math.round(Number(state.getRawScore()));
        panel.appendChild(el('p', 'Weighted score so far: ' + score + '%. Pass mark: ' + passMark + '%. Theme quizzes count for 25% and the final quiz for 75%.'));
        var status = el('p');
        status.className = 'xtLmsStatus';
        status.setAttribute('data-status', state.getSuccessStatus());
        status.appendChild(el('strong', 'LMS status: '));
        status.appendChild(document.createTextNode(statusText(state.getSuccessStatus(), score, passMark, unsubmitted)));
        panel.appendChild(status);
    }

    function fillPanels() {
        var panels = document.querySelectorAll('.xtStatusPanel');
        var i = 0;
        for (i = 0; i !== panels.length; i = i + 1) {
            panels[i].style.border = '1px solid currentColor';
            panels[i].style.borderRadius = '6px';
            panels[i].style.padding = '0.5em 1em';
            panels[i].style.margin = '0 0 1em 0';
            buildPanel(panels[i]);
        }
    }

    function refreshUi() {
        try { fixTicks(); } catch (e) { }
        try { fixMilestones(); } catch (e) { }
        try { fillPanels(); } catch (e) { }
    }

    window.xtRefreshProgressUi = refreshUi;

    function wrapTickViewed() {
        if (typeof XENITH === 'undefined') { return; }
        if (!XENITH.PAGEMENU) { return; }
        if (typeof XENITH.PAGEMENU.tickViewed !== 'function') { return; }
        var orig = XENITH.PAGEMENU.tickViewed;
        XENITH.PAGEMENU.tickViewed = function () {
            var result = orig.apply(this, arguments);
            refreshUi();
            return result;
        };
    }

    function wrapProgressBar() {
        if (typeof XENITH === 'undefined') { return; }
        if (!XENITH.PROGRESSBAR) { return; }
        if (typeof XENITH.PROGRESSBAR.update !== 'function') { return; }
        var orig = XENITH.PROGRESSBAR.update;
        XENITH.PROGRESSBAR.update = function () {
            var result = orig.apply(this, arguments);
            try { fixMilestones(); } catch (e) { }
            return result;
        };
    }

    /* every page model calls x_pageLoaded once its content is in the DOM */
    function wrapPageLoaded() {
        if (typeof window.x_pageLoaded !== 'function') { return; }
        var orig = window.x_pageLoaded;
        window.x_pageLoaded = function () {
            var result = orig.apply(this, arguments);
            refreshUi();
            return result;
        };
    }

    /* the quiz results screen is the only caller of XTSetPageScore */
    function wrapPageScore() {
        if (typeof window.XTSetPageScore !== 'function') { return; }
        var orig = window.XTSetPageScore;
        window.XTSetPageScore = function (pageNr, score) {
            var result = orig.apply(this, arguments);
            try { markSubmitted(pageNr); } catch (e) { }
            persist();
            refreshUi();
            return result;
        };
    }

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
            refreshUi();
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
    wrapTickViewed();
    wrapProgressBar();
    wrapPageLoaded();
    wrapPageScore();
    if (typeof window.addEventListener === 'function') {
        window.addEventListener('pagehide', persist);
    }
    install();
})();
