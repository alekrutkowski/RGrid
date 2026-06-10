# Security

RGrid executes workbook formulas as R code inside webR in the user's browser. Workbooks and imported RGrid scripts should therefore be treated as executable code.

- Review RGrid R scripts before importing them.
- Package installation and formula networking can contact external services.
- Workbook autosaves are stored in the current browser profile's local storage.
- No workbook data is intentionally sent to an RGrid server because the application has no backend.

Report security issues privately to the repository maintainer rather than opening a public issue with exploit details.
