from pathlib import Path

path = Path("src/core/filters/page_layout/OptionsWidget.cpp")
text = path.read_text(encoding="utf-8")

replacements = {
    'marginFillColor->addItem(QStringLiteral("White"), QStringLiteral("WHITE"));':
        'marginFillColor->addItem(tr("White"), QStringLiteral("WHITE"));',
    'marginFillColor->addItem(QStringLiteral("Black"), QStringLiteral("BLACK"));':
        'marginFillColor->addItem(tr("Black"), QStringLiteral("BLACK"));',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"Arkhivum UI override marker not found: {old}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
