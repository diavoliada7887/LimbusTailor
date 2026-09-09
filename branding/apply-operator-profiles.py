from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path.cwd()
UI_FILE = ROOT / "src/app/ui/MainWindow.ui"
MAIN_CPP = ROOT / "src/app/MainWindow.cpp"
OUT_OPTIONS_CPP = ROOT / "src/core/filters/output/OptionsWidget.cpp"


def direct_layout(widget):
    for child in widget:
        if child.tag == "layout":
            return child
    raise RuntimeError(f"direct layout missing on {widget.get('name')}")


def prop_number(layout, name, value):
    prop = None
    for child in layout.findall("property"):
        if child.get("name") == name:
            prop = child
            break
    if prop is None:
        prop = ET.Element("property", {"name": name})
        num = ET.SubElement(prop, "number")
        num.text = str(value)
        first_item = next((i for i, c in enumerate(layout) if c.tag == "item"), len(layout))
        layout.insert(first_item, prop)
    else:
        num = prop.find("number")
        if num is None:
            raise RuntimeError(f"property {name} is not numeric")
        num.text = str(value)


def make_label(name, text):
    w = ET.Element("widget", {"class": "QLabel", "name": name})
    p = ET.SubElement(w, "property", {"name": "text"})
    s = ET.SubElement(p, "string")
    s.text = text
    return w


def make_button(name, text):
    w = ET.Element("widget", {"class": "QPushButton", "name": name})
    p = ET.SubElement(w, "property", {"name": "text"})
    s = ET.SubElement(p, "string")
    s.text = text
    return w


def make_item_with_widget(widget):
    item = ET.Element("item")
    item.append(widget)
    return item


# ---------------------------------------------------------------------------
# Compact named-profile bar above the bottom settings strip.
# The workspace script has already converted verticalLayout_3 to a QHBoxLayout.
tree = ET.parse(UI_FILE)
root = tree.getroot()
dock_contents = root.find(".//widget[@name='dockWidgetContents_5']")
if dock_contents is None:
    raise RuntimeError("dockWidgetContents_5 not found")
layout = direct_layout(dock_contents)
if layout.get("name") != "verticalLayout_3":
    raise RuntimeError(f"unexpected filters dock layout: {layout.get('name')}")

# Idempotence guard for local testing / repeated application.
if root.find(".//widget[@name='limbusProfileBar']") is None:
    existing_items = [child for child in list(layout) if child.tag == "item"]
    if len(existing_items) < 2:
        raise RuntimeError("filters dock must contain stage list + options")
    for item in existing_items:
        layout.remove(item)

    layout.set("class", "QVBoxLayout")
    prop_number(layout, "spacing", 4)
    for name in ("leftMargin", "topMargin", "rightMargin", "bottomMargin"):
        prop_number(layout, name, 4)

    profile_bar = ET.Element("widget", {"class": "QWidget", "name": "limbusProfileBar", "native": "true"})
    max_prop = ET.SubElement(profile_bar, "property", {"name": "maximumSize"})
    size = ET.SubElement(max_prop, "size")
    ET.SubElement(size, "width").text = "16777215"
    ET.SubElement(size, "height").text = "36"
    bar_layout = ET.SubElement(profile_bar, "layout", {"class": "QHBoxLayout", "name": "limbusProfileBarLayout"})
    prop_number(bar_layout, "spacing", 6)
    for name in ("leftMargin", "topMargin", "rightMargin", "bottomMargin"):
        prop_number(bar_layout, name, 0)

    bar_layout.append(make_item_with_widget(make_label("limbusProfileLabel", "Профиль настроек:")))

    combo = ET.Element("widget", {"class": "QComboBox", "name": "limbusProfileCombo"})
    min_prop = ET.SubElement(combo, "property", {"name": "minimumSize"})
    min_size = ET.SubElement(min_prop, "size")
    ET.SubElement(min_size, "width").text = "210"
    ET.SubElement(min_size, "height").text = "0"
    bar_layout.append(make_item_with_widget(combo))
    bar_layout.append(make_item_with_widget(make_button("limbusProfileLoadButton", "Загрузить")))
    bar_layout.append(make_item_with_widget(make_button("limbusProfileSaveButton", "Сохранить")))
    bar_layout.append(make_item_with_widget(make_button("limbusProfileDeleteButton", "Удалить")))

    spacer_item = ET.Element("item")
    spacer = ET.SubElement(spacer_item, "spacer", {"name": "limbusProfileSpacer"})
    op = ET.SubElement(spacer, "property", {"name": "orientation"})
    ET.SubElement(op, "enum").text = "Qt::Horizontal"
    sp = ET.SubElement(spacer, "property", {"name": "sizeType"})
    ET.SubElement(sp, "enum").text = "QSizePolicy::Expanding"
    hint = ET.SubElement(spacer, "property", {"name": "sizeHint", "stdset": "0"})
    hint_size = ET.SubElement(hint, "size")
    ET.SubElement(hint_size, "width").text = "40"
    ET.SubElement(hint_size, "height").text = "20"
    bar_layout.append(spacer_item)

    strip = ET.Element("widget", {"class": "QWidget", "name": "limbusSettingsStrip", "native": "true"})
    strip_layout = ET.SubElement(strip, "layout", {"class": "QHBoxLayout", "name": "limbusSettingsStripLayout"})
    prop_number(strip_layout, "spacing", 8)
    for name in ("leftMargin", "topMargin", "rightMargin", "bottomMargin"):
        prop_number(strip_layout, name, 0)
    for item in existing_items:
        strip_layout.append(item)

    layout.append(make_item_with_widget(profile_bar))
    layout.append(make_item_with_widget(strip))

ET.indent(tree, space=" ", level=0)
tree.write(UI_FILE, encoding="UTF-8", xml_declaration=True)


# ---------------------------------------------------------------------------
# Named processing profiles. We intentionally exclude geometry/session keys and
# snapshot everything else, including the existing LimbusTailor last-profile
# XML, output DPI, TIFF/JPEG/PNG settings, margins, content tuning and naming.
cpp = MAIN_CPP.read_text(encoding="utf-8")

include_marker = '#include <QMessageBox>\n'
if include_marker not in cpp:
    raise RuntimeError("MainWindow include marker not found")
cpp = cpp.replace(
    include_marker,
    include_marker + '#include <QInputDialog>\n#include <QLineEdit>\n#include <QStringList>\n',
    1,
)

constructor_marker = "    setupUi(this);\n    setupStatusBar();\n"
if constructor_marker not in cpp:
    raise RuntimeError("MainWindow constructor setup marker not found")
profile_code = r'''    setupUi(this);
    setupStatusBar();

    // LimbusTailor named operator profiles.  The automatically remembered
    // last-profile remains active; named profiles are snapshots of the same
    // processing defaults so 50-page archive batches don't need re-entry.
    auto limbusIsProfileSetting = [](QString const& key) {
        if (key.startsWith(QLatin1String("limbustailor/profiles/"))
            || key.startsWith(QLatin1String("limbustailor/profile_manager/"))
            || key == QLatin1String("limbustailor/ui_layout_version")) {
            return false;
        }
        static const QStringList excludedPrefixes = QStringList()
            << QStringLiteral("main_window/")
            << QStringLiteral("docking_panels/")
            << QStringLiteral("thumbnails/")
            << QStringLiteral("hot_keys/")
            << QStringLiteral("project/")
            << QStringLiteral("auto-save_project/")
            << QStringLiteral("add_file_dlg/");
        for (QString const& prefix : excludedPrefixes) {
            if (key.startsWith(prefix)) {
                return false;
            }
        }
        return key != QLatin1String("lastInputDir");
    };

    auto limbusProfileId = [](QString name) {
        name = name.trimmed();
        name.replace(QLatin1Char('/'), QLatin1Char('_'));
        name.replace(QLatin1Char('\\'), QLatin1Char('_'));
        return name;
    };

    auto limbusRefreshProfiles = [this]() {
        QSettings s;
        const QString selected = s.value(
            QStringLiteral("limbustailor/profile_manager/selected")
        ).toString();
        limbusProfileCombo->blockSignals(true);
        limbusProfileCombo->clear();
        s.beginGroup(QStringLiteral("limbustailor/profiles"));
        QStringList ids = s.childGroups();
        s.endGroup();
        ids.sort(Qt::CaseInsensitive);
        for (QString const& id : ids) {
            const QString name = s.value(
                QStringLiteral("limbustailor/profiles/%1/name").arg(id), id
            ).toString();
            limbusProfileCombo->addItem(name, id);
        }
        const int idx = limbusProfileCombo->findData(selected);
        if (idx >= 0) {
            limbusProfileCombo->setCurrentIndex(idx);
        }
        limbusProfileCombo->blockSignals(false);
        const bool have = limbusProfileCombo->count() > 0;
        limbusProfileLoadButton->setEnabled(have);
        limbusProfileDeleteButton->setEnabled(have);
    };

    connect(limbusProfileCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, [this](int) {
        QSettings().setValue(
            QStringLiteral("limbustailor/profile_manager/selected"),
            limbusProfileCombo->currentData().toString()
        );
    });

    connect(limbusProfileSaveButton, &QPushButton::clicked, this,
            [this, limbusIsProfileSetting, limbusProfileId, limbusRefreshProfiles]() {
        bool ok = false;
        QString suggested = limbusProfileCombo->currentText();
        QString const name = QInputDialog::getText(
            this, tr("Save settings profile"), tr("Profile name:"),
            QLineEdit::Normal, suggested, &ok
        ).trimmed();
        if (!ok || name.isEmpty()) {
            return;
        }
        const QString id = limbusProfileId(name);
        if (id.isEmpty()) {
            return;
        }

        QSettings live;
        const QString base = QStringLiteral("limbustailor/profiles/%1").arg(id);
        const QStringList liveKeys = live.allKeys();
        live.remove(base);
        live.setValue(base + QStringLiteral("/name"), name);
        for (QString const& key : liveKeys) {
            if (limbusIsProfileSetting(key)) {
                live.setValue(base + QStringLiteral("/values/") + key, live.value(key));
            }
        }
        live.setValue(QStringLiteral("limbustailor/profile_manager/selected"), id);
        live.sync();
        limbusRefreshProfiles();
        const int idx = limbusProfileCombo->findData(id);
        if (idx >= 0) {
            limbusProfileCombo->setCurrentIndex(idx);
        }
        appStatusBar->showMessage(tr("Settings profile saved: %1").arg(name), 4000);
    });

    connect(limbusProfileLoadButton, &QPushButton::clicked, this,
            [this, limbusIsProfileSetting]() {
        const QString id = limbusProfileCombo->currentData().toString();
        if (id.isEmpty()) {
            return;
        }
        QSettings live;
        const QString base = QStringLiteral("limbustailor/profiles/%1").arg(id);
        if (!live.contains(base + QStringLiteral("/name"))) {
            return;
        }

        // Clear only processing/default settings.  Window geometry, docking,
        // recents and the profile library itself are deliberately preserved.
        const QStringList liveKeys = live.allKeys();
        for (QString const& key : liveKeys) {
            if (limbusIsProfileSetting(key)) {
                live.remove(key);
            }
        }

        QSettings profile;
        profile.beginGroup(base + QStringLiteral("/values"));
        const QStringList keys = profile.allKeys();
        for (QString const& key : keys) {
            live.setValue(key, profile.value(key));
        }
        profile.endGroup();
        live.setValue(QStringLiteral("limbustailor/profile_manager/selected"), id);
        live.sync();

        CommandLine::updateSettings();
        GlobalStaticSettings::updateSettings();
        settingsChanged();
        appStatusBar->showMessage(
            tr("Settings profile loaded: %1. It is the default for the next project/batch.")
                .arg(limbusProfileCombo->currentText()),
            6000
        );
    });

    connect(limbusProfileDeleteButton, &QPushButton::clicked, this,
            [this, limbusRefreshProfiles]() {
        const QString id = limbusProfileCombo->currentData().toString();
        if (id.isEmpty()) {
            return;
        }
        const QString name = limbusProfileCombo->currentText();
        if (QMessageBox::question(
                this, tr("Delete settings profile"),
                tr("Delete profile '%1'?").arg(name),
                QMessageBox::Yes | QMessageBox::No, QMessageBox::No
            ) != QMessageBox::Yes) {
            return;
        }
        QSettings s;
        s.remove(QStringLiteral("limbustailor/profiles/%1").arg(id));
        s.remove(QStringLiteral("limbustailor/profile_manager/selected"));
        s.sync();
        limbusRefreshProfiles();
    });

    limbusRefreshProfiles();
'''
cpp = cpp.replace(constructor_marker, profile_code, 1)

# The operator-tuned proportions from the production screenshot: a deliberately
# broad thumbnail rail for fast visual QC and a slightly taller bottom strip.
old_layout_v3 = """    if (limbusUiLayoutVersion < 3) {
        addDockWidget(Qt::LeftDockWidgetArea, dockWidgetThumbnails);
        addDockWidget(Qt::BottomDockWidgetArea, dockWidget_4);
        resizeDocks(QList<QDockWidget*>() << dockWidgetThumbnails,
                    QList<int>() << 280, Qt::Horizontal);
        resizeDocks(QList<QDockWidget*>() << dockWidget_4,
                    QList<int>() << 255, Qt::Vertical);
        settings.setValue(QStringLiteral(\"limbustailor/ui_layout_version\"), 3);
    }
"""
new_layout_v4 = """    if (limbusUiLayoutVersion < 4) {
        addDockWidget(Qt::LeftDockWidgetArea, dockWidgetThumbnails);
        addDockWidget(Qt::BottomDockWidgetArea, dockWidget_4);
        resizeDocks(QList<QDockWidget*>() << dockWidgetThumbnails,
                    QList<int>() << 1000, Qt::Horizontal);
        resizeDocks(QList<QDockWidget*>() << dockWidget_4,
                    QList<int>() << 285, Qt::Vertical);
        settings.setValue(QStringLiteral(\"limbustailor/ui_layout_version\"), 4);
    }
"""
if old_layout_v3 not in cpp:
    raise RuntimeError("workspace v3 migration marker not found")
cpp = cpp.replace(old_layout_v3, new_layout_v4, 1)

MAIN_CPP.write_text(cpp, encoding="utf-8")


# ---------------------------------------------------------------------------
# Output is the most frequently repeated production setup.  Persist DPI as a
# real default as soon as the operator changes it, and compact archive naming
# into three rows so Output reads as adjacent columns in the bottom strip.
out_cpp = OUT_OPTIONS_CPP.read_text(encoding="utf-8")

dpi_marker = '''void\nOptionsWidget::dpiChanged(std::set<PageId> const& pages, Dpi const& dpi)\n{\n    for (PageId const& page_id : pages) {\n        m_ptrSettings->setDpi(page_id, dpi);\n    }\n'''
if dpi_marker not in out_cpp:
    raise RuntimeError("output dpiChanged marker not found")
out_cpp = out_cpp.replace(
    dpi_marker,
    '''void\nOptionsWidget::dpiChanged(std::set<PageId> const& pages, Dpi const& dpi)\n{\n    // LimbusTailor: output DPI is part of the reusable operator profile.\n    QSettings dpiSettings;\n    dpiSettings.setValue(_key_output_default_dpi_x, dpi.horizontal());\n    dpiSettings.setValue(_key_output_default_dpi_y, dpi.vertical());\n\n    for (PageId const& page_id : pages) {\n        m_ptrSettings->setDpi(page_id, dpi);\n    }\n''',
    1,
)

old_naming_layout = '''    namingLayout->addWidget(namingEnabled, 0, 0, 1, 2);\n    namingLayout->addWidget(new QLabel(tr("Case index:"), namingBox), 1, 0);\n    namingLayout->addWidget(namingIndex, 1, 1);\n    namingLayout->addWidget(new QLabel(tr("Template:"), namingBox), 2, 0);\n    namingLayout->addWidget(namingTemplate, 2, 1);\n    namingLayout->addWidget(new QLabel(tr("Start sheet:"), namingBox), 3, 0);\n    namingLayout->addWidget(namingStart, 3, 1);\n    namingLayout->addWidget(new QLabel(tr("Digits:"), namingBox), 4, 0);\n    namingLayout->addWidget(namingWidth, 4, 1);\n    namingLayout->addWidget(new QLabel(tr("Front suffix:"), namingBox), 5, 0);\n    namingLayout->addWidget(namingFront, 5, 1);\n    namingLayout->addWidget(new QLabel(tr("Back suffix:"), namingBox), 6, 0);\n    namingLayout->addWidget(namingBack, 6, 1);\n    namingLayout->addWidget(new QLabel(tr("First side:"), namingBox), 7, 0);\n    namingLayout->addWidget(namingFirstSide, 7, 1);\n    namingLayout->addWidget(namingPreview, 8, 0, 1, 2);\n'''
new_naming_layout = '''    // Wide bottom strip: archive naming is a compact three-row card rather\n    // than the old tall right-panel form.\n    namingLayout->setContentsMargins(6, 6, 6, 6);\n    namingLayout->setHorizontalSpacing(8);\n    namingLayout->setVerticalSpacing(4);\n    namingIndex->setMinimumWidth(120);\n    namingTemplate->setMinimumWidth(250);\n    namingFront->setMinimumWidth(70);\n    namingBack->setMinimumWidth(70);\n\n    namingLayout->addWidget(namingEnabled, 0, 0, 1, 2);\n    namingLayout->addWidget(new QLabel(tr("Case index:"), namingBox), 0, 2);\n    namingLayout->addWidget(namingIndex, 0, 3);\n    namingLayout->addWidget(new QLabel(tr("Template:"), namingBox), 0, 4);\n    namingLayout->addWidget(namingTemplate, 0, 5);\n\n    namingLayout->addWidget(new QLabel(tr("Start sheet:"), namingBox), 1, 0);\n    namingLayout->addWidget(namingStart, 1, 1);\n    namingLayout->addWidget(new QLabel(tr("Digits:"), namingBox), 1, 2);\n    namingLayout->addWidget(namingWidth, 1, 3);\n    namingLayout->addWidget(new QLabel(tr("First side:"), namingBox), 1, 4);\n    namingLayout->addWidget(namingFirstSide, 1, 5);\n\n    namingLayout->addWidget(new QLabel(tr("Front suffix:"), namingBox), 2, 0);\n    namingLayout->addWidget(namingFront, 2, 1);\n    namingLayout->addWidget(new QLabel(tr("Back suffix:"), namingBox), 2, 2);\n    namingLayout->addWidget(namingBack, 2, 3);\n    namingLayout->addWidget(namingPreview, 2, 4, 1, 2);\n'''
if old_naming_layout not in out_cpp:
    raise RuntimeError("archive naming layout marker not found")
out_cpp = out_cpp.replace(old_naming_layout, new_naming_layout, 1)
OUT_OPTIONS_CPP.write_text(out_cpp, encoding="utf-8")

print("Applied named operator profiles, persistent output DPI and compact Output naming")
