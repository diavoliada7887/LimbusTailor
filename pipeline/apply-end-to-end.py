from pathlib import Path

ROOT = Path(".")
CPP = ROOT / "src/app/MainWindow.cpp"
HDR = ROOT / "src/app/MainWindow.h"
RU = ROOT / "src/translations/scantailor-universal_ru.ts"
PL_FILTER_H = ROOT / "src/core/filters/page_layout/Filter.h"
PL_FILTER_CPP = ROOT / "src/core/filters/page_layout/Filter.cpp"
PL_OPTIONS_H = ROOT / "src/core/filters/page_layout/OptionsWidget.h"
PL_OPTIONS_CPP = ROOT / "src/core/filters/page_layout/OptionsWidget.cpp"
PL_TASK_CPP = ROOT / "src/core/filters/page_layout/Task.cpp"
PS_SETTINGS_CPP = ROOT / "src/core/filters/page_split/Settings.cpp"
OUT_SETTINGS_CPP = ROOT / "src/core/filters/output/Settings.cpp"
OUT_OPTIONS_CPP = ROOT / "src/core/filters/output/OptionsWidget.cpp"
OUT_NAME_H = ROOT / "src/core/OutputFileNameGenerator.h"
OUT_NAME_CPP = ROOT / "src/core/OutputFileNameGenerator.cpp"

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one marker, found {count}")
    return text.replace(old, new, 1)

# ---- MainWindow.h ---------------------------------------------------------
h = HDR.read_text(encoding="utf-8")

h = replace_once(
    h,
    "class QLayout;\n",
    "class QLayout;\nclass QAction;\n",
    "MainWindow.h forward declaration",
)

h = replace_once(
    h,
    "    void startBatchProcessing();\n\n    void stopBatchProcessing(MainAreaAction main_area = UPDATE_MAIN_AREA);\n",
    "    void startBatchProcessing();\n\n"
    "    void setRouteConfigurationMode(bool enabled);\n\n"
    "    void startThroughProcessing();\n\n"
    "    void stopBatchProcessing(MainAreaAction main_area = UPDATE_MAIN_AREA);\n",
    "MainWindow.h slots",
)

h = replace_once(
    h,
    "    void jumpToPage(int cnt, bool in_selection = false);\n",
    "    void jumpToPage(int cnt, bool in_selection = false);\n"
    "    void prepareArchiveOutputNames(PageSequence const& pages);\n",
    "MainWindow.h archive output naming helper",
)

h = replace_once(
    h,
    "    int m_curFilter;\n"
    "    int m_ignoreSelectionChanges;\n"
    "    int m_ignorePageOrderingChanges;\n"
    "    bool m_debug;\n",
    "    int m_curFilter;\n"
    "    QAction* m_routeConfigAction;\n"
    "    QAction* m_runThroughAction;\n"
    "    int m_routeConfigPreviousFilter;\n"
    "    int m_ignoreSelectionChanges;\n"
    "    int m_ignorePageOrderingChanges;\n"
    "    bool m_routeConfigMode;\n"
    "    bool m_throughProcessing;\n"
    "    bool m_debug;\n",
    "MainWindow.h members",
)

HDR.write_text(h, encoding="utf-8")

# ---- Page Layout: route setup + no uniform-size normalization -------------
# In route setup mode, margins are editable before Select Content has run.
# During end-to-end processing, aggregate alignment (soft margins that make
# every page share the largest final canvas) can be disabled without changing
# the stored per-page alignment settings.

pl_options_h = PL_OPTIONS_H.read_text(encoding="utf-8")
pl_options_h = replace_once(
    pl_options_h,
    "    void postUpdateUI();\n\n"
    "    bool leftRightLinked() const\n",
    "    void postUpdateUI();\n\n"
    "    void setRouteSetupMode(bool enabled);\n\n"
    "    bool leftRightLinked() const\n",
    "page_layout OptionsWidget route setup declaration",
)
pl_options_h = replace_once(
    pl_options_h,
    "    bool m_leftRightLinked;\n"
    "    bool m_topBottomLinked;\n",
    "    bool m_leftRightLinked;\n"
    "    bool m_topBottomLinked;\n"
    "    bool m_routeSetupMode;\n",
    "page_layout OptionsWidget route setup member",
)
PL_OPTIONS_H.write_text(pl_options_h, encoding="utf-8")

pl_options_cpp = PL_OPTIONS_CPP.read_text(encoding="utf-8")
pl_options_cpp = replace_once(
    pl_options_cpp,
    '#include "PageInfo.h"\n',
    '#include "PageInfo.h"\n#include "PageSequence.h"\n',
    "page_layout OptionsWidget PageSequence include",
)
pl_options_cpp = replace_once(
    pl_options_cpp,
    "        m_ignoreMarginChanges(0),\n"
    "        m_leftRightLinked(true),\n"
    "        m_topBottomLinked(true)\n",
    "        m_ignoreMarginChanges(0),\n"
    "        m_leftRightLinked(true),\n"
    "        m_topBottomLinked(true),\n"
    "        m_routeSetupMode(false)\n",
    "page_layout OptionsWidget constructor",
)
pl_options_cpp = replace_once(
    pl_options_cpp,
    "OptionsWidget::~OptionsWidget()\n"
    "{\n"
    "}\n\n"
    "void\n"
    "OptionsWidget::preUpdateUI(\n",
    "OptionsWidget::~OptionsWidget()\n"
    "{\n"
    "}\n\n"
    "void\n"
    "OptionsWidget::setRouteSetupMode(bool const enabled)\n"
    "{\n"
    "    m_routeSetupMode = enabled;\n"
    "    if (enabled) {\n"
    "        // End-to-end archive route never aligns pages to each other.\n"
    "        // Persist NULL alignment for all current pages so the checkbox\n"
    "        // is visibly OFF and no later code path can add soft margins.\n"
    "        PageSequence const pages(m_pageSelectionAccessor.allPages());\n"
    "        for (PageInfo const& page : pages) {\n"
    "            Alignment page_alignment(m_ptrSettings->getPageAlignment(page.id()));\n"
    "            if (!page_alignment.isNull()) {\n"
    "                page_alignment.setNull(true);\n"
    "                m_ptrSettings->setPageAlignment(page.id(), page_alignment);\n"
    "            }\n"
    "        }\n"
    "\n"
    "        if (!m_pageId.isNull()) {\n"
    "            m_alignment = m_ptrSettings->getPageAlignment(m_pageId);\n"
    "            m_alignment.setNull(true);\n"
    "            widgetAlignment->setAlignment(&m_alignment);\n"
    "            displayAlignmentText();\n"
    "        }\n"
    "\n"
    "        marginsGroup->setEnabled(true);\n"
    "        alignmentGroup->setEnabled(false);\n"
    "    }\n"
    "}\n\n"
    "void\n"
    "OptionsWidget::preUpdateUI(\n",
    "page_layout OptionsWidget route setup implementation",
)
pl_options_cpp = replace_once(
    pl_options_cpp,
    "    marginsGroup->setEnabled(false);\n"
    "    alignmentGroup->setEnabled(false);\n",
    "    marginsGroup->setEnabled(m_routeSetupMode);\n"
    "    alignmentGroup->setEnabled(false);\n",
    "page_layout OptionsWidget preUpdate state",
)
pl_options_cpp = replace_once(
    pl_options_cpp,
    "    m_pageId = page_id;\n"
    "    m_marginsMM = margins_mm;\n"
    "    m_alignment = alignment;\n",
    "    m_pageId = page_id;\n"
    "    m_marginsMM = margins_mm;\n"
    "    m_alignment = alignment;\n"
    "    if (m_routeSetupMode && !m_alignment.isNull()) {\n"
    "        m_alignment.setNull(true);\n"
    "        m_ptrSettings->setPageAlignment(page_id, m_alignment);\n"
    "    }\n",
    "page_layout force null alignment during route setup",
)
pl_options_cpp = replace_once(
    pl_options_cpp,
    "    m_marginsMM.setLeft(leftMarginSpinBox->value() * m_unitToMM);\n"
    "    m_marginsMM.setRight(rightMarginSpinBox->value() * m_unitToMM);\n"
    "\n"
    "    emit marginsSetLocally(static_cast<Margins>(m_marginsMM));\n",
    "    m_marginsMM.setLeft(leftMarginSpinBox->value() * m_unitToMM);\n"
    "    m_marginsMM.setRight(rightMarginSpinBox->value() * m_unitToMM);\n"
    "\n"
    "    // LimbusTailor: the last operator-entered margins become the defaults\n"
    "    // for the next project.  Only reusable settings are persisted; no\n"
    "    // page geometry is copied between projects.\n"
    "    QSettings margin_settings;\n"
    "    margin_settings.setValue(_key_margins_default_left, m_marginsMM.left());\n"
    "    margin_settings.setValue(_key_margins_default_right, m_marginsMM.right());\n"
    "\n"
    "    emit marginsSetLocally(static_cast<Margins>(m_marginsMM));\n",
    "page_layout persist horizontal margins",
)
pl_options_cpp = replace_once(
    pl_options_cpp,
    "    m_marginsMM.setTop(topMarginSpinBox->value() * m_unitToMM);\n"
    "    m_marginsMM.setBottom(bottomMarginSpinBox->value() * m_unitToMM);\n"
    "\n"
    "    emit marginsSetLocally(static_cast<Margins>(m_marginsMM));\n",
    "    m_marginsMM.setTop(topMarginSpinBox->value() * m_unitToMM);\n"
    "    m_marginsMM.setBottom(bottomMarginSpinBox->value() * m_unitToMM);\n"
    "\n"
    "    QSettings margin_settings;\n"
    "    margin_settings.setValue(_key_margins_default_top, m_marginsMM.top());\n"
    "    margin_settings.setValue(_key_margins_default_bottom, m_marginsMM.bottom());\n"
    "\n"
    "    emit marginsSetLocally(static_cast<Margins>(m_marginsMM));\n",
    "page_layout persist vertical margins",
)
pl_options_cpp = replace_once(
    pl_options_cpp,
    "    m_marginsMM.setAutoMargins(checked);\n"
    "    m_ptrSettings->setHardMarginsMM(m_pageId, m_marginsMM);\n",
    "    m_marginsMM.setAutoMargins(checked);\n"
    "    QSettings().setValue(_key_margins_auto_margins_default, checked);\n"
    "    m_ptrSettings->setHardMarginsMM(m_pageId, m_marginsMM);\n",
    "page_layout persist auto margins",
)

PL_OPTIONS_CPP.write_text(pl_options_cpp, encoding="utf-8")

pl_filter_h = PL_FILTER_H.read_text(encoding="utf-8")
pl_filter_h = replace_once(
    pl_filter_h,
    "    virtual void preUpdateUI(FilterUiInterface* ui, PageId const& page_id);\n\n"
    "    virtual QDomElement saveSettings(\n",
    "    virtual void preUpdateUI(FilterUiInterface* ui, PageId const& page_id);\n\n"
    "    void setRouteSetupMode(bool enabled);\n\n"
    "    void setAggregateAlignmentDisabled(bool disabled)\n"
    "    {\n"
    "        m_disableAggregateAlignment = disabled;\n"
    "    }\n\n"
    "    bool aggregateAlignmentDisabled() const\n"
    "    {\n"
    "        return m_disableAggregateAlignment;\n"
    "    }\n\n"
    "    virtual QDomElement saveSettings(\n",
    "page_layout Filter route controls declaration",
)
pl_filter_h = replace_once(
    pl_filter_h,
    "    int m_selectedPageOrder;\n",
    "    int m_selectedPageOrder;\n"
    "    bool m_disableAggregateAlignment;\n",
    "page_layout Filter aggregate member",
)
PL_FILTER_H.write_text(pl_filter_h, encoding="utf-8")

pl_filter_cpp = PL_FILTER_CPP.read_text(encoding="utf-8")
pl_filter_cpp = replace_once(
    pl_filter_cpp,
    "        m_ptrSettings(new Settings),\n"
    "        m_selectedPageOrder(0)\n",
    "        m_ptrSettings(new Settings),\n"
    "        m_selectedPageOrder(0),\n"
    "        m_disableAggregateAlignment(false)\n",
    "page_layout Filter constructor",
)
pl_filter_cpp = replace_once(
    pl_filter_cpp,
    "void\n"
    "Filter::preUpdateUI(FilterUiInterface* ui, PageId const& page_id)\n"
    "{\n"
    "    MarginsWithAuto const margins_mm(m_ptrSettings->getHardMarginsMM(page_id));\n"
    "    Alignment const alignment(m_ptrSettings->getPageAlignment(page_id));\n"
    "    m_ptrOptionsWidget->preUpdateUI(page_id, margins_mm, alignment);\n"
    "    ui->setOptionsWidget(m_ptrOptionsWidget.get(), ui->KEEP_OWNERSHIP);\n"
    "}\n\n"
    "QDomElement\n",
    "void\n"
    "Filter::preUpdateUI(FilterUiInterface* ui, PageId const& page_id)\n"
    "{\n"
    "    MarginsWithAuto const margins_mm(m_ptrSettings->getHardMarginsMM(page_id));\n"
    "    Alignment const alignment(m_ptrSettings->getPageAlignment(page_id));\n"
    "    m_ptrOptionsWidget->preUpdateUI(page_id, margins_mm, alignment);\n"
    "    ui->setOptionsWidget(m_ptrOptionsWidget.get(), ui->KEEP_OWNERSHIP);\n"
    "}\n\n"
    "void\n"
    "Filter::setRouteSetupMode(bool const enabled)\n"
    "{\n"
    "    if (m_ptrOptionsWidget.get() != 0) {\n"
    "        m_ptrOptionsWidget->setRouteSetupMode(enabled);\n"
    "    }\n"
    "}\n\n"
    "QDomElement\n",
    "page_layout Filter route setup implementation",
)
PL_FILTER_CPP.write_text(pl_filter_cpp, encoding="utf-8")

pl_task_cpp = PL_TASK_CPP.read_text(encoding="utf-8")
pl_task_cpp = replace_once(
    pl_task_cpp,
    "        QPolygonF const page_rect_phys(\n"
    "            Utils::calcPageRectPhys(\n"
    "                data.xform(), content_rect_phys,\n"
    "                params, agg_hard_size_after\n"
    "            )\n"
    "        );\n",
    "        QPolygonF page_rect_phys;\n"
    "        if (m_ptrFilter->aggregateAlignmentDisabled()) {\n"
    "            // End-to-end route: preserve hard margins, but don't add the\n"
    "            // soft margins used to normalize every page to one canvas.\n"
    "            Alignment route_alignment(params.alignment());\n"
    "            route_alignment.setNull(true);\n"
    "            Params const route_params(\n"
    "                params.hardMarginsMM(), params.pageRect(), params.contentRect(),\n"
    "                params.contentSizeMM(), route_alignment\n"
    "            );\n"
    "            page_rect_phys = Utils::calcPageRectPhys(\n"
    "                data.xform(), content_rect_phys, route_params, agg_hard_size_after\n"
    "            );\n"
    "        } else {\n"
    "            page_rect_phys = Utils::calcPageRectPhys(\n"
    "                data.xform(), content_rect_phys, params, agg_hard_size_after\n"
    "            );\n"
    "        }\n",
    "page_layout Task aggregate alignment bypass",
)
PL_TASK_CPP.write_text(pl_task_cpp, encoding="utf-8")


# ---- Reusable last-project profile ---------------------------------------
# Keep operator-entered defaults across projects without copying page-specific
# geometry.  Page Split remembers only its default layout type.  Output
# remembers Params (DPI / color mode / thresholds / dewarping / despeckle).

ps_settings_cpp = PS_SETTINGS_CPP.read_text(encoding="utf-8")
ps_settings_cpp = replace_once(
    ps_settings_cpp,
    "#include <QMutexLocker>\n",
    "#include <QMutexLocker>\n#include <QSettings>\n",
    "page_split Settings QSettings include",
)
ps_settings_cpp = replace_once(
    ps_settings_cpp,
    "Settings::Settings()\n"
    "    :   m_defaultLayoutType(AUTO_LAYOUT_TYPE)\n",
    "Settings::Settings()\n"
    "    :   m_defaultLayoutType(static_cast<LayoutType>(QSettings().value(\n"
    "            \"limbustailor/last_profile/page_split_layout_type\",\n"
    "            static_cast<int>(AUTO_LAYOUT_TYPE)\n"
    "        ).toInt()))\n",
    "page_split persistent default constructor",
)
ps_settings_cpp = replace_once(
    ps_settings_cpp,
    "    m_perPageRecords.clear();\n"
    "    m_defaultLayoutType = AUTO_LAYOUT_TYPE;\n",
    "    m_perPageRecords.clear();\n"
    "    m_defaultLayoutType = static_cast<LayoutType>(QSettings().value(\n"
    "        \"limbustailor/last_profile/page_split_layout_type\",\n"
    "        static_cast<int>(AUTO_LAYOUT_TYPE)\n"
    "    ).toInt());\n",
    "page_split persistent default clear",
)
ps_settings_cpp = replace_once(
    ps_settings_cpp,
    "    m_defaultLayoutType = layout_type;\n"
    "}\n",
    "    m_defaultLayoutType = layout_type;\n"
    "    QSettings().setValue(\n"
    "        \"limbustailor/last_profile/page_split_layout_type\",\n"
    "        static_cast<int>(layout_type)\n"
    "    );\n"
    "}\n",
    "page_split remember default layout",
)
PS_SETTINGS_CPP.write_text(ps_settings_cpp, encoding="utf-8")

out_settings_cpp = OUT_SETTINGS_CPP.read_text(encoding="utf-8")
out_settings_cpp = replace_once(
    out_settings_cpp,
    "#include <QRegularExpression>\n",
    "#include <QRegularExpression>\n#include <QSettings>\n#include <QDomDocument>\n",
    "output Settings profile includes",
)
out_settings_cpp = replace_once(
    out_settings_cpp,
    "namespace output\n"
    "{\n"
    "\n"
    "Settings::Settings()\n",
    "namespace output\n"
    "{\n"
    "\n"
    "namespace\n"
    "{\n"
    "const char* const kLastOutputParamsKey = \"limbustailor/last_profile/output_params_xml\";\n"
    "\n"
    "Params loadLastOutputParams()\n"
    "{\n"
    "    const QString xml = QSettings().value(kLastOutputParamsKey).toString();\n"
    "    if (!xml.isEmpty()) {\n"
    "        QDomDocument doc;\n"
    "        if (doc.setContent(xml)) {\n"
    "            QDomElement const root(doc.documentElement());\n"
    "            if (!root.isNull() && root.tagName() == QLatin1String(\"params\")) {\n"
    "                return Params(root);\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "    return Params();\n"
    "}\n"
    "\n"
    "void saveLastOutputParams(Params const& params)\n"
    "{\n"
    "    QDomDocument doc(QLatin1String(\"limbustailor-output-profile\"));\n"
    "    doc.appendChild(params.toXml(doc, QLatin1String(\"params\")));\n"
    "    QSettings().setValue(kLastOutputParamsKey, doc.toString(-1));\n"
    "}\n"
    "}\n"
    "\n"
    "Settings::Settings()\n",
    "output Settings profile helpers",
)
out_settings_cpp = replace_once(
    out_settings_cpp,
    "    if (it != m_perPageParams.end()) {\n"
    "        return it->second;\n"
    "    } else {\n"
    "        return Params();\n"
    "    }\n",
    "    if (it != m_perPageParams.end()) {\n"
    "        return it->second;\n"
    "    } else {\n"
    "        return loadLastOutputParams();\n"
    "    }\n",
    "output Settings use last profile",
)
out_settings_cpp = replace_once(
    out_settings_cpp,
    "    QMutexLocker const locker(&m_mutex);\n"
    "    Utils::mapSetValue(m_perPageParams, page_id, params);\n"
    "}\n",
    "    QMutexLocker const locker(&m_mutex);\n"
    "    Utils::mapSetValue(m_perPageParams, page_id, params);\n"
    "    saveLastOutputParams(params);\n"
    "}\n",
    "output Settings save last profile",
)
OUT_SETTINGS_CPP.write_text(out_settings_cpp, encoding="utf-8")

# ---- Archive output name map ----------------------------------------------
# OutputFileNameGenerator already owns the final extension decision.  Give it a
# per-logical-page base-name map prepared by MainWindow before output tasks are
# created.  This cleanly replaces _1L / _2R only when archive naming is enabled.

out_name_h = OUT_NAME_H.read_text(encoding="utf-8")
out_name_h = replace_once(
    out_name_h,
    '#include "FileNameDisambiguator.h"\n',
    '#include "FileNameDisambiguator.h"\n#include "PageId.h"\n#include <map>\n',
    "OutputFileNameGenerator archive map includes",
)
out_name_h = replace_once(
    out_name_h,
    "    QString fileNameFor(PageId const& page) const;\n"
    "\n"
    "    QString filePathFor(PageId const& page) const;\n",
    "    void clearArchiveFileNames();\n"
    "\n"
    "    void setArchiveFileName(PageId const& page, QString const& base_name);\n"
    "\n"
    "    QString fileNameFor(PageId const& page) const;\n"
    "\n"
    "    QString filePathFor(PageId const& page) const;\n",
    "OutputFileNameGenerator archive map API",
)
out_name_h = replace_once(
    out_name_h,
    "    Qt::LayoutDirection m_layoutDirection;\n"
    "};\n",
    "    Qt::LayoutDirection m_layoutDirection;\n"
    "    std::map<PageId, QString> m_archiveFileNames;\n"
    "};\n",
    "OutputFileNameGenerator archive map member",
)
OUT_NAME_H.write_text(out_name_h, encoding="utf-8")

out_name_cpp = OUT_NAME_CPP.read_text(encoding="utf-8")
out_name_cpp = replace_once(
    out_name_cpp,
    "    m_ptrDisambiguator->performRelinking(relinker);\n"
    "    m_outDir = relinker.substitutionPathFor(RelinkablePath(m_outDir, RelinkablePath::Dir));\n"
    "}\n"
    "\n"
    "QString\n"
    "OutputFileNameGenerator::fileNameFor(PageId const& page) const\n"
    "{\n",
    "    m_ptrDisambiguator->performRelinking(relinker);\n"
    "    m_outDir = relinker.substitutionPathFor(RelinkablePath(m_outDir, RelinkablePath::Dir));\n"
    "    m_archiveFileNames.clear();\n"
    "}\n"
    "\n"
    "void\n"
    "OutputFileNameGenerator::clearArchiveFileNames()\n"
    "{\n"
    "    m_archiveFileNames.clear();\n"
    "}\n"
    "\n"
    "void\n"
    "OutputFileNameGenerator::setArchiveFileName(PageId const& page, QString const& base_name)\n"
    "{\n"
    "    if (base_name.isEmpty()) {\n"
    "        m_archiveFileNames.erase(page);\n"
    "    } else {\n"
    "        m_archiveFileNames[page] = base_name;\n"
    "    }\n"
    "}\n"
    "\n"
    "QString\n"
    "OutputFileNameGenerator::fileNameFor(PageId const& page) const\n"
    "{\n"
    "    std::map<PageId, QString>::const_iterator const archive_it(m_archiveFileNames.find(page));\n"
    "    if (archive_it != m_archiveFileNames.end()) {\n"
    "        QString name(archive_it->second);\n"
    "        const QString format = GlobalStaticSettings::m_output_image_format;\n"
    "        if (format == QLatin1String(\"JPEG\") || format == QLatin1String(\"JPG\")) {\n"
    "            name += QString::fromLatin1(\".jpg\");\n"
    "        } else if (format == QLatin1String(\"PNG\")) {\n"
    "            name += QString::fromLatin1(\".png\");\n"
    "        } else {\n"
    "            name += QString::fromLatin1(\".tif\");\n"
    "        }\n"
    "        return name;\n"
    "    }\n"
    "\n",
    "OutputFileNameGenerator archive filename implementation",
)
OUT_NAME_CPP.write_text(out_name_cpp, encoding="utf-8")

# ---- Archive naming controls in Output -----------------------------------
out_options_cpp = OUT_OPTIONS_CPP.read_text(encoding="utf-8")
out_options_cpp = replace_once(
    out_options_cpp,
    "#include <QPainter>\n",
    "#include <QPainter>\n"
    "#include <QGroupBox>\n"
    "#include <QGridLayout>\n"
    "#include <QCheckBox>\n"
    "#include <QLineEdit>\n"
    "#include <QSpinBox>\n"
    "#include <QLabel>\n"
    "#include <QBoxLayout>\n",
    "output OptionsWidget archive naming includes",
)
out_options_cpp = replace_once(
    out_options_cpp,
    "    setDespeckleLevel(DESPECKLE_NORMAL);\n",
    "    // LimbusTailor: archive output naming, modelled after the existing\n"
    "    // SboeBoi / Oblegchazhka scheme: index + sheet + side.\n"
    "    QGroupBox* const namingBox = new QGroupBox(tr(\"Archive file naming\"), this);\n"
    "    QGridLayout* const namingLayout = new QGridLayout(namingBox);\n"
    "    QCheckBox* const namingEnabled = new QCheckBox(tr(\"Use archive names\"), namingBox);\n"
    "    QLineEdit* const namingIndex = new QLineEdit(namingBox);\n"
    "    QLineEdit* const namingTemplate = new QLineEdit(namingBox);\n"
    "    QSpinBox* const namingStart = new QSpinBox(namingBox);\n"
    "    QSpinBox* const namingWidth = new QSpinBox(namingBox);\n"
    "    QLineEdit* const namingFront = new QLineEdit(namingBox);\n"
    "    QLineEdit* const namingBack = new QLineEdit(namingBox);\n"
    "    QLabel* const namingPreview = new QLabel(namingBox);\n"
    "\n"
    "    namingStart->setRange(0, 9999999);\n"
    "    namingWidth->setRange(1, 12);\n"
    "    namingEnabled->setChecked(archiveSettings.value(\n"
    "        \"limbustailor/archive_naming/enabled\", false\n"
    "    ).toBool());\n"
    "    namingIndex->setText(archiveSettings.value(\n"
    "        \"limbustailor/archive_naming/index\", QString()\n"
    "    ).toString());\n"
    "    namingTemplate->setText(archiveSettings.value(\n"
    "        \"limbustailor/archive_naming/template\", QStringLiteral(\"{индекс}_{лист}{сторона}\")\n"
    "    ).toString());\n"
    "    namingStart->setValue(archiveSettings.value(\n"
    "        \"limbustailor/archive_naming/start\", 1\n"
    "    ).toInt());\n"
    "    namingWidth->setValue(archiveSettings.value(\n"
    "        \"limbustailor/archive_naming/width\", 3\n"
    "    ).toInt());\n"
    "    namingFront->setText(archiveSettings.value(\n"
    "        \"limbustailor/archive_naming/front\", QStringLiteral(\"_0\")\n"
    "    ).toString());\n"
    "    namingBack->setText(archiveSettings.value(\n"
    "        \"limbustailor/archive_naming/back\", QStringLiteral(\"_1\")\n"
    "    ).toString());\n"
    "\n"
    "    namingLayout->addWidget(namingEnabled, 0, 0, 1, 2);\n"
    "    namingLayout->addWidget(new QLabel(tr(\"Case index:\"), namingBox), 1, 0);\n"
    "    namingLayout->addWidget(namingIndex, 1, 1);\n"
    "    namingLayout->addWidget(new QLabel(tr(\"Template:\"), namingBox), 2, 0);\n"
    "    namingLayout->addWidget(namingTemplate, 2, 1);\n"
    "    namingLayout->addWidget(new QLabel(tr(\"Start sheet:\"), namingBox), 3, 0);\n"
    "    namingLayout->addWidget(namingStart, 3, 1);\n"
    "    namingLayout->addWidget(new QLabel(tr(\"Digits:\"), namingBox), 4, 0);\n"
    "    namingLayout->addWidget(namingWidth, 4, 1);\n"
    "    namingLayout->addWidget(new QLabel(tr(\"Front suffix:\"), namingBox), 5, 0);\n"
    "    namingLayout->addWidget(namingFront, 5, 1);\n"
    "    namingLayout->addWidget(new QLabel(tr(\"Back suffix:\"), namingBox), 6, 0);\n"
    "    namingLayout->addWidget(namingBack, 6, 1);\n"
    "    namingLayout->addWidget(namingPreview, 7, 0, 1, 2);\n"
    "\n"
    "    if (QBoxLayout* const box = qobject_cast<QBoxLayout*>(layout())) {\n"
    "        box->insertWidget(0, namingBox);\n"
    "    } else if (layout()) {\n"
    "        layout()->addWidget(namingBox);\n"
    "    }\n"
    "\n"
    "    auto saveNaming = [=]() {\n"
    "        QSettings s;\n"
    "        s.setValue(\"limbustailor/archive_naming/enabled\", namingEnabled->isChecked());\n"
    "        s.setValue(\"limbustailor/archive_naming/index\", namingIndex->text().trimmed());\n"
    "        s.setValue(\"limbustailor/archive_naming/template\", namingTemplate->text());\n"
    "        s.setValue(\"limbustailor/archive_naming/start\", namingStart->value());\n"
    "        s.setValue(\"limbustailor/archive_naming/width\", namingWidth->value());\n"
    "        s.setValue(\"limbustailor/archive_naming/front\", namingFront->text());\n"
    "        s.setValue(\"limbustailor/archive_naming/back\", namingBack->text());\n"
    "    };\n"
    "    auto updateNamingPreview = [=]() {\n"
    "        QString const sheet = QStringLiteral(\"%1\").arg(\n"
    "            namingStart->value(), namingWidth->value(), 10, QLatin1Char('0')\n"
    "        );\n"
    "        auto render = [=](QString const& side) {\n"
    "            QString name(namingTemplate->text());\n"
    "            name.replace(QStringLiteral(\"{индекс}\"), namingIndex->text().trimmed());\n"
    "            name.replace(QStringLiteral(\"{index}\"), namingIndex->text().trimmed());\n"
    "            name.replace(QStringLiteral(\"{лист}\"), sheet);\n"
    "            name.replace(QStringLiteral(\"{номер}\"), sheet);\n"
    "            name.replace(QStringLiteral(\"{sheet}\"), sheet);\n"
    "            name.replace(QStringLiteral(\"{сторона}\"), side);\n"
    "            name.replace(QStringLiteral(\"{side}\"), side);\n"
    "            return name;\n"
    "        };\n"
    "        namingPreview->setText(tr(\"First pair: %1 / %2\").arg(\n"
    "            render(namingFront->text()), render(namingBack->text())\n"
    "        ));\n"
    "        namingBox->setToolTip(tr(\"Pages are named in natural order: front, back, next sheet.\"));\n"
    "    };\n"
    "\n"
    "    connect(namingEnabled, &QCheckBox::toggled, this, [=](bool) { saveNaming(); updateNamingPreview(); });\n"
    "    connect(namingIndex, &QLineEdit::textChanged, this, [=](QString const&) { saveNaming(); updateNamingPreview(); });\n"
    "    connect(namingTemplate, &QLineEdit::textChanged, this, [=](QString const&) { saveNaming(); updateNamingPreview(); });\n"
    "    connect(namingStart, QOverload<int>::of(&QSpinBox::valueChanged), this, [=](int) { saveNaming(); updateNamingPreview(); });\n"
    "    connect(namingWidth, QOverload<int>::of(&QSpinBox::valueChanged), this, [=](int) { saveNaming(); updateNamingPreview(); });\n"
    "    connect(namingFront, &QLineEdit::textChanged, this, [=](QString const&) { saveNaming(); updateNamingPreview(); });\n"
    "    connect(namingBack, &QLineEdit::textChanged, this, [=](QString const&) { saveNaming(); updateNamingPreview(); });\n"
    "    updateNamingPreview();\n"
    "\n"
    "    setDespeckleLevel(DESPECKLE_NORMAL);\n",
    "output OptionsWidget archive naming controls",
)
OUT_OPTIONS_CPP.write_text(out_options_cpp, encoding="utf-8")


# ---- MainWindow.cpp -------------------------------------------------------
cpp = CPP.read_text(encoding="utf-8")

cpp = replace_once(
    cpp,
    "#include <QApplication>\n",
    "#include <QApplication>\n#include <QAction>\n#include <QLineEdit>\n#include <QLabel>\n#include <QTimer>\n",
    "MainWindow.cpp route/search includes",
)

cpp = replace_once(
    cpp,
    "    setupUi(this);\n"
    "    setupStatusBar();\n",
    "    setupUi(this);\n"
    "    setupStatusBar();\n"
    "\n"
    "    // LimbusTailor: quick jump by page number for large projects.\n"
    "    // Leading zeroes are accepted: 045 means page 45.\n"
    "    QLabel* const quick_page_label = new QLabel(tr(\"Page:\"), this);\n"
    "    QLineEdit* const quick_page_edit = new QLineEdit(this);\n"
    "    quick_page_edit->setFixedWidth(92);\n"
    "    quick_page_edit->setPlaceholderText(tr(\"045\"));\n"
    "    quick_page_edit->setToolTip(tr(\"Quick jump to page number\"));\n"
    "    quick_page_edit->setClearButtonEnabled(true);\n"
    "    statusBar()->addPermanentWidget(quick_page_label);\n"
    "    statusBar()->addPermanentWidget(quick_page_edit);\n"
    "\n"
    "    QTimer* const quick_page_timer = new QTimer(quick_page_edit);\n"
    "    quick_page_timer->setSingleShot(true);\n"
    "    connect(quick_page_edit, &QLineEdit::textEdited, this,\n"
    "            [quick_page_timer](QString const&) { quick_page_timer->start(220); });\n"
    "    connect(quick_page_edit, &QLineEdit::returnPressed, this,\n"
    "            [quick_page_timer]() { quick_page_timer->start(0); });\n"
    "    connect(quick_page_timer, &QTimer::timeout, this, [this, quick_page_edit]() {\n"
    "        if (!isProjectLoaded()) {\n"
    "            return;\n"
    "        }\n"
    "        bool ok = false;\n"
    "        int const page_no = quick_page_edit->text().trimmed().toInt(&ok);\n"
    "        if (!ok || page_no < 1) {\n"
    "            return;\n"
    "        }\n"
    "        PageSequence const pages(m_ptrPages->toPageSequence(getCurrentView()));\n"
    "        if (page_no <= static_cast<int>(pages.numPages())) {\n"
    "            goToPage(pages.pageAt(page_no - 1).id());\n"
    "        } else {\n"
    "            QApplication::beep();\n"
    "        }\n"
    "    });\n",
    "MainWindow quick page jump",
)

cpp = replace_once(
    cpp,
    "        m_ptrInteractiveQueue(new ProcessingTaskQueue(ProcessingTaskQueue::RANDOM_ORDER)),\n"
    "        m_curFilter(0),\n"
    "        m_ignoreSelectionChanges(0),\n"
    "        m_ignorePageOrderingChanges(0),\n"
    "        m_debug(false),\n",
    "        m_ptrInteractiveQueue(new ProcessingTaskQueue(ProcessingTaskQueue::RANDOM_ORDER)),\n"
    "        m_curFilter(0),\n"
    "        m_routeConfigAction(nullptr),\n"
    "        m_runThroughAction(nullptr),\n"
    "        m_routeConfigPreviousFilter(0),\n"
    "        m_ignoreSelectionChanges(0),\n"
    "        m_ignorePageOrderingChanges(0),\n"
    "        m_routeConfigMode(false),\n"
    "        m_throughProcessing(false),\n"
    "        m_debug(false),\n",
    "MainWindow.cpp constructor init",
)

cpp = replace_once(
    cpp,
    "    connect(actionFixDpi, SIGNAL(triggered(bool)), SLOT(fixDpiDialogRequested()));\n"
    "    connect(actionRelinking, SIGNAL(triggered(bool)), SLOT(showRelinkingDialog()));\n"
    "    connect(actionSettings, SIGNAL(triggered(bool)), SLOT(openSettingsDialog()));\n",
    "    connect(actionFixDpi, SIGNAL(triggered(bool)), SLOT(fixDpiDialogRequested()));\n"
    "    connect(actionRelinking, SIGNAL(triggered(bool)), SLOT(showRelinkingDialog()));\n"
    "    connect(actionSettings, SIGNAL(triggered(bool)), SLOT(openSettingsDialog()));\n"
    "\n"
    "    // LimbusTailor: optional end-to-end route.  Route setup deliberately\n"
    "    // exposes stage option widgets without running prerequisite filters.\n"
    "    // The normal ScanTailor interaction remains unchanged when it is off.\n"
    "    m_routeConfigAction = new QAction(tr(\"End-to-end route setup\"), this);\n"
    "    m_routeConfigAction->setCheckable(true);\n"
    "    m_routeConfigAction->setStatusTip(\n"
    "        tr(\"Allows configuring every stage without running prerequisite processing.\")\n"
    "    );\n"
    "    m_runThroughAction = new QAction(tr(\"Run end-to-end processing\"), this);\n"
    "    m_runThroughAction->setStatusTip(\n"
    "        tr(\"Process every page through all stages and write output.\")\n"
    "    );\n"
    "    menuDebug->insertAction(actionSettings, m_routeConfigAction);\n"
    "    menuDebug->insertAction(actionSettings, m_runThroughAction);\n"
    "    menuDebug->insertSeparator(actionSettings);\n"
    "    connect(m_routeConfigAction, &QAction::toggled,\n"
    "            this, &MainWindow::setRouteConfigurationMode);\n"
    "    connect(m_runThroughAction, &QAction::triggered,\n"
    "            this, &MainWindow::startThroughProcessing);\n",
    "MainWindow.cpp route actions",
)

cpp = replace_once(
    cpp,
    "    bool const was_below_fix_orientation = isBelowFixOrientation(m_curFilter);\n"
    "    bool const was_below_select_content = isBelowSelectContent(m_curFilter);\n"
    "    m_curFilter = selected.front().top();\n"
    "    bool const now_below_fix_orientation = isBelowFixOrientation(m_curFilter);\n"
    "    bool const now_below_select_content = isBelowSelectContent(m_curFilter);\n",
    "    bool const was_below_fix_orientation = isBelowFixOrientation(m_curFilter);\n"
    "    bool const was_below_select_content = isBelowSelectContent(m_curFilter);\n"
    "    m_curFilter = selected.front().top();\n"
    "\n"
    "    if (m_routeConfigMode) {\n"
    "        // Parameter-only navigation: do not call updateMainArea(), because\n"
    "        // Output normally refuses to open until Page Layout is ready.\n"
    "        m_ptrStages->filterAt(m_curFilter)->selected();\n"
    "        updateSortOptions();\n"
    "        focusButton->setChecked(true);\n"
    "        resetThumbSequence(currentPageOrderProvider(), ThumbnailSequence::KEEP_SELECTION);\n"
    "\n"
    "        PageInfo const page(m_ptrThumbSequence->selectionLeader());\n"
    "        if (!page.isNull()) {\n"
    "            m_ptrStages->filterAt(m_curFilter)->preUpdateUI(this, page.id());\n"
    "        }\n"
    "        StatusBarProvider::changeFilterIdx(m_curFilter);\n"
    "        if (QStatusBar* sb = statusBar()) {\n"
    "            sb->showMessage(tr(\"Route setup mode: stage settings are editable without processing; uniform page sizing is disabled for the through route.\"));\n"
    "        }\n"
    "        return;\n"
    "    }\n"
    "\n"
    "    bool const now_below_fix_orientation = isBelowFixOrientation(m_curFilter);\n"
    "    bool const now_below_select_content = isBelowSelectContent(m_curFilter);\n",
    "MainWindow.cpp route selection bypass",
)

cpp = replace_once(
    cpp,
    "void\n"
    "MainWindow::reloadRequested()\n"
    "{\n"
    "    // Start loading / processing the current page.\n"
    "    updateMainArea();\n"
    "}\n"
    "\n"
    "void\n"
    "MainWindow::startBatchProcessing()\n",
    "void\n"
    "MainWindow::reloadRequested()\n"
    "{\n"
    "    if (m_routeConfigMode) {\n"
    "        // Widgets still emit reloadRequested() when a parameter changes.\n"
    "        // In route setup mode that must never start image processing.\n"
    "        PageInfo const page(m_ptrThumbSequence->selectionLeader());\n"
    "        if (!page.isNull()) {\n"
    "            m_ptrStages->filterAt(m_curFilter)->preUpdateUI(this, page.id());\n"
    "        }\n"
    "        return;\n"
    "    }\n"
    "\n"
    "    // Start loading / processing the current page.\n"
    "    updateMainArea();\n"
    "}\n"
    "\n"
    "void\n"
    "MainWindow::prepareArchiveOutputNames(PageSequence const& pages)\n"
    "{\n"
    "    m_outFileNameGen.clearArchiveFileNames();\n"
    "\n"
    "    QSettings settings;\n"
    "    if (!settings.value(\"limbustailor/archive_naming/enabled\", false).toBool()) {\n"
    "        return;\n"
    "    }\n"
    "\n"
    "    const QString index = settings.value(\n"
    "        \"limbustailor/archive_naming/index\", QString()\n"
    "    ).toString().trimmed();\n"
    "    const QString naming_template = settings.value(\n"
    "        \"limbustailor/archive_naming/template\", QStringLiteral(\"{индекс}_{лист}{сторона}\")\n"
    "    ).toString();\n"
    "    const int start = qMax(0, settings.value(\n"
    "        \"limbustailor/archive_naming/start\", 1\n"
    "    ).toInt());\n"
    "    const int width = qBound(1, settings.value(\n"
    "        \"limbustailor/archive_naming/width\", 3\n"
    "    ).toInt(), 12);\n"
    "    const QString front = settings.value(\n"
    "        \"limbustailor/archive_naming/front\", QStringLiteral(\"_0\")\n"
    "    ).toString();\n"
    "    const QString back = settings.value(\n"
    "        \"limbustailor/archive_naming/back\", QStringLiteral(\"_1\")\n"
    "    ).toString();\n"
    "\n"
    "    int logical_index = 0;\n"
    "    for (PageInfo const& page : pages) {\n"
    "        const int sheet_no = start + logical_index / 2;\n"
    "        const QString sheet = QStringLiteral(\"%1\").arg(\n"
    "            sheet_no, width, 10, QLatin1Char('0')\n"
    "        );\n"
    "        const QString side = (logical_index % 2 == 0) ? front : back;\n"
    "        QString base(naming_template);\n"
    "        base.replace(QStringLiteral(\"{индекс}\"), index);\n"
    "        base.replace(QStringLiteral(\"{index}\"), index);\n"
    "        base.replace(QStringLiteral(\"{лист}\"), sheet);\n"
    "        base.replace(QStringLiteral(\"{номер}\"), sheet);\n"
    "        base.replace(QStringLiteral(\"{sheet}\"), sheet);\n"
    "        base.replace(QStringLiteral(\"{сторона}\"), side);\n"
    "        base.replace(QStringLiteral(\"{side}\"), side);\n"
    "\n"
    "        const QString invalid = QStringLiteral(\"\\\\/:*?\\\\"<>|\");\n"
    "        for (QChar const ch : invalid) {\n"
    "            base.replace(ch, QLatin1Char('_'));\n"
    "        }\n"
    "        while (base.endsWith(QLatin1Char(' ')) || base.endsWith(QLatin1Char('.'))) {\n"
    "            base.chop(1);\n"
    "        }\n"
    "        if (!base.isEmpty()) {\n"
    "            m_outFileNameGen.setArchiveFileName(page.id(), base);\n"
    "        }\n"
    "        ++logical_index;\n"
    "    }\n"
    "}\n"
    "\n"
    "void\n"
    "MainWindow::setRouteConfigurationMode(bool const enabled)\n"
    "{\n"
    "    if (enabled == m_routeConfigMode) {\n"
    "        return;\n"
    "    }\n"
    "\n"
    "    if (enabled) {\n"
    "        if (!isProjectLoaded() || isBatchProcessingInProgress()) {\n"
    "            if (m_routeConfigAction) {\n"
    "                const bool blocked = m_routeConfigAction->blockSignals(true);\n"
    "                m_routeConfigAction->setChecked(false);\n"
    "                m_routeConfigAction->blockSignals(blocked);\n"
    "            }\n"
    "            return;\n"
    "        }\n"
    "\n"
    "        m_routeConfigPreviousFilter = m_curFilter;\n"
    "        m_routeConfigMode = true;\n"
    "        PageInfo const page(m_ptrThumbSequence->selectionLeader());\n"
    "        if (!page.isNull()) {\n"
    "            m_ptrStages->filterAt(m_curFilter)->preUpdateUI(this, page.id());\n"
    "        }\n"
    "        if (QStatusBar* sb = statusBar()) {\n"
    "            sb->showMessage(tr(\"Route setup mode: stage settings are editable without processing.\"));\n"
    "        }\n"
    "        return;\n"
    "    }\n"
    "\n"
    "    m_routeConfigMode = false;\n"
    "    if (QStatusBar* sb = statusBar()) {\n"
    "        sb->clearMessage();\n"
    "    }\n"
    "\n"
    "    if (!isProjectLoaded()) {\n"
    "        return;\n"
    "    }\n"
    "\n"
    "    const int restore_idx = qBound(0, m_routeConfigPreviousFilter, m_ptrStages->count() - 1);\n"
    "    {\n"
    "        ScopedIncDec<int> guard(m_ignoreSelectionChanges);\n"
    "        m_curFilter = restore_idx;\n"
    "        filterList->selectRow(restore_idx);\n"
    "    }\n"
    "    m_ptrStages->filterAt(m_curFilter)->selected();\n"
    "    updateSortOptions();\n"
    "    focusButton->setChecked(true);\n"
    "    resetThumbSequence(currentPageOrderProvider(), ThumbnailSequence::KEEP_SELECTION);\n"
    "    updateMainArea();\n"
    "}\n"
    "\n"
    "void\n"
    "MainWindow::startThroughProcessing()\n"
    "{\n"
    "    if (isBatchProcessingInProgress() || !isProjectLoaded()) {\n"
    "        return;\n"
    "    }\n"
    "\n"
    "    m_ptrInteractiveQueue->cancelAndClear();\n"
    "\n"
    "    // Leave parameter-only mode without restoring / processing the old stage.\n"
    "    if (m_routeConfigMode) {\n"
    "        m_routeConfigMode = false;\n"
    "        if (m_routeConfigAction) {\n"
    "            const bool blocked = m_routeConfigAction->blockSignals(true);\n"
    "            m_routeConfigAction->setChecked(false);\n"
    "            m_routeConfigAction->blockSignals(blocked);\n"
    "        }\n"
    "    }\n"
    "\n"
    "    QSettings settings;\n"
    "    bool show_dlg = !settings.value(\n"
    "        _key_batch_dialog_remember_choice, _key_batch_dialog_remember_choice_def\n"
    "    ).toBool();\n"
    "    bool process_all = !settings.value(\n"
    "        _key_batch_dialog_start_from_current, _key_batch_dialog_start_from_current_def\n"
    "    ).toBool();\n"
    "\n"
    "    if (show_dlg) {\n"
    "        StartBatchProcessingDialog dialog(this, process_all);\n"
    "        dialog.show();\n"
    "        if (!dialog.exec()) {\n"
    "            return;\n"
    "        }\n"
    "        process_all = dialog.isAllPagesChecked();\n"
    "        settings.setValue(_key_batch_dialog_remember_choice, dialog.isRememberChoiceChecked());\n"
    "        settings.setValue(_key_batch_dialog_start_from_current, !process_all);\n"
    "    }\n"
    "\n"
    "    const int output_idx = m_ptrStages->outputFilterIdx();\n"
    "    PageId const selected_id(m_ptrThumbSequence->selectionLeader().id());\n"
    "\n"
    "    // Build a natural PAGE_VIEW queue.  Each task is a composite ending at\n"
    "    // Output, so Split Pages -> Deskew -> Select Content -> Page Layout ->\n"
    "    // Output happens without returning control to the operator.\n"
    "    m_ptrBatchQueue.reset(new ProcessingTaskQueue(ProcessingTaskQueue::SEQUENTIAL_ORDER));\n"
    "    PageSequence const route_pages(m_ptrPages->toPageSequence(PAGE_VIEW));\n"
    "    prepareArchiveOutputNames(route_pages);\n"
    "    bool started = process_all || selected_id.isNull();\n"
    "    int queued = 0;\n"
    "    for (PageInfo const& page : route_pages) {\n"
    "        if (!started && (page.id() == selected_id || page.imageId() == selected_id.imageId())) {\n"
    "            started = true;\n"
    "        }\n"
    "        if (!started) {\n"
    "            continue;\n"
    "        }\n"
    "        m_ptrBatchQueue->addProcessingTask(\n"
    "            page, createCompositeTask(page, output_idx, /*batch=*/true, m_debug)\n"
    "        );\n"
    "        ++queued;\n"
    "    }\n"
    "\n"
    "    m_ptrBatchQueue->startProgressTracking(queued);\n"
    "    m_throughProcessing = true;\n"
    "\n"
    "    // Move the GUI to Output only after the queue exists.  updateMainArea()\n"
    "    // will then show the batch screen and won't hit checkReadyForOutput().\n"
    "    {\n"
    "        ScopedIncDec<int> guard(m_ignoreSelectionChanges);\n"
    "        m_curFilter = output_idx;\n"
    "        filterList->selectRow(output_idx);\n"
    "    }\n"
    "    m_ptrStages->filterAt(m_curFilter)->selected();\n"
    "    updateSortOptions();\n"
    "    focusButton->setChecked(true);\n"
    "    resetThumbSequence(currentPageOrderProvider(), ThumbnailSequence::KEEP_SELECTION);\n"
    "\n"
    "    removeFilterOptionsWidget();\n"
    "    filterList->setBatchProcessingInProgress(true);\n"
    "    filterList->setEnabled(false);\n"
    "\n"
    "    BackgroundTaskPtr const task(m_ptrBatchQueue->takeForProcessing());\n"
    "    if (task) {\n"
    "        m_ptrWorkerThread->performTask(task);\n"
    "    } else {\n"
    "        stopBatchProcessing();\n"
    "        return;\n"
    "    }\n"
    "\n"
    "    PageInfo const selected_page(m_ptrBatchQueue->selectedPage());\n"
    "    if (!selected_page.isNull()) {\n"
    "        m_ptrThumbSequence->setSelection(selected_page.id());\n"
    "    }\n"
    "\n"
    "    if (QStatusBar* sb = statusBar()) {\n"
    "        sb->showMessage(tr(\"End-to-end processing: Split Pages -> Deskew -> Select Content -> Page Layout -> Output\"));\n"
    "    }\n"
    "    updateMainArea();\n"
    "}\n"
    "\n"
    "void\n"
    "MainWindow::startBatchProcessing()\n",
    "MainWindow.cpp route methods",
)

cpp = replace_once(
    cpp,
    "    m_ptrStages->filterAt(m_curFilter)->updateStatistics();\n"
    "    resetThumbSequence(currentPageOrderProvider());\n"
    "}\n"
    "\n"
    "void\n"
    "MainWindow::filterResult",
    "    if (m_throughProcessing) {\n"
    "        for (int idx = 0; idx < m_ptrStages->count(); ++idx) {\n"
    "            m_ptrStages->filterAt(idx)->updateStatistics();\n"
    "        }\n"
    "    } else {\n"
    "        m_ptrStages->filterAt(m_curFilter)->updateStatistics();\n"
    "    }\n"
    "    m_throughProcessing = false;\n"
    "    if (QStatusBar* sb = statusBar()) {\n"
    "        sb->clearMessage();\n"
    "    }\n"
    "    resetThumbSequence(currentPageOrderProvider());\n"
    "}\n"
    "\n"
    "void\n"
    "MainWindow::filterResult",
    "MainWindow.cpp stop through statistics",
)


# ---- Wire route mode into MainWindow --------------------------------------
# The route-specific Page Layout behavior above is opt-in.  These switches
# connect the MainWindow lifecycle to the filter without touching normal mode.

cpp = replace_once(
    cpp,
    "        m_routeConfigPreviousFilter = m_curFilter;\n"
    "        m_routeConfigMode = true;\n"
    "        PageInfo const page(m_ptrThumbSequence->selectionLeader());\n",
    "        m_routeConfigPreviousFilter = m_curFilter;\n"
    "        m_routeConfigMode = true;\n"
    "        m_ptrStages->pageLayoutFilter()->setRouteSetupMode(true);\n"
    "        PageInfo const page(m_ptrThumbSequence->selectionLeader());\n",
    "MainWindow enable Page Layout route setup",
)

cpp = replace_once(
    cpp,
    "    m_routeConfigMode = false;\n"
    "    if (QStatusBar* sb = statusBar()) {\n",
    "    m_routeConfigMode = false;\n"
    "    m_ptrStages->pageLayoutFilter()->setRouteSetupMode(false);\n"
    "    if (QStatusBar* sb = statusBar()) {\n",
    "MainWindow disable Page Layout route setup",
)

cpp = replace_once(
    cpp,
    "    if (m_routeConfigMode) {\n"
    "        m_routeConfigMode = false;\n"
    "        if (m_routeConfigAction) {\n",
    "    if (m_routeConfigMode) {\n"
    "        m_routeConfigMode = false;\n"
    "        m_ptrStages->pageLayoutFilter()->setRouteSetupMode(false);\n"
    "        if (m_routeConfigAction) {\n",
    "MainWindow leave route setup before through processing",
)

cpp = replace_once(
    cpp,
    "    const int output_idx = m_ptrStages->outputFilterIdx();\n"
    "    PageId const selected_id(m_ptrThumbSequence->selectionLeader().id());\n",
    "    const int output_idx = m_ptrStages->outputFilterIdx();\n"
    "    PageId const selected_id(m_ptrThumbSequence->selectionLeader().id());\n"
    "\n"
    "    // End-to-end route: preserve each page's own content size + hard\n"
    "    // margins.  Do not add soft margins to normalize to the largest page.\n"
    "    m_ptrStages->pageLayoutFilter()->setAggregateAlignmentDisabled(true);\n",
    "MainWindow disable aggregate alignment for through processing",
)

cpp = replace_once(
    cpp,
    "    PageInfo start_page = processAll ? m_ptrThumbSequence->firstPage() : m_ptrThumbSequence->selectionLeader();\n",
    "    if (m_curFilter == m_ptrStages->outputFilterIdx()) {\n"
    "        prepareArchiveOutputNames(m_ptrPages->toPageSequence(PAGE_VIEW));\n"
    "    }\n"
    "\n"
    "    PageInfo start_page = processAll ? m_ptrThumbSequence->firstPage() : m_ptrThumbSequence->selectionLeader();\n",
    "MainWindow prepare archive names for normal Output batch",
)

cpp = replace_once(
    cpp,
    "    if (m_throughProcessing) {\n"
    "        for (int idx = 0; idx < m_ptrStages->count(); ++idx) {\n",
    "    if (m_throughProcessing) {\n"
    "        m_ptrStages->pageLayoutFilter()->setAggregateAlignmentDisabled(false);\n"
    "        for (int idx = 0; idx < m_ptrStages->count(); ++idx) {\n",
    "MainWindow restore aggregate alignment after through processing",
)

CPP.write_text(cpp, encoding="utf-8")

# ---- Russian translation --------------------------------------------------
ru = RU.read_text(encoding="utf-8")
marker = """    <message>
        <location filename="../app/MainWindow.cpp" line="589"/>
        <source>Stop batch processing</source>
        <translation>Остановить пакетную обработку</translation>
    </message>
</context>"""

replacement = """    <message>
        <location filename="../app/MainWindow.cpp" line="589"/>
        <source>Stop batch processing</source>
        <translation>Остановить пакетную обработку</translation>
    </message>
    <message>
        <source>Page:</source>
        <translation>Страница:</translation>
    </message>
    <message>
        <source>Quick jump to page number</source>
        <translation>Быстрый переход к номеру страницы</translation>
    </message>
    <message>
        <source>End-to-end route setup</source>
        <translation>Настройка сквозного маршрута</translation>
    </message>
    <message>
        <source>Allows configuring every stage without running prerequisite processing.</source>
        <translation>Позволяет настроить любой этап без запуска предыдущих этапов.</translation>
    </message>
    <message>
        <source>Run end-to-end processing</source>
        <translation>Запустить сквозную обработку</translation>
    </message>
    <message>
        <source>Process every page through all stages and write output.</source>
        <translation>Прогнать все страницы через весь маршрут и сохранить результат.</translation>
    </message>
    <message>
        <source>Route setup mode: stage settings are editable without processing.</source>
        <translation>Настройка маршрута: параметры этапов доступны без обработки; выравнивание всех страниц под единый размер отключено.</translation>
    </message>
    <message>
        <source>End-to-end processing: Split Pages -&gt; Deskew -&gt; Select Content -&gt; Page Layout -&gt; Output</source>
        <translation>Сквозная обработка: Разрезка → Наклон → Область контента → Поля → Вывод</translation>
    </message>
</context>"""

ru = replace_once(ru, marker, replacement, "Russian MainWindow translations")
ru = replace_once(
    ru,
    "    <name>output::OptionsWidget</name>\n",
    "    <name>output::OptionsWidget</name>\n"
    "    <message><source>Archive file naming</source><translation>Архивное именование файлов</translation></message>\n"
    "    <message><source>Use archive names</source><translation>Использовать архивные имена</translation></message>\n"
    "    <message><source>Case index:</source><translation>Индекс дела:</translation></message>\n"
    "    <message><source>Template:</source><translation>Шаблон:</translation></message>\n"
    "    <message><source>Start sheet:</source><translation>Начать с листа:</translation></message>\n"
    "    <message><source>Digits:</source><translation>Знаков в номере:</translation></message>\n"
    "    <message><source>Front suffix:</source><translation>Лицевая сторона:</translation></message>\n"
    "    <message><source>Back suffix:</source><translation>Оборотная сторона:</translation></message>\n"
    "    <message><source>First pair: %1 / %2</source><translation>Первая пара: %1 / %2</translation></message>\n"
    "    <message><source>Pages are named in natural order: front, back, next sheet.</source><translation>Имена идут по естественному порядку: лицо, оборот, следующий лист.</translation></message>\n",
    "Russian archive naming translations",
)

RU.write_text(ru, encoding="utf-8")
