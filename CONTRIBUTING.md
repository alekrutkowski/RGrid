# Contributing

RGrid is a no-build static web application. The main files are `index.html`, `app.css`, and `app.js`.

## Local development

Run either:

```bash
python serve.py
```

or:

```bash
Rscript serve.R
```

Then open `http://127.0.0.1:8080`.

## Checks before committing

```bash
cp app.js /tmp/rgrid-app.mjs
node --check /tmp/rgrid-app.mjs
python tests/static_check.py
python -m py_compile serve.py
```

The `.mjs` copy is intentional: it makes Node parse `app.js` with the same module rules used by the browser.

An optional deterministic browser test is included. It uses local webR and SheetJS test doubles, so it does not download R or parse a real Excel workbook:

```bash
python -m pip install playwright
playwright install chromium
python tests/browser_smoke.py
```

Set `CHROMIUM_PATH` when using a system Chromium executable instead of Playwright's bundled browser.

Before a release, also perform a live browser test with the real webR CDN and a representative `.xlsx` file. Check formula entry, CSV/TSV/Excel import, autosave, RGrid R-script restoration, F1 documentation, both reference styles, object displays, plots, exports, and light/dark modes.
