# Changelog

All notable changes to RGrid are documented here.

## 0.8.0 – 2026-06-10

### Added

- Value-only import of Excel workbooks, CSV files, and TSV files into new worksheets.
- F1 documentation lookup for the R function under the formula cursor.
- Clickable `fx` link to the R function index.
- A1/R1C1 display and reference-insertion toggle.
- Compact two-line ribbon commands with matching icons.
- GitHub Pages deployment workflow, web app manifest, and release metadata.

### Fixed

- Removed the object-attribute display mode that could fail while constructing attribute rows.
- Swapped the RGrid R-script import and export icons so they match their actions.
- Added built-in F1 help for `ref()` instead of opening the general R function index.
- Displayed `ref()` F1 help in a styled in-page dialog rather than a plain popup page.
- Added an Expand all / Collapse all control to the list tree viewer.

### Changed

- Spill triangles are displayed in the top-left corner.
- Ribbon command names are more explicit about imports and value-only exports.
- webR explicitly uses the PostMessage channel on hosts such as GitHub Pages that cannot provide cross-origin-isolation headers.
