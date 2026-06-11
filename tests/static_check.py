from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "index.html",
    "help.html",
    "app.js",
    "app.css",
    "favicon.svg",
    "manifest.webmanifest",
    "package.json",
    "README.md",
    "CHANGELOG.md",
    "RELEASE_NOTES.md",
    "LICENSE",
    "LICENSES.md",
    ".nojekyll",
    ".github/workflows/pages.yml",
    ".github/workflows/validate.yml",
    "vendor/codemirror/LICENSE",
    "vendor/codemirror/lib/codemirror.css",
    "vendor/codemirror/lib/codemirror.js",
    "vendor/codemirror/mode/r/r.js",
    "vendor/codemirror/addon/edit/matchbrackets.js",
    "vendor/codemirror/addon/display/placeholder.js",
}
missing = sorted(path for path in REQUIRED if not (ROOT / path).exists())
if missing:
    raise SystemExit(f"Missing required release files: {', '.join(missing)}")


class DocumentChecker(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.ids = set()
        self.duplicates = []
        self.references = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicates.append(element_id)
            self.ids.add(element_id)
        for key in ("src", "href"):
            value = attributes.get(key)
            if value:
                self.references.append(value)


for filename in ("index.html", "help.html"):
    checker = DocumentChecker(filename)
    checker.feed((ROOT / filename).read_text(encoding="utf-8"))
    if checker.duplicates:
        raise SystemExit(f"{filename}: duplicate ids: {', '.join(checker.duplicates)}")
    for reference in checker.references:
        split = urlsplit(reference)
        if split.scheme or reference.startswith(("#", "mailto:", "data:")):
            continue
        target = (ROOT / split.path).resolve()
        if not target.exists():
            raise SystemExit(f"{filename}: missing local reference {reference}")

index = (ROOT / "index.html").read_text(encoding="utf-8")
app = (ROOT / "app.js").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
help_text = (ROOT / "help.html").read_text(encoding="utf-8")
manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

if index.index('id="exampleWorkbookBtn"') > index.index('id="helpBtn"'):
    raise SystemExit("Load an example workbook must be immediately to the left of Help & cheatsheet")
if "Load an example workbook" not in index:
    raise SystemExit("Example-workbook button label is missing")
if "let workbook = loadWorkbook() ?? createBlankWorkbook();" not in app:
    raise SystemExit("Fresh startup is not wired to a blank workbook")
if "loadWorkbook() ?? createExampleWorkbook()" in app:
    raise SystemExit("Old automatic example-workbook startup is still present")
if "replaceWorkbook(createBlankWorkbook(), 'create new workbook')" not in app:
    raise SystemExit("New workbook does not create a blank workbook")
if "replaceWorkbook(createExampleWorkbook(), 'load example workbook')" not in app:
    raise SystemExit("Example-workbook button is not wired")

example_block = app[app.index("function createExampleWorkbook()") : app.index("function loadWorkbook()")]
expected_sheets = ["Start Here", "References", "Data & Pivot", "Objects & Import", "Plots"]
for name in expected_sheets:
    if f"name: '{name}'" not in example_block:
        raise SystemExit(f"Example worksheet is missing: {name}")
if len(re.findall(r"\bname: '(?:Start Here|References|Data & Pivot|Objects & Import|Plots)'", example_block)) != 5:
    raise SystemExit("The example workbook must contain exactly five named worksheets")

required_examples = [
    'ref("B8#")',
    'ref("R8C2")',
    "Start Here",
    'data.table::dcast',
    'eurodata::importData',
    'rio::import',
    'ggplot2::ggplot',
    'lattice::xyplot',
    'Nested R list',
    "literal: true",
]
for token in required_examples:
    if token not in example_block:
        raise SystemExit(f"Example workbook is missing coverage for {token}")

for token in ("function startsWithRCallExpression", "function appendInlineMarkdown", "plot-kind-superscript", "'ggplot2' : 'lattice'", "invisible(NULL)"):
    if token not in app:
        raise SystemExit(f"Regression fix is missing: {token}")
for token in ("function showCellTooltip", "function hideCellTooltip", "tooltipMarkdown", "appendInlineMarkdown(els.cellTooltip, text)"):
    if token not in app:
        raise SystemExit(f"Markdown tooltip support is missing: {token}")
if 'id="cellTooltip"' not in index:
    raise SystemExit("Cell tooltip element is missing")
if "td.title = pieces.join" in app:
    raise SystemExit("Native cell titles still conflict with the custom Markdown tooltip")
for phrase in ("Packages:", "library()", "package::function()", "same R session", "Calculation order still matters"):
    if phrase not in help_text:
        raise SystemExit(f"Package help is incomplete: missing {phrase}")
if ".callout + .grid { margin-top:" not in help_text:
    raise SystemExit("Example-workbook callout spacing is missing")
if '  grid()' in example_block:
    raise SystemExit("The base-plot example still returns graphics::grid() metadata")
if "literal || isPlainTextInput(input)" not in example_block:
    raise SystemExit("Example workbook text cells are not explicitly stored as literal text")

installer = app[app.index("rgrid_install_required_packages <- function") : app.index("# ---- End executable RGrid runtime")]
if 'identical(R.version$arch, "wasm32")' not in installer:
    raise SystemExit("Exported runtime lacks the wasm32 architecture guard")
if installer.index('webr::install(missing)') < installer.index('identical(R.version$arch, "wasm32")'):
    raise SystemExit("webr::install is not guarded by the wasm32 branch")
if "install.packages(missing, repos = repositories)" not in installer:
    raise SystemExit("Exported runtime lacks the standard-R install.packages branch")

for phrase in ("fresh", "blank", "Load an example workbook", "wasm32", "data.table::dcast", "eurodata::importData"):
    if phrase.lower() not in readme.lower():
        raise SystemExit(f"README is not synchronized: missing {phrase}")

if package.get("version") != "0.9.2":
    raise SystemExit("package.json version is not 0.9.2")
if manifest.get("start_url") != "./":
    raise SystemExit("manifest start_url must remain relative")

print("static release checks passed")
