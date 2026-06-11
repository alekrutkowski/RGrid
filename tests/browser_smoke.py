import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEBR_STUB = r'''
export const ChannelType = { PostMessage: 'post-message' };
function scalarNode(value) { return { values: [value] }; }
function packed(value, kind = 'scalar', plotKind = '') {
  return {
    type: 'list',
    names: ['ok','nrow','ncol','kind','object_kind','plot_kind','object_class','preserve_object','values','tree_label','tree_type','tree_summary','tree_parent'],
    values: [
      scalarNode(true), scalarNode(1), scalarNode(1), scalarNode(typeof value),
      scalarNode(kind), scalarNode(plotKind), scalarNode(typeof value), scalarNode(plotKind !== ''),
      scalarNode(value), {values:[]}, {values:[]}, {values:[]}, {values:[]}
    ]
  };
}
function expressionFrom(code) {
  const match = code.match(/\.rgrid_value\s*<-\s*\{\n([\s\S]*?)\n\}/);
  return match ? match[1].trim() : '';
}
class Result {
  constructor(value) { this.value = value; }
  async toJs() { return this.value; }
}
class Shelter {
  async captureR(code) {
    const expr = expressionFrom(code);
    let value = expr;
    if (/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(expr)) value = Number(expr);
    else if (expr === 'TRUE') value = true;
    else if (expr === 'FALSE') value = false;
    else if (/^['"]/.test(expr)) {
      try { value = JSON.parse(expr); } catch {}
    }
    if (expr.includes('ggplot2::ggplot')) return { result: new Result(packed('<list [9]>', 'plot', 'ggplot')), images: [], output: [] };
    if (expr.includes('lattice::xyplot')) return { result: new Result(packed('<list [24]>', 'plot', 'lattice')), images: [], output: [] };
    return { result: new Result(packed(value)), images: [], output: [] };
  }
  async purge() {}
}
export class WebR {
  constructor(options = {}) {
    this.options = options;
    this.Shelter = Shelter;
    window.__webrOptions = options;
  }
  async init() {}
  async evalRVoid() {}
  async evalRBoolean() { return true; }
  async installPackages() {}
  async evalRString(code) {
    if (code.includes('.name <- "lm"')) return 'stats\tlm';
    if (code.includes('.name <- "capture.output"')) return 'utils\tcapture.output';
    if (code.includes('.name <- "importData"')) return 'eurodata\timportData';
    return '';
  }
}
'''

XLSX_STUB = r'''
export function read() { return { SheetNames: [], Sheets: {} }; }
export const utils = {
  sheet_to_json() { return []; },
  aoa_to_sheet() { return {}; },
  book_new() { return {}; },
  book_append_sheet() {},
};
export function writeFile() {}
'''


def inline_app_html():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    html = html.replace(
        '<link rel="stylesheet" href="vendor/codemirror/lib/codemirror.css">',
        f'<style>{(ROOT / "vendor/codemirror/lib/codemirror.css").read_text(encoding="utf-8")}</style>',
    )
    html = html.replace(
        '<link rel="stylesheet" href="app.css">',
        f'<style>{(ROOT / "app.css").read_text(encoding="utf-8")}</style>',
    )
    html = html.replace('<link rel="icon" href="favicon.svg" type="image/svg+xml">', '')
    html = html.replace('<link rel="manifest" href="manifest.webmanifest">', '')
    storage_stub = """<script>
      (() => {
        const values = new Map();
        Object.defineProperty(window, 'localStorage', { value: {
          getItem: key => values.has(String(key)) ? values.get(String(key)) : null,
          setItem: (key, value) => values.set(String(key), String(value)),
          removeItem: key => values.delete(String(key)),
          clear: () => values.clear(),
        }});
      })();
    </script>"""
    html = html.replace('<body>', '<body>' + storage_stub, 1)
    for rel in [
        "vendor/codemirror/lib/codemirror.js",
        "vendor/codemirror/mode/r/r.js",
        "vendor/codemirror/addon/edit/matchbrackets.js",
        "vendor/codemirror/addon/display/placeholder.js",
    ]:
        source = (ROOT / rel).read_text(encoding="utf-8").replace("</script>", "<\\/script>")
        html = html.replace(f'<script src="{rel}"></script>', f'<script>{source}</script>')
    app_source = (ROOT / "app.js").read_text(encoding="utf-8").replace("</script>", "<\\/script>")
    html = html.replace('<script type="module" src="app.js"></script>', f'<script type="module">{app_source}</script>')
    return html

def main():
    with sync_playwright() as playwright:
        launch_options = {
            "headless": True,
            "args": ["--no-sandbox"],
            "executable_path": os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium"),
        }
        browser = playwright.chromium.launch(**launch_options)
        context = browser.new_context(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        page = context.new_page()
        page.route(
            "https://webr.r-wasm.org/v0.6.0/webr.mjs",
            lambda route: route.fulfill(
                status=200,
                content_type="text/javascript",
                headers={"Access-Control-Allow-Origin": "*"},
                body=WEBR_STUB,
            ),
        )
        page.route(
            "https://cdn.sheetjs.com/xlsx-0.20.3/package/xlsx.mjs",
            lambda route: route.fulfill(
                status=200,
                content_type="text/javascript",
                headers={"Access-Control-Allow-Origin": "*"},
                body=XLSX_STUB,
            ),
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(inline_app_html(), wait_until="networkidle")
        page.wait_for_function("document.querySelector('#runtimeStatusText').textContent.includes('webR ready')")

        assert page.locator(".sheet-tab").all_inner_texts() == ["Sheet1"]
        assert page.locator('td[data-address="A1"]').inner_text() == ""
        title_order = page.locator(".title-actions > *").evaluate_all("els => els.map(x => x.id)")
        assert title_order[:2] == ["exampleWorkbookBtn", "helpBtn"], title_order
        assert page.locator("#exampleWorkbookBtn").inner_text() == "Load an example workbook"

        page.once("dialog", lambda dialog: dialog.accept())
        page.click("#exampleWorkbookBtn")
        page.wait_for_function("document.querySelectorAll('.sheet-tab').length === 5")
        assert page.locator(".sheet-tab").all_inner_texts() == [
            "Start Here", "References", "Data & Pivot", "Objects & Import", "Plots"
        ]
        assert page.locator('td[data-address="A1"]').inner_text() == "RGrid example workbook"
        assert page.locator('td[data-address="A15"] strong').inner_text() == "Workbook tips"
        assert page.locator('td[data-address="A23"] strong').all_inner_texts() == ["bold", "also bold"]
        assert page.locator('td[data-address="A23"] em').all_inner_texts() == ["italic", "also italic"]

        markdown_cell = page.locator('td[data-address="A23"]')
        markdown_cell.hover()
        page.wait_for_selector('#cellTooltip:not([hidden])')
        assert page.locator('#cellTooltip').inner_text() == "Text formatting: bold, also bold, italic, and also italic."
        assert page.locator('#cellTooltip strong').all_inner_texts() == ["bold", "also bold"]
        assert page.locator('#cellTooltip em').all_inner_texts() == ["italic", "also italic"]
        assert markdown_cell.get_attribute("title") is None
        page.mouse.move(1500, 900)
        page.wait_for_function("document.querySelector('#cellTooltip').hidden")

        text_cells = {
            "Start Here": ["A16", "A17", "A18", "A19"],
            "References": ["A1", "A2", "A16", "A23", "A26", "A27", "A28", "D5", "H4", "H5"],
            "Data & Pivot": ["A1", "A4", "A22", "F4", "K22"],
            "Objects & Import": ["A1", "A2", "A13", "A17", "A18", "A26", "A27", "E25", "E26"],
            "Plots": ["A1", "A2", "A28"],
        }
        for sheet_name, addresses in text_cells.items():
            page.get_by_role("tab", name=sheet_name, exact=True).click()
            for address in addresses:
                value = page.locator(f'td[data-address="{address}"]').inner_text()
                assert value and value != "#PARSE!", (sheet_name, address, value)

        page.get_by_role("tab", name="Data & Pivot", exact=True).click()
        page.locator('td[data-address="A23"]').click()
        assert "eurodata::importData" in page.locator(".CodeMirror").evaluate("el => el.CodeMirror.getValue()")
        page.locator('td[data-address="F5"]').click()
        assert "data.table::dcast" in page.locator(".CodeMirror").evaluate("el => el.CodeMirror.getValue()")

        page.get_by_role("tab", name="Objects & Import", exact=True).click()
        page.locator('td[data-address="B19"]').click()
        assert "rio::import" in page.locator(".CodeMirror").evaluate("el => el.CodeMirror.getValue()")

        page.get_by_role("tab", name="Plots", exact=True).click()
        page.locator('td[data-address="B12"]').click()
        assert "ggplot2::ggplot" in page.locator(".CodeMirror").evaluate("el => el.CodeMirror.getValue()")
        assert page.locator('td[data-address="B12"]').inner_text() == "Plotggplot2"
        assert page.locator('td[data-address="B12"] sup.plot-kind-superscript').inner_text() == "ggplot2"
        assert "has-plot" in page.locator('td[data-address="B12"]').get_attribute("class")
        page.locator('td[data-address="B12"]').hover()
        page.wait_for_selector('#cellTooltip:not([hidden])')
        assert "Input: ={" in page.locator('#cellTooltip').inner_text()
        assert "ggplot2 plot object" in page.locator('#cellTooltip').inner_text()
        assert page.locator('#cellTooltip strong').count() == 0
        page.mouse.move(1500, 900)
        page.wait_for_function("document.querySelector('#cellTooltip').hidden")
        assert page.locator('td[data-address="B22"]').inner_text() == "Plotlattice"
        assert page.locator('td[data-address="B22"] sup.plot-kind-superscript').inner_text() == "lattice"
        assert "has-plot" in page.locator('td[data-address="B22"]').get_attribute("class")

        with page.expect_download() as download_info:
            page.click("#exportRBtn")
        download = download_info.value
        export_path = Path(download.path())
        exported = export_path.read_text(encoding="utf-8")
        assert 'identical(R.version$arch, "wasm32")' in exported
        guard = exported.index('identical(R.version$arch, "wasm32")')
        assert exported.index("webr::install(missing)") > guard
        assert "install.packages(missing, repos = repositories)" in exported
        assert 'rgrid_define_sheet("Start Here"' in exported

        page.once("dialog", lambda dialog: dialog.accept())
        page.click("#newWorkbookBtn")
        page.wait_for_function("document.querySelectorAll('.sheet-tab').length === 1")
        assert page.locator(".sheet-tab").all_inner_texts() == ["Sheet1"]
        assert page.locator('td[data-address="A1"]').inner_text() == ""

        assert not errors, errors
        browser.close()
    print("browser smoke test passed")


if __name__ == "__main__":
    main()
