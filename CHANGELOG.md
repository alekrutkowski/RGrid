# Changelog

All notable changes to RGrid are documented here.

## 0.9.2 – 2026-06-11

### Added

- Markdown-aware cell hover pop-ups. Pure text cells show their complete stored text and render the same bold and italic syntax as the grid.
- A dedicated help section explaining package detection, automatic installation, workbook-wide `library()` attachment, calculation-order implications, and the safer `package::function()` style.

### Changed

- Added a small visual gap below the example-workbook replacement callout in the full help page.
- Replaced native browser cell titles with a styled RGrid tooltip while preserving formula, error, spill, object, and plot details for non-text cells.

## 0.9.1 – 2026-06-11

### Added

- Minimal inline Markdown rendering for text cells: `**bold**` and `__bold__` render in bold, while `*italic*` and `_italic_` render in italics.
- Regression tests for every example-workbook label that previously produced `#PARSE!`, plus ggplot2 and lattice cell labels.

### Fixed

- Replaced the punctuation-based plain-text heuristic with positive detection of actual R expressions, preventing ordinary labels containing commas, colons, hyphens, parentheses, plus signs, exclamation marks, or namespace-like text from being parsed as R.
- Stored example-workbook labels explicitly as literal text.
- Returned ggplot2 and lattice objects now display as `Plot` with `ggplot2` or `lattice` in superscript, and both retain the plot marker in the cell corner.
- The base line-plot example now ends with `invisible(NULL)` instead of returning the helper object from `grid()`.
- Plot-pane captions distinguish R, ggplot2, and lattice plots.

## 0.9.0 – 2026-06-11

### Added

- A title-bar **Load an example workbook** button immediately before **Help & cheatsheet**.
- A new five-sheet, commented example workbook covering references, dynamic spills, names, `eurodata::importData()`, `data.table::dcast()`, `rio::import()`, imported literal text, lists and other R objects, base graphics, ggplot2, lattice, and common corner cases.
- Static and browser checks for blank startup, button placement, the five example sheets, and architecture-specific package installation in exported RGrid scripts.

### Changed

- A fresh browser session with empty local storage now starts with a blank worksheet.
- **New workbook** now creates a blank workbook rather than reloading example data.
- Exported RGrid R scripts call `webr::install()` only on the `wasm32` architecture. Standard R architectures use `install.packages()` even if the `webr` namespace happens to be installed.
- Help, README, release notes, package metadata, and tests were synchronized with the new startup and export behavior.

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
