import re, zipfile, html
from pathlib import Path

docx = Path(r"c:\Users\Андрей\Desktop\Диссертация\Диссертация В.02.docx")
out = Path(r"c:\Users\Андрей\Desktop\Диссертация\AutoAssess\.tools\dissertation_text.txt")

with zipfile.ZipFile(docx) as z:
    xml = z.read("word/document.xml").decode("utf-8")

# paragraph breaks
xml = re.sub(r"</w:p>", "\n", xml)
# tab
xml = xml.replace("<w:tab/>", "\t")
text = re.sub(r"<[^>]+>", "", text if (text := xml) else xml)
text = html.unescape(text)
# collapse spaces per line
lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
lines = [ln for ln in lines if ln]
out.write_text("\n".join(lines), encoding="utf-8")
print(f"lines={len(lines)} chars={len(text)}")
