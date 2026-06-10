# RGrid 0.8.0 release notes

RGrid 0.8.0 adds external data import, contextual R function help, and an A1/R1C1 display toggle. It is packaged as a no-build static site suitable for deployment through GitHub Pages.

## Highlights

- Import `.xlsx`, `.xls`, `.xlsb`, `.xlsm`, `.csv`, `.tsv`, and delimited `.txt` files.
- Press F1 over a formula function to open its core R manual or CRAN package reference; `ref()` uses a styled in-page RGrid help box.
- Toggle worksheet headings and newly inserted references between A1 and R1C1 forms.
- Expand or collapse the complete nested structure in the list tree viewer with one button.
- Deploy from the `main` branch with the included GitHub Actions workflow.

## Deployment

1. Commit the contents of this directory to the repository root.
2. Push the `main` branch to GitHub.
3. In **Settings → Pages**, select **GitHub Actions** as the source if it is not selected automatically.
4. The included workflow deploys the repository root as the static site.

GitHub Pages cannot add the COOP and COEP headers used by webR's SharedArrayBuffer channel. RGrid therefore selects webR's supported PostMessage channel on Pages. Interrupting running R code and interactive console input are unavailable in that mode, but spreadsheet calculations remain local to the browser.
