#!/usr/bin/env python3
"""Render a Xerte Nottingham data.xml into a single readable HTML preview.

This is for PR review: it lets reviewers read the course content (pages and
quizzes, with correct answers marked) without running Xerte. It is NOT the
playable/SCORM output — the real deliverable is built by the release workflow
from the running XOT instance.

Usage: python3 tools/render_preview.py source/data.xml preview/index.html
"""
import sys, os, re, html, xml.etree.ElementTree as ET

def unesc(s):
    """Nottingham names are stored double-encoded (&amp;amp;); unescape twice."""
    if s is None: return ""
    return html.unescape(html.unescape(s))

def clean_name(s):
    return unesc(s).strip()

def strip_cdata(html_str):
    """Return inner HTML of a CDATA/escaped body, lightly cleaned."""
    if html_str is None: return ""
    # data.xml bodies are raw HTML inside CDATA; ET gives them as text.
    return html_str.strip()

def render_options(opts):
    out = ['<ul class="opts">']
    for o in opts:
        correct = o.get("correct") == "true"
        name = clean_name(o.get("name")) or "•"
        text = unesc(o.get("text", "")).replace("<p>", "").replace("</p>", "").strip()
        cls = "opt correct" if correct else "opt"
        mark = " <span class='mark'>✓ correct</span>" if correct else ""
        out.append(f'<li class="{cls}"><span class="lbl">{html.escape(name)}</span>. '
                   f'{html.escape(text)}{mark}</li>')
    out.append('</ul>')
    return "\n".join(out)

def render_question(q):
    prompt = unesc(q.get("prompt", "")).replace("<p>", "").replace("</p>", "").strip()
    qtype = q.get("type", "")
    opts = [c for c in q if c.tag == "option"]
    out = [f'<div class="question">',
           f'<div class="q-prompt"><strong>Q:</strong> {html.escape(prompt)}</div>',
           f'<div class="q-meta">{html.escape(qtype)} ({len(opts)} options)</div>',
           render_options(opts),
           f'</div>']
    return "\n".join(out)

def render_page(node, idx):
    tag = node.tag
    name = clean_name(node.get("name"))
    body = node.text or ""
    parts = [f'<section class="page" id="page-{idx}">']
    parts.append(f'<h2><span class="pnum">#{idx}</span> {html.escape(name)} '
                 f'<span class="ptype">{html.escape(tag)}</span></h2>')
    if tag in ("text", "bullets"):
        parts.append(f'<div class="body">{body}</div>')
    elif tag == "mcq":
        # standalone MCQ: prompt attr + options
        prompt = unesc(node.get("prompt", "")).replace("<p>", "").replace("</p>", "").strip()
        opts = [c for c in node if c.tag == "option"]
        parts.append(f'<div class="question"><div class="q-prompt"><strong>Q:</strong> {html.escape(prompt)}</div>')
        parts.append(render_options(opts))
        parts.append('</div>')
    elif tag == "quiz":
        qs = [c for c in node if c.tag == "question"]
        parts.append(f'<div class="quiz"><div class="quiz-meta">{len(qs)} questions</div>')
        for q in qs:
            parts.append(render_question(q))
        parts.append('</div>')
    parts.append('</section>')
    return "\n".join(parts)

def main():
    if len(sys.argv) < 3:
        print("usage: render_preview.py <data.xml> <out.html>", file=sys.stderr)
        sys.exit(1)
    src, out = sys.argv[1], sys.argv[2]
    tree = ET.parse(src)
    root = tree.getroot()
    title = clean_name(root.get("name")) or "Xerte course"
    pages = [c for c in root if c.tag in ("text", "bullets", "mcq", "quiz")]

    toc = []
    for i, p in enumerate(pages, 1):
        nm = clean_name(p.get("name"))
        toc.append(f'<li><a href="#page-{i}">#{i} {html.escape(nm)}</a></li>')

    body = "\n".join(render_page(p, i) for i, p in enumerate(pages, 1))

    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — preview</title>
<style>
:root {{ --fg:#1a1a1a; --muted:#666; --bg:#fff; --accent:#0a6; }}
* {{ box-sizing: border-box; }}
body {{ font: 16px/1.6 -apple-system,Segoe UI,Roboto,sans-serif; color:var(--fg); margin:0; }}
header {{ position:sticky; top:0; background:var(--bg); border-bottom:1px solid #ddd; padding:12px 20px; z-index:1; }}
header h1 {{ margin:0; font-size:1.2rem; }}
.toc {{ columns:2; font-size:.9rem; padding-left:18px; }}
main {{ max-width:900px; margin:0 auto; padding:20px; }}
.page {{ border:1px solid #e5e5e5; border-radius:8px; padding:18px 22px; margin:18px 0; background:#fff; }}
.page h2 {{ margin-top:0; font-size:1.15rem; }}
.pnum {{ color:var(--muted); font-weight:normal; }}
.ptype {{ font-size:.7rem; background:#eee; border-radius:4px; padding:1px 6px; vertical-align:middle; }}
.body {{ overflow-x:auto; }}
.body h2,.body h3,.body h4 {{ margin-top:1.2em; }}
.body ul,.body ol {{ padding-left:20px; }}
.quiz,.question {{ margin-top:10px; padding:10px 14px; background:#f8f9fa; border-radius:6px; }}
.q-prompt {{ margin-bottom:6px; }}
.q-meta,.quiz-meta {{ color:var(--muted); font-size:.8rem; margin-bottom:6px; }}
.opts {{ list-style:none; padding-left:0; }}
.opt {{ padding:3px 0; }}
.opt.correct {{ font-weight:bold; }}
.opt .lbl {{ color:var(--muted); }}
.opt .mark {{ color:var(--accent); font-size:.8rem; }}
footer {{ color:var(--muted); font-size:.8rem; text-align:center; padding:20px; }}
</style></head><body>
<header><h1>{html.escape(title)}</h1>
<p class="toc-meta">Auto-generated preview for review · {len(pages)} pages · correct answers are marked ✓</p>
</header>
<main>
<nav class="toc"><ul>{''.join(toc)}</ul></nav>
{body}
</main>
<footer>Generated from <code>source/data.xml</code> by <code>tools/render_preview.py</code>.
This is a review preview, not the playable/SCORM output.</footer>
</body></html>"""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print(f"wrote {out}: {len(pages)} pages")

if __name__ == "__main__":
    main()
