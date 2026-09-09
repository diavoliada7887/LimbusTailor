from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path.cwd()
UI_FILE = ROOT / "src/app/ui/MainWindow.ui"
MAIN_CPP = ROOT / "src/app/MainWindow.cpp"
MAIN_H = ROOT / "src/app/MainWindow.h"
OUT_SETTINGS_H = ROOT / "src/core/filters/output/Settings.h"
OUT_SETTINGS_CPP = ROOT / "src/core/filters/output/Settings.cpp"
SC_SETTINGS_H = ROOT / "src/core/filters/select_content/Settings.h"
SC_SETTINGS_CPP = ROOT / "src/core/filters/select_content/Settings.cpp"
PL_SETTINGS_CPP = ROOT / "src/core/filters/page_layout/Settings.cpp"
PL_OPTIONS_CPP = ROOT / "src/core/filters/page_layout/OptionsWidget.cpp"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one marker, found {count}")
    return text.replace(old, new, 1)


def direct_layout(widget):
    for child in widget:
        if child.tag == "layout":
            return child
    raise RuntimeError(f"direct layout missing on {widget.get('name')}")


def make_checkbox(name: str, text: str):
    w = ET.Element("widget", {"class": "QCheckBox", "name": name})
    p = ET.SubElement(w, "property", {"name": "text"})
    s = ET.SubElement(p, "string")
    s.text = text
    return w


def make_item_with_widget(widget):
    item = ET.Element("item")
    item.append(widget)
    return item


def inject_before_function_end(text: str, signature: str, injection: str, label: str) -> str:
    start = text.find(signature)
    if start < 0:
        raise RuntimeError(f"{label}: signature not found")
    open_brace = text.find("{", start)
    if open_brace < 0:
        raise RuntimeError(f"{label}: opening brace not found")
    depth = 0
    i = open_brace
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[:i] + injection + text[i:]
        i += 1
    raise RuntimeError(f"{label}: closing brace not found")


# Profile scope control: named profiles carry both VALUES and APPLY SCOPE.
tree = ET.parse(UI_FILE)
root = tree.getroot()
bar = root.find(".//widget[@name='limbusProfileBar']")
if bar is None:
    raise RuntimeError("limbusProfileBar not found; apply-operator-profiles.py must run first")
bar_layout = direct_layout(bar)
if root.find(".//widget[@name='limbusProfileAllPages']") is None:
    children = list(bar_layout)
    spacer_index = None
    for idx, item in enumerate(children):
        if item.tag == "item" and item.find("spacer[@name='limbusProfileSpacer']") is not None:
            spacer_index = idx
            break
    if spacer_index is None:
        raise RuntimeError("limbusProfileSpacer not found")
    bar_layout.insert(spacer_index, make_item_with_widget(
        make_checkbox("limbusProfileAllPages", "Для всех страниц")
    ))
ET.indent(tree, space=" ", level=0)
tree.write(UI_FILE, encoding="UTF-8", xml_declaration=True)


# Output profile persistence + bulk apply.
# Fixes the case where the operator selected Color but the reusable profile
# still contained an older B/W value because only setParams() was persisted.
out_h = OUT_SETTINGS_H.read_text(encoding="utf-8")
out_h = replace_once(out_h, "class AbstractRelinker;\n",
                     "class AbstractRelinker;\nclass PageSequence;\n",
                     "output Settings PageSequence forward declaration")
out_h = replace_once(out_h,
                     "    void setParams(PageId const& page_id, Params const& params);\n",
                     "    void setParams(PageId const& page_id, Params const& params);\n\n"
                     "    void applyLastProfileToPages(PageSequence const& pages);\n",
                     "output Settings apply profile declaration")
OUT_SETTINGS_H.write_text(out_h, encoding="utf-8")

out_cpp = OUT_SETTINGS_CPP.read_text(encoding="utf-8")
out_cpp = replace_once(out_cpp, '#include "AbstractRelinker.h"\n',
                       '#include "AbstractRelinker.h"\n#include "PageSequence.h"\n',
                       "output Settings PageSequence include")
for signature, label in (
    ("Settings::setColorParams(PageId const& page_id, ColorParams const& prms, ColorParamsApplyFilter const& filter)", "output color persistence"),
    ("Settings::setDpi(PageId const& page_id, Dpi const& dpi)", "output dpi persistence"),
    ("Settings::setDewarpingMode(PageId const& page_id, DewarpingMode const& mode)", "output dewarp-mode persistence"),
    ("Settings::setDepthPerception(PageId const& page_id, DepthPerception const& depth_perception)", "output depth persistence"),
    ("Settings::setDespeckleLevel(PageId const& page_id, DespeckleLevel level)", "output despeckle persistence"),
):
    out_cpp = inject_before_function_end(
        out_cpp, signature,
        "    saveLastOutputParams(m_perPageParams.find(page_id)->second);\n",
        label
    )
profile_apply_impl = r'''
void
Settings::applyLastProfileToPages(PageSequence const& pages)
{
    Params reusable(loadLastOutputParams());
    // The distortion curve belongs to one physical page and must not be cloned.
    reusable.setDistortionModel(dewarping::DistortionModel());

    QMutexLocker const locker(&m_mutex);
    for (PageInfo const& page : pages) {
        Utils::mapSetValue(m_perPageParams, page.id(), reusable);
    }
}

'''
marker = "std::unique_ptr<OutputParams>\nSettings::getOutputParams(PageId const& page_id) const\n"
if marker not in out_cpp:
    raise RuntimeError("output profile bulk-apply insertion marker not found")
out_cpp = out_cpp.replace(marker, profile_apply_impl + marker, 1)
OUT_SETTINGS_CPP.write_text(out_cpp, encoding="utf-8")


# Select Content: copy reusable switches and borders to already visited pages,
# while deliberately preserving every page's own content/page rectangles.
sc_h = SC_SETTINGS_H.read_text(encoding="utf-8")
sc_h = replace_once(sc_h,
                    "    std::unique_ptr<Params> getPageParams(PageId const& page_id) const;\n",
                    "    std::unique_ptr<Params> getPageParams(PageId const& page_id) const;\n\n"
                    "    void applyLastProfileToExistingPages();\n",
                    "select content bulk-profile declaration")
SC_SETTINGS_H.write_text(sc_h, encoding="utf-8")

sc_cpp = SC_SETTINGS_CPP.read_text(encoding="utf-8")
sc_marker = "void\nSettings::clearPageParams(PageId const& page_id)\n"
if sc_marker not in sc_cpp:
    raise RuntimeError("select content bulk-profile insertion marker not found")
sc_impl = r'''
void
Settings::applyLastProfileToExistingPages()
{
    QSettings profile;
    const bool contentDetect = profile.value(
        "limbustailor/last_profile/select_content/content_detect", true
    ).toBool();
    const bool pageDetect = profile.value(
        "limbustailor/last_profile/select_content/page_detect", false
    ).toBool();
    const bool fineTune = profile.value(
        "limbustailor/last_profile/select_content/fine_tune", false
    ).toBool();
    const AutoManualMode mode = profile.value(
        "limbustailor/last_profile/select_content/mode", static_cast<int>(MODE_AUTO)
    ).toInt() == static_cast<int>(MODE_MANUAL) ? MODE_MANUAL : MODE_AUTO;

    Margins borders;
    borders.setLeft(profile.value(
        "limbustailor/last_profile/select_content/border_left", 0.0
    ).toDouble());
    borders.setTop(profile.value(
        "limbustailor/last_profile/select_content/border_top", 0.0
    ).toDouble());
    borders.setRight(profile.value(
        "limbustailor/last_profile/select_content/border_right", 0.0
    ).toDouble());
    borders.setBottom(profile.value(
        "limbustailor/last_profile/select_content/border_bottom", 0.0
    ).toDouble());

    QMutexLocker locker(&m_mutex);
    for (PageParams::value_type& kv : m_pageParams) {
        Params& params = kv.second;
        params.setContentDetect(contentDetect);
        params.setPageDetect(pageDetect);
        params.setFineTuneCorners(fineTune);
        params.setMode(mode);
        params.setPageBorders(borders);
    }
}

'''
sc_cpp = sc_cpp.replace(sc_marker, sc_impl + sc_marker, 1)
SC_SETTINGS_CPP.write_text(sc_cpp, encoding="utf-8")


# Page Layout: archive sheets are independent by default.  Null alignment
# prevents one page from forcing soft margins / placement changes on another.
pl_cpp = PL_SETTINGS_CPP.read_text(encoding="utf-8")
pl_cpp = replace_once(pl_cpp,
                      "    Alignment const m_defaultAlignment;\n",
                      "    Alignment m_defaultAlignment;\n",
                      "page layout mutable default alignment")
pl_cpp = replace_once(
    pl_cpp,
    "        m_defaultHardMarginsMM(page_layout::Settings::defaultHardMarginsMM()),\n"
    "        m_defaultAlignment(Alignment::TOP, Alignment::HCENTER)\n"
    "{\n"
    "}\n",
    "        m_defaultHardMarginsMM(page_layout::Settings::defaultHardMarginsMM()),\n"
    "        m_defaultAlignment(Alignment::TOP, Alignment::HCENTER)\n"
    "{\n"
    "    m_defaultAlignment.setNull(true);\n"
    "}\n",
    "page layout null default alignment")
PL_SETTINGS_CPP.write_text(pl_cpp, encoding="utf-8")


# With "For all pages" active, margin edits are truly global immediately.
pl_opt = PL_OPTIONS_CPP.read_text(encoding="utf-8")
scope_code = r'''
    if (QSettings().value(
            "limbustailor/last_profile/apply_all_pages", true
        ).toBool()) {
        PageSequence const pages(m_pageSelectionAccessor.allPages());
        for (PageInfo const& page : pages) {
            m_ptrSettings->setHardMarginsMM(page.id(), m_marginsMM);
            Alignment alignment(m_ptrSettings->getPageAlignment(page.id()));
            if (!alignment.isNull()) {
                alignment.setNull(true);
                m_ptrSettings->setPageAlignment(page.id(), alignment);
            }
        }
        emit invalidateAllThumbnails();
    }
'''
for signature, label in (
    ("OptionsWidget::horMarginsChanged(double const val)", "global horizontal margins"),
    ("OptionsWidget::vertMarginsChanged(double const val)", "global vertical margins"),
):
    pl_opt = inject_before_function_end(pl_opt, signature, scope_code, label)
PL_OPTIONS_CPP.write_text(pl_opt, encoding="utf-8")


# MainWindow owns the remembered scope and materializes the reusable template
# into every page both on profile load and immediately before End-to-End.
main_h = MAIN_H.read_text(encoding="utf-8")
main_h = replace_once(main_h,
                      "    void prepareArchiveOutputNames(PageSequence const& pages);\n",
                      "    void prepareArchiveOutputNames(PageSequence const& pages);\n"
                      "    void applyOperatorProfileToAllPages();\n",
                      "MainWindow profile scope helper declaration")
MAIN_H.write_text(main_h, encoding="utf-8")

main_cpp = MAIN_CPP.read_text(encoding="utf-8")
main_cpp = replace_once(
    main_cpp,
    "#include <QStringList>\n",
    "#include <QStringList>\n"
    '#include "filters/output/Settings.h"\n'
    '#include "filters/select_content/Settings.h"\n'
    '#include "filters/page_layout/Settings.h"\n'
    '#include "filters/page_layout/Alignment.h"\n',
    "MainWindow profile scope includes")

checkbox_setup_marker = "    connect(limbusProfileCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),\n"
checkbox_setup = r'''    QSettings limbusScopeSettings;
    const QString limbusScopeKey = QStringLiteral("limbustailor/last_profile/apply_all_pages");
    if (!limbusScopeSettings.contains(limbusScopeKey)) {
        limbusScopeSettings.setValue(limbusScopeKey, true);
    }
    limbusProfileAllPages->setChecked(
        limbusScopeSettings.value(limbusScopeKey, true).toBool()
    );
    connect(limbusProfileAllPages, &QCheckBox::toggled, this, [](bool checked) {
        QSettings().setValue(
            QStringLiteral("limbustailor/last_profile/apply_all_pages"), checked
        );
    });

'''
if checkbox_setup_marker not in main_cpp:
    raise RuntimeError("MainWindow profile checkbox setup marker not found")
main_cpp = main_cpp.replace(checkbox_setup_marker, checkbox_setup + checkbox_setup_marker, 1)

load_marker = (
    "        live.setValue(QStringLiteral(\"limbustailor/profile_manager/selected\"), id);\n"
    "        live.sync();\n\n"
    "        CommandLine::updateSettings();\n"
)
load_repl = (
    "        live.setValue(QStringLiteral(\"limbustailor/profile_manager/selected\"), id);\n"
    "        live.sync();\n\n"
    "        const bool applyAllPages = live.value(\n"
    "            QStringLiteral(\"limbustailor/last_profile/apply_all_pages\"), true\n"
    "        ).toBool();\n"
    "        live.setValue(QStringLiteral(\"limbustailor/last_profile/apply_all_pages\"), applyAllPages);\n"
    "        limbusProfileAllPages->setChecked(applyAllPages);\n\n"
    "        CommandLine::updateSettings();\n"
)
main_cpp = replace_once(main_cpp, load_marker, load_repl, "profile load restores scope")

main_cpp = replace_once(
    main_cpp,
    "        GlobalStaticSettings::updateSettings();\n"
    "        settingsChanged();\n"
    "        appStatusBar->showMessage(\n",
    "        GlobalStaticSettings::updateSettings();\n"
    "        settingsChanged();\n"
    "        applyOperatorProfileToAllPages();\n"
    "        if (isProjectLoaded() && !isBatchProcessingInProgress()) {\n"
    "            updateMainArea();\n"
    "        }\n"
    "        appStatusBar->showMessage(\n",
    "profile load applies to current project")

helper_marker = "void\nMainWindow::setRouteConfigurationMode(bool const enabled)\n"
if helper_marker not in main_cpp:
    raise RuntimeError("MainWindow route helper insertion marker not found")
helper_impl = r'''void
MainWindow::applyOperatorProfileToAllPages()
{
    if (!isProjectLoaded()) {
        return;
    }

    QSettings settings;
    if (!settings.value(
            QStringLiteral("limbustailor/last_profile/apply_all_pages"), true
        ).toBool()) {
        return;
    }

    PageSequence const pages(m_ptrPages->toPageSequence(PAGE_VIEW));

    page_layout::Settings* const layoutSettings =
        m_ptrStages->pageLayoutFilter()->getSettings();
    MarginsWithAuto const hardMargins = page_layout::Settings::defaultHardMarginsMM();
    for (PageInfo const& page : pages) {
        layoutSettings->setHardMarginsMM(page.id(), hardMargins);
        page_layout::Alignment alignment(layoutSettings->getPageAlignment(page.id()));
        if (!alignment.isNull()) {
            alignment.setNull(true);
            layoutSettings->setPageAlignment(page.id(), alignment);
        }
    }

    m_ptrStages->selectContentFilter()->getSettings()->applyLastProfileToExistingPages();
    m_ptrStages->outputFilter()->getSettings()->applyLastProfileToPages(pages);

    invalidateAllThumbnails();
}

'''
main_cpp = main_cpp.replace(helper_marker, helper_impl + helper_marker, 1)

through_marker = "    const int output_idx = m_ptrStages->outputFilterIdx();\n"
main_cpp = replace_once(
    main_cpp,
    through_marker,
    "    // Remembered profile scope: materialize it into every page before\n"
    "    // building the End-to-End queue.\n"
    "    applyOperatorProfileToAllPages();\n\n" + through_marker,
    "End-to-end applies all-pages profile")

MAIN_CPP.write_text(main_cpp, encoding="utf-8")

print("Applied V5 profile scope: real all-pages templates, output persistence, stable page layout")
