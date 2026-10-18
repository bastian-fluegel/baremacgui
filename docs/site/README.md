# Documentation web app

Open `index.html` in a browser, or serve this folder (with `docs/screenshots` next to it) from any static host.

Rules this folder keeps, checked by `tests/test_site.py`:
- Four files, written by hand or generated (`data.js` by `python tools/make_site.py`). No library, no build step.
- Nothing is loaded from elsewhere: no CDN, no font, no image, no request of any kind. The page ships a Content-Security-Policy
  that would block it anyway (`default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'`).
- The JavaScript only presents: it reads `data.js` and builds the page (navigation, search, theme, copy button). It sends nothing,
  stores nothing but the chosen theme in `localStorage`, and uses no inline style, no `innerHTML` and no `eval`.
- Without JavaScript the page shows nothing; the same content is in `docs/REFERENCE.md` and the README.
