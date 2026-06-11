# RGrid 0.9.2 release notes

RGrid 0.9.2 adds focused help and hover-display refinements without changing the workbook format or calculation model.

## Highlights

- Pure text cells now use a styled hover pop-up that shows the complete stored cell text.
- Bold and italic Markdown is rendered inside that pop-up, so formatting remains visible even when a spreadsheet column is too narrow.
- Formula, error, spill, object, and plot cells retain their existing diagnostic hover information in the new pop-up.
- The full help page now explains both `library(package)` and `package::function()` usage.
- The help explicitly states that all sheets share one R session: after a `library()` cell evaluates, its package is attached for cells in every sheet. It also explains the fresh-recalculation order caveat and recommends qualified `::` calls when order independence matters.
- A small vertical gap was added below the example-workbook replacement callout.

## Compatibility

The workbook format remains version 6. Existing autosaves and RGrid R-script files remain compatible. Package installation and standard-R export behavior are unchanged.

## Validation

Run `npm test` for static checks and `npm run test:browser` for the headless browser regression suite.
