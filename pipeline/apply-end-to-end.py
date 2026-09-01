from pathlib import Path

ROOT = Path("scantailor-universal")
CPP = ROOT / "src/app/MainWindow.cpp"
HDR = ROOT / "src/app/MainWindow.h"
RU = ROOT / "src/translations/scantailor-universal_ru.ts"

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

# ---- MainWindow.cpp -------------------------------------------------------
cpp = CPP.read_text(encoding="utf-8")

cpp = replace_once(
    cpp,
    "#include <QApplication>\n",
    "#include <QApplication>\n#include <QAction>\n",
    "MainWindow.cpp QAction include",
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
    "            sb->showMessage(tr(\"Route setup mode: stage settings are editable without processing.\"));\n"
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
        <translation>Настройка маршрута: параметры этапов доступны без обработки.</translation>
    </message>
    <message>
        <source>End-to-end processing: Split Pages -&gt; Deskew -&gt; Select Content -&gt; Page Layout -&gt; Output</source>
        <translation>Сквозная обработка: Разрезка → Наклон → Область контента → Поля → Вывод</translation>
    </message>
</context>"""

ru = replace_once(ru, marker, replacement, "Russian MainWindow translations")
RU.write_text(ru, encoding="utf-8")
