#!/usr/bin/env python3
"""Inline every asset so the wiki works in a browser that blocks externals.

This user's browser blocks external CSS and JS, and the wiki is served as
static files from the Pi. mkdocs emits a page full of <link> and <script src>
that would all fail, so every one of them is pulled in and written into the
page itself. Google Fonts are cut rather than inlined - they are remote by
definition and the fallback stack is fine.

Runs inside the umb-wiki container, where mkdocs' output lives. Kept in the
project (bind-mounted to /app) rather than in /tmp, because the deploy
pipeline used to depend on scratch files that got cleared and broke it.
"""
import os
import re
import shutil
import sys

SRC = "/app/site"
DST = "/app/site-inline"

if not os.path.isdir(SRC):
    raise SystemExit("no mkdocs output at %s - run mkdocs build first" % SRC)

if os.path.isdir(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)

LINK = re.compile(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', re.I)
SCRIPT = re.compile(r'<script[^>]+src=["\']([^"\']+)["\'][^>]*>\s*</script>', re.I)
HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)

stats = {"pages": 0, "css": 0, "js": 0, "fonts_cut": 0}


def resolve(page_path, ref):
    """Turn a page-relative asset reference into a real path inside DST."""
    ref = ref.split("?")[0].split("#")[0]
    if ref.startswith(("http://", "https://", "//", "data:")):
        return None
    base = os.path.dirname(page_path)
    p = os.path.normpath(os.path.join(base, ref))
    return p if os.path.isfile(p) else None


def read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError as e:
        print("  ! could not read %s: %s" % (p, e))
        return None


for root, _, files in os.walk(DST):
    for f in files:
        if not f.endswith(".html"):
            continue
        page = os.path.join(root, f)
        html = read(page)
        if html is None:
            continue
        stats["pages"] += 1

        def css_sub(m):
            tag = m.group(0)
            href = HREF.search(tag)
            if not href:
                return ""
            ref = href.group(1)
            if "fonts.googleapis.com" in ref or "fonts.gstatic.com" in ref:
                stats["fonts_cut"] += 1
                return ""
            p = resolve(page, ref)
            if not p:
                stats["fonts_cut"] += 1
                return ""            # remote or missing: drop it
            body = read(p)
            if body is None:
                return ""
            stats["css"] += 1
            return "<style>%s</style>" % body

        html = LINK.sub(css_sub, html)

        def js_sub(m):
            ref = m.group(1)
            p = resolve(page, ref)
            if not p:
                return ""            # remote: drop it
            body = read(p)
            if body is None:
                return ""
            stats["js"] += 1
            return "<script>%s</script>" % body

        html = SCRIPT.sub(js_sub, html)

        with open(page, "w", encoding="utf-8") as fh:
            fh.write(html)

# ── prove it ─────────────────────────────────────────────────────────
left = 0
for root, _, files in os.walk(DST):
    for f in files:
        if f.endswith(".html"):
            h = read(os.path.join(root, f)) or ""
            left += len(re.findall(r'<script[^>]+src=|rel=["\']stylesheet["\']',
                                   h, re.I))

print("pages processed : %d" % stats["pages"])
print("css inlined     : %d" % stats["css"])
print("js inlined      : %d" % stats["js"])
print("remote refs cut : %d" % stats["fonts_cut"])
print("external refs left: %d" % left)
print("output: %s" % DST)
if left:
    sys.exit("still %d external references - the page will break for her" % left)
