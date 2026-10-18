"""The documentation web app (docs/site) stays small and self-contained: no libraries, nothing loaded from
elsewhere, and JavaScript that only shows things. These checks run on every OS."""
import pathlib
import re

SITE = pathlib.Path(__file__).parent.parent / "docs" / "site"
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def read(name):
    return (SITE / name).read_text(encoding="utf-8")


def test_markup_and_styles_load_nothing_from_elsewhere():
    html, css = read("index.html"), read("style.css")
    assert "http" not in html.replace("http-equiv", "") and "http" not in css
    assert "@import" not in css and "url(" not in css
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html), "no inline script"
    assert "<style" not in html and " style=" not in html, "no inline style"
    sources = re.findall(r'(?:src|href)="([^"#][^"]*)"', html)
    assert sources and all(not s.startswith(("http", "//")) for s in sources), sources
    assert "script-src 'self'" in html and "default-src 'none'" in html


def test_script_only_presents_data():
    js = read("app.js")
    forbidden = ["fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "eval(", "new Function", "import(", "importScripts",
                 "innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "createContextualFragment",
                 "cookie", "indexedDB", "postMessage", "window.open", ".style.", 'style:', "setAttribute(\"style\"",
                 "<script", "location.href", "location.assign", "location.replace"]
    assert not [word for word in forbidden if word in js], [word for word in forbidden if word in js]
    assert js.replace(SVG_NAMESPACE, "").count("http") == 0
    assert not re.search(r"\bsrc\s*:\s*[\"']https?:", js)


def test_no_library_is_bundled():
    names = sorted(p.name for p in SITE.iterdir())
    assert names == ["README.md", "app.js", "data.js", "index.html", "style.css"], names
