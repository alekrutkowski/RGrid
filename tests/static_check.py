from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'index.html', 'help.html', 'app.js', 'app.css', 'favicon.svg',
    'manifest.webmanifest', 'README.md', 'LICENSE', '.nojekyll',
    '.github/workflows/pages.yml',
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
        element_id = attributes.get('id')
        if element_id:
            if element_id in self.ids:
                self.duplicates.append(element_id)
            self.ids.add(element_id)
        for key in ('src', 'href'):
            value = attributes.get(key)
            if value:
                self.references.append(value)


for filename in ('index.html', 'help.html'):
    checker = DocumentChecker(filename)
    checker.feed((ROOT / filename).read_text(encoding='utf-8'))
    if checker.duplicates:
        raise SystemExit(f"{filename}: duplicate ids: {', '.join(checker.duplicates)}")
    for reference in checker.references:
        split = urlsplit(reference)
        if split.scheme or reference.startswith(('#', 'mailto:', 'data:')):
            continue
        target = (ROOT / split.path).resolve()
        if not target.exists():
            raise SystemExit(f"{filename}: missing local reference {reference}")

print('static release checks passed')
