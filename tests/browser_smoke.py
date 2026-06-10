import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

WEBR_STUB = r'''
export const ChannelType = { PostMessage: 'post-message' };
function scalarNode(value) { return { values: [value] }; }
function packed(value, kind = 'scalar') {
  return {
    type: 'list',
    names: ['ok','nrow','ncol','kind','object_kind','plot_kind','object_class','preserve_object','values','tree_label','tree_type','tree_summary','tree_parent'],
    values: [scalarNode(true), scalarNode(1), scalarNode(1), scalarNode(typeof value), scalarNode(kind), scalarNode(''), scalarNode(typeof value), scalarNode(false), scalarNode(value), {values:[]},{values:[]},{values:[]},{values:[]}]
  };
}
function expressionFrom(code) {
  const m = code.match(/\.rgrid_value\s*<-\s*\{\n([\s\S]*?)\n\}/);
  return m ? m[1].trim() : '';
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
    else if (/^['\"]/.test(expr)) { try { value = JSON.parse(expr); } catch {} }
    return { result: new Result(packed(value)), images: [], output: [] };
  }
  async purge() {}
}
export class WebR {
  constructor(options = {}) { this.options = options; this.Shelter = Shelter; window.__webrOptions = options; }
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
export function read() {
  return { SheetNames: ['First', 'Second'], Sheets: { First: {id:1}, Second: {id:2} } };
}
export const utils = {
  sheet_to_json(sheet) {
    return sheet.id === 1 ? [['Name','Value'],['alpha',11],['=literal',22]] : [['Second sheet'],['ok']];
  },
  aoa_to_sheet() { return {}; },
  book_new() { return {}; },
  book_append_sheet() {},
};
export function writeFile() {}
'''


def inline_app_html():
    html = (ROOT / 'index.html').read_text()
    html = html.replace(
        '<link rel="stylesheet" href="vendor/codemirror/lib/codemirror.css">',
        f'<style>{(ROOT / "vendor/codemirror/lib/codemirror.css").read_text()}</style>',
    )
    html = html.replace(
        '<link rel="stylesheet" href="app.css">',
        f'<style>{(ROOT / "app.css").read_text()}</style>',
    )
    for rel in [
        'vendor/codemirror/lib/codemirror.js',
        'vendor/codemirror/mode/r/r.js',
        'vendor/codemirror/addon/edit/matchbrackets.js',
        'vendor/codemirror/addon/display/placeholder.js',
    ]:
        html = html.replace(
            f'<script src="{rel}"></script>',
            f'<script>{(ROOT / rel).read_text()}</script>',
        )
    prep = """<script>
      window.__opened = [];
      window.__popupBodies = [];
      window.open = (url) => {
        let bodyText = '';
        const body = { style: {} };
        Object.defineProperty(body, 'textContent', {
          get: () => bodyText,
          set: value => { bodyText = String(value); window.__popupBodies.push(bodyText); }
        });
        return {
          opener: null,
          document: { title: '', body },
          location: { replace: next => window.__opened.push(next) },
          close() {}
        };
      };
    </script>"""
    html = html.replace(
        '<script type="module" src="app.js"></script>',
        prep + '<script type="module">' + (ROOT / 'app.js').read_text() + '</script>',
    )
    return html


with sync_playwright() as p:
    launch_options = {'headless': True, 'args': ['--no-sandbox']}
    if os.environ.get('CHROMIUM_PATH'): launch_options['executable_path'] = os.environ['CHROMIUM_PATH']
    browser = p.chromium.launch(**launch_options)
    context = browser.new_context(viewport={'width': 1600, 'height': 1000})
    page = context.new_page()
    page.route(
        'https://webr.r-wasm.org/v0.6.0/webr.mjs',
        lambda route: route.fulfill(
            status=200,
            content_type='text/javascript',
            headers={'Access-Control-Allow-Origin': '*'},
            body=WEBR_STUB,
        ),
    )
    page.route(
        'https://cdn.sheetjs.com/xlsx-0.20.3/package/xlsx.mjs',
        lambda route: route.fulfill(
            status=200,
            content_type='text/javascript',
            headers={'Access-Control-Allow-Origin': '*'},
            body=XLSX_STUB,
        ),
    )
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.set_content(inline_app_html(), wait_until='networkidle')
    page.wait_for_function("document.querySelector('#runtimeStatusText').textContent.includes('webR ready')")
    assert not errors, errors

    expected = {
        'importScriptBtn': 'Import from RGrid R script',
        'namesBtn': 'Name manager',
        'toggleElementNamesBtn': 'Show element names',
        'plotsBtn': 'Show plots',
        'plotSettingsBtn': 'Set plot size',
        'renameSheetBtn': 'Rename current sheet',
        'deleteSheetBtn': 'Delete current sheet',
        'exportRBtn': 'Export to RGrid R script',
        'exportCsvBtn': 'Export to CSV (zipped, only values)',
        'exportXlsxBtn': 'Export to Excel (only values)',
        'referenceStyleBtn': 'Toggle A1/R1C1',
    }
    for element_id, text in expected.items():
        actual = ' '.join(page.locator(f'#{element_id} .ribbon-button-label').inner_text().split())
        assert actual == text, (element_id, actual)

    assert page.locator('#toggleAttributesBtn').count() == 0
    assert page.locator('#importScriptBtn .ribbon-icon').inner_text() == 'R↓'
    assert page.locator('#exportRBtn .ribbon-icon').inner_text() == 'R↥'

    cell = page.locator('td[data-address="A1"]')
    cell.evaluate("el => el.classList.add('spill-anchor')")
    style = cell.evaluate(
        "el => ({position:getComputedStyle(el).backgroundPosition, image:getComputedStyle(el).backgroundImage})"
    )
    assert style['position'].startswith('0% 0%') or style['position'].startswith('left top'), style
    assert 'linear-gradient' in style['image']
    cell.evaluate("el => el.classList.remove('spill-anchor')")

    sheetjs_requests = []
    page.on('request', lambda req: sheetjs_requests.append(req.url) if 'sheetjs.com' in req.url else None)
    page.set_input_files('#importDataInput', files=[{
        'name': 'sample.csv',
        'mimeType': 'text/csv',
        'buffer': b'Label,Value\nalpha,1\n"=literal",2\n',
    }])
    page.wait_for_function(
        "[...document.querySelectorAll('.sheet-tab')].some(x => x.textContent === 'sample')"
    )
    assert not sheetjs_requests, sheetjs_requests
    assert page.locator('td[data-address="A1"]').inner_text() == 'Label'
    assert page.locator('td[data-address="A3"]').inner_text() == '=literal'

    page.set_input_files('#importDataInput', files=[{
        'name': 'book.xlsx',
        'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'buffer': b'fake-xlsx',
    }])
    page.wait_for_function(
        "[...document.querySelectorAll('.sheet-tab')].some(x => x.textContent === 'book – First') && "
        "[...document.querySelectorAll('.sheet-tab')].some(x => x.textContent === 'book – Second')"
    )
    tabs = page.locator('.sheet-tab').all_inner_texts()
    assert 'book – First' in tabs and 'book – Second' in tabs

    page.click('#referenceStyleBtn')
    assert page.locator('th.col-header[data-col="1"]').inner_text() == '1'
    assert page.locator('#referenceStyleBtn .ribbon-icon').inner_text() == 'R1C1'

    cm = page.locator('.CodeMirror')
    cm.evaluate(
        "el => { const cm = el.CodeMirror; cm.setValue('=lm(mpg ~ wt)'); "
        "cm.setCursor({line:0,ch:3}); cm.focus(); }"
    )
    page.keyboard.press('F1')
    page.wait_for_function("window.__opened.length >= 1")
    assert page.evaluate('window.__opened.at(-1)') == (
        'https://stat.ethz.ch/R-manual/R-devel/library/stats/html/lm.html'
    )

    cm.evaluate(
        "el => { const cm = el.CodeMirror; cm.setValue('=eurodata::importData()'); "
        "cm.setCursor({line:0,ch:20}); cm.focus(); }"
    )
    page.keyboard.press('F1')
    page.wait_for_function("window.__opened.length >= 2")
    assert page.evaluate('window.__opened.at(-1)') == (
        'https://cran.r-project.org/web/packages/eurodata/refman/eurodata.html#importData'
    )

    opened_before_ref = page.evaluate('window.__opened.length')
    cm.evaluate(
        """el => { const cm = el.CodeMirror; cm.setValue('=ref(\"A1\")');
        cm.setCursor({line:0,ch:4}); cm.focus(); }"""
    )
    page.keyboard.press('F1')
    page.wait_for_function("document.querySelector('#refHelpDialog').open")
    assert page.evaluate('window.__opened.length') == opened_before_ref
    ref_help = page.locator('#refHelpDialog').inner_text()
    assert 'case-insensitive Excel-style reference' in ref_help
    assert 'A1:G5' in ref_help and 'B8#' in ref_help and 'Name manager' in ref_help
    assert page.locator('#refHelpDialog .ref-help-examples article').count() == 5
    if os.environ.get('RGRID_REF_HELP_SCREENSHOT'):
        page.screenshot(path=os.environ['RGRID_REF_HELP_SCREENSHOT'], full_page=True)
    page.get_by_role('button', name='Got it').click()
    page.wait_for_function("!document.querySelector('#refHelpDialog').open")

    page.evaluate(
        """() => {
          const tree = document.querySelector('#objectTree');
          tree.innerHTML = '<details class="object-node" open><summary>root</summary>' +
            '<details class="object-node"><summary>branch</summary>' +
            '<details class="object-node"><summary>nested</summary><div>leaf</div></details>' +
            '</details></details>';
          tree.querySelector('details').dispatchEvent(new Event('toggle'));
          document.querySelector('#objectDialog').showModal();
        }"""
    )
    page.wait_for_function("!document.querySelector('#expandObjectTreeBtn').disabled")
    assert page.locator('#expandObjectTreeBtn').inner_text() == 'Expand all'
    page.locator('#expandObjectTreeBtn').click()
    assert page.evaluate("[...document.querySelectorAll('#objectTree details')].every(x => x.open)")
    assert page.locator('#expandObjectTreeBtn').inner_text() == 'Collapse all'
    if os.environ.get('RGRID_OBJECT_TREE_SCREENSHOT'):
        page.screenshot(path=os.environ['RGRID_OBJECT_TREE_SCREENSHOT'], full_page=True)
    page.locator('#expandObjectTreeBtn').click()
    assert page.evaluate("[...document.querySelectorAll('#objectTree details')].every(x => !x.open)")
    assert page.locator('#expandObjectTreeBtn').inner_text() == 'Expand all'
    page.locator('#objectDialog').get_by_role('button', name='Close', exact=True).last.click()

    assert page.locator('#fxHelpLink').get_attribute('href') == 'https://rdrr.io/r/'
    assert not errors, errors
    if os.environ.get('RGRID_SMOKE_SCREENSHOT'):
        page.screenshot(path=os.environ['RGRID_SMOKE_SCREENSHOT'], full_page=True)
    browser.close()
    print('browser smoke test passed')
