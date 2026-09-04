from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path.cwd()
UI_FILE = ROOT / "src/app/ui/MainWindow.ui"
MAIN_CPP = ROOT / "src/app/MainWindow.cpp"


def widget(root, name):
    item = root.find(f".//widget[@name='{name}']")
    if item is None:
        raise RuntimeError(f"MainWindow UI widget not found: {name}")
    return item


def direct_property(item, name):
    for prop in item.findall("property"):
        if prop.get("name") == name:
            return prop
    raise RuntimeError(f"Property {name} not found on {item.get('name')}")


def set_size_property(item, name, width, height):
    prop = direct_property(item, name)
    size = prop.find("size")
    if size is None:
        raise RuntimeError(f"Size property {name} is malformed on {item.get('name')}")
    w = size.find("width")
    h = size.find("height")
    if w is None or h is None:
        raise RuntimeError(f"Size property {name} has no width/height on {item.get('name')}")
    w.text = str(width)
    h.text = str(height)


# Recompose the original ScanTailor three-pane workspace for LimbusTailor:
# a wide page rail on the left, the image in the centre and controls below.
tree = ET.parse(UI_FILE)
root = tree.getroot()

thumb_dock = widget(root, "dockWidgetThumbnails")
thumb_allowed = direct_property(thumb_dock, "allowedAreas").find("set")
thumb_area = thumb_dock.find("attribute[@name='dockWidgetArea']/number")
if thumb_allowed is None or thumb_area is None:
    raise RuntimeError("Thumbnail dock placement metadata is missing")
thumb_allowed.text = "Qt::LeftDockWidgetArea"
thumb_area.text = "1"  # Qt::LeftDockWidgetArea

thumb_view = widget(root, "thumbView")
set_size_property(thumb_view, "minimumSize", 260, 0)

filters_dock = widget(root, "dockWidget_4")
filters_allowed = direct_property(filters_dock, "allowedAreas").find("set")
filters_area = filters_dock.find("attribute[@name='dockWidgetArea']/number")
if filters_allowed is None or filters_area is None:
    raise RuntimeError("Filter dock placement metadata is missing")
filters_allowed.text = "Qt::BottomDockWidgetArea"
filters_area.text = "8"  # Qt::BottomDockWidgetArea
set_size_property(filters_dock, "minimumSize", 0, 205)

# In a bottom dock the stage selector and the current stage settings belong
# side-by-side. This keeps the centre image tall while giving controls a full
# horizontal strip.
filters_layout = filters_dock.find(".//layout[@name='verticalLayout_3']")
if filters_layout is None:
    raise RuntimeError("Filter dock layout not found")
filters_layout.set("class", "QHBoxLayout")

filter_list = widget(root, "filterList")
set_size_property(filter_list, "minimumSize", 185, 0)
set_size_property(filter_list, "maximumSize", 235, 16777215)

scroll_area = widget(root, "scrollArea")
vertical_policy = direct_property(scroll_area, "verticalScrollBarPolicy").find("enum")
if vertical_policy is None:
    raise RuntimeError("Filter scroll area vertical policy is missing")
vertical_policy.text = "Qt::ScrollBarAsNeeded"

ET.indent(tree, space=" ", level=0)
tree.write(UI_FILE, encoding="UTF-8", xml_declaration=True)


# Qt restores the previous QMainWindow dock state from QSettings. Apply this
# new workspace once per layout version so existing LimbusTailor users see the
# redesign, then preserve any manual dock changes they make afterwards.
main_cpp = MAIN_CPP.read_text(encoding="utf-8")
old = """    QByteArray arr = settings.value(_key_app_state).toByteArray();
    if (!arr.isEmpty()) {
        restoreState(arr);
    }

    scrollArea->horizontalScrollBar()->setDisabled(true);
"""
new = """    QByteArray arr = settings.value(_key_app_state).toByteArray();
    if (!arr.isEmpty()) {
        restoreState(arr);
    }

    const int limbusUiLayoutVersion = settings.value(
        QStringLiteral(\"limbustailor/ui_layout_version\"), 0
    ).toInt();
    if (limbusUiLayoutVersion < 1) {
        addDockWidget(Qt::LeftDockWidgetArea, dockWidgetThumbnails);
        addDockWidget(Qt::BottomDockWidgetArea, dockWidget_4);
        resizeDocks(QList<QDockWidget*>() << dockWidgetThumbnails,
                    QList<int>() << 280, Qt::Horizontal);
        resizeDocks(QList<QDockWidget*>() << dockWidget_4,
                    QList<int>() << 225, Qt::Vertical);
        settings.setValue(QStringLiteral(\"limbustailor/ui_layout_version\"), 1);
    }

    scrollArea->horizontalScrollBar()->setDisabled(true);
"""
count = main_cpp.count(old)
if count != 1:
    raise RuntimeError(f"MainWindow state restore marker expected once, got {count}")
MAIN_CPP.write_text(main_cpp.replace(old, new, 1), encoding="utf-8")

print("Applied LimbusTailor workspace layout v1: left page rail + bottom controls")
