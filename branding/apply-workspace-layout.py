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


def optional_direct_property(item, name):
    for prop in item.findall("property"):
        if prop.get("name") == name:
            return prop
    return None


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


def direct_layout(item):
    for child in item:
        if child.tag == "layout":
            return child
    raise RuntimeError(f"Direct layout not found on {item.get('name')}")


def set_number_property(layout, name, value):
    prop = optional_direct_property(layout, name)
    if prop is None:
        prop = ET.Element("property", {"name": name})
        number = ET.SubElement(prop, "number")
        number.text = str(value)
        first_item = next(
            (idx for idx, child in enumerate(layout) if child.tag == "item"),
            len(layout),
        )
        layout.insert(first_item, prop)
        return

    number = prop.find("number")
    if number is None:
        raise RuntimeError(f"Layout property {name} is not numeric")
    number.text = str(value)


def make_direct_spacers_horizontal(layout):
    for item in layout.findall("item"):
        spacer = item.find("spacer")
        if spacer is None:
            continue

        orientation = optional_direct_property(spacer, "orientation")
        if orientation is not None:
            enum = orientation.find("enum")
            if enum is not None and enum.text == "Qt::Vertical":
                enum.text = "Qt::Horizontal"

        size_hint = optional_direct_property(spacer, "sizeHint")
        if size_hint is not None:
            size = size_hint.find("size")
            if size is not None:
                width = size.find("width")
                height = size.find("height")
                if width is not None:
                    width.text = "24"
                if height is not None:
                    height.text = "20"


def compact_group(root, group_name):
    group = root.find(f".//widget[@name='{group_name}']")
    if group is None:
        return
    layout = direct_layout(group)
    set_number_property(layout, "spacing", 4)
    for prop_name in ("leftMargin", "topMargin", "rightMargin", "bottomMargin"):
        set_number_property(layout, prop_name, 5)


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
set_size_property(filters_dock, "minimumSize", 0, 225)

# Stage selector and current-stage settings remain side-by-side in the bottom dock.
filters_layout = filters_dock.find(".//layout[@name='verticalLayout_3']")
if filters_layout is None:
    raise RuntimeError("Filter dock layout not found")
filters_layout.set("class", "QHBoxLayout")

filter_list = widget(root, "filterList")
set_size_property(filter_list, "minimumSize", 185, 0)
set_size_property(filter_list, "maximumSize", 235, 16777215)

scroll_area = widget(root, "scrollArea")
vertical_policy = direct_property(scroll_area, "verticalScrollBarPolicy").find("enum")
horizontal_policy = direct_property(scroll_area, "horizontalScrollBarPolicy").find("enum")
if vertical_policy is None or horizontal_policy is None:
    raise RuntimeError("Filter scroll area policies are missing")
vertical_policy.text = "Qt::ScrollBarAsNeeded"
horizontal_policy.text = "Qt::ScrollBarAsNeeded"

ET.indent(tree, space=" ", level=0)
tree.write(UI_FILE, encoding="UTF-8", xml_declaration=True)


# Upstream ScanTailor option widgets are tall narrow columns because they lived
# on the right side. In LimbusTailor they live in a wide bottom strip, so the
# logical cards of each stage must run left-to-right.
option_ui_files = (
    "src/core/filters/fix_orientation/ui/OrientationOptionsWidget.ui",
    "src/core/filters/page_split/ui/PageSplitOptionsWidget.ui",
    "src/core/filters/deskew/ui/DeskewOptionsWidget.ui",
    "src/core/filters/select_content/ui/SelectContentOptionsWidget.ui",
    "src/core/filters/page_layout/ui/PageLayoutOptionsWidget.ui",
)

for rel_path in option_ui_files:
    path = ROOT / rel_path
    if not path.exists():
        raise RuntimeError(f"Options UI not found: {rel_path}")

    option_tree = ET.parse(path)
    option_root = option_tree.getroot()
    form = option_root.find("widget")
    if form is None:
        raise RuntimeError(f"Root widget missing in {rel_path}")

    layout = direct_layout(form)
    if layout.get("class") != "QVBoxLayout":
        raise RuntimeError(
            f"Expected vertical root layout in {rel_path}, got {layout.get('class')}"
        )

    layout.set("class", "QHBoxLayout")
    set_number_property(layout, "spacing", 10)
    for prop_name in ("leftMargin", "topMargin", "rightMargin", "bottomMargin"):
        set_number_property(layout, prop_name, 6)
    make_direct_spacers_horizontal(layout)

    # These are the two busiest stages in archive work. Reduce dead padding so
    # their buttons stay visible without turning the bottom strip into a wall.
    if rel_path.endswith("PageLayoutOptionsWidget.ui"):
        compact_group(option_root, "marginsGroup")
        compact_group(option_root, "alignmentGroup")
    elif rel_path.endswith("SelectContentOptionsWidget.ui"):
        compact_group(option_root, "gbPageBox")
        compact_group(option_root, "groupBox")
        compact_group(option_root, "scopeBox")

    ET.indent(option_tree, space=" ", level=0)
    option_tree.write(path, encoding="UTF-8", xml_declaration=True)


# Qt restores the previous QMainWindow dock state from QSettings. Apply this
# revision once so existing LimbusTailor users receive the wider bottom strip,
# then preserve any manual dock changes afterwards.
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
    if (limbusUiLayoutVersion < 2) {
        addDockWidget(Qt::LeftDockWidgetArea, dockWidgetThumbnails);
        addDockWidget(Qt::BottomDockWidgetArea, dockWidget_4);
        resizeDocks(QList<QDockWidget*>() << dockWidgetThumbnails,
                    QList<int>() << 280, Qt::Horizontal);
        resizeDocks(QList<QDockWidget*>() << dockWidget_4,
                    QList<int>() << 255, Qt::Vertical);
        settings.setValue(QStringLiteral(\"limbustailor/ui_layout_version\"), 2);
    }

    scrollArea->horizontalScrollBar()->setDisabled(false);
"""
count = main_cpp.count(old)
if count != 1:
    raise RuntimeError(f"MainWindow state restore marker expected once, got {count}")
MAIN_CPP.write_text(main_cpp.replace(old, new, 1), encoding="utf-8")

print("Applied LimbusTailor workspace layout v2: horizontal bottom option cards")
