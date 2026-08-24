from pathlib import Path
import re

ROOT = Path.cwd()
SRC = Path('/tmp/stu')

def read(rel):
    return (SRC / rel).read_text()

def write(rel, text):
    (SRC / rel).write_text(text)

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'marker not found: {label}')
    return text.replace(old, new, 1)

# --- OutputParams: persist scanner-background QC score. ---
p = 'src/core/filters/output/OutputParams.h'
t = read(p)
t = replace_once(t,
'''                 OutputFileParams const& speckles_file_params,\n                 ZoneSet const& picture_zones, ZoneSet const& fill_zones);''',
'''                 OutputFileParams const& speckles_file_params,\n                 ZoneSet const& picture_zones, ZoneSet const& fill_zones,\n                 double archive_scanner_background_score = 0.0);''', 'OutputParams ctor declaration')
t = replace_once(t,
'''    ZoneSet const& fillZones() const\n    {\n        return m_fillZones;\n    }\nprivate:''',
'''    ZoneSet const& fillZones() const\n    {\n        return m_fillZones;\n    }\n\n    double archiveScannerBackgroundScore() const\n    {\n        return m_archiveScannerBackgroundScore;\n    }\nprivate:''', 'OutputParams accessor')
t = replace_once(t,
'''    ZoneSet m_pictureZones;\n    ZoneSet m_fillZones;''',
'''    ZoneSet m_pictureZones;\n    ZoneSet m_fillZones;\n    double m_archiveScannerBackgroundScore;''', 'OutputParams member')
write(p, t)

p = 'src/core/filters/output/OutputParams.cpp'
t = read(p)
t = replace_once(t,
'''    OutputFileParams const& speckles_file_params,\n    ZoneSet const& picture_zones,\n    ZoneSet const& fill_zones)''',
'''    OutputFileParams const& speckles_file_params,\n    ZoneSet const& picture_zones,\n    ZoneSet const& fill_zones,\n    double archive_scanner_background_score)''', 'OutputParams ctor definition')
t = replace_once(t,
'''        m_specklesFileParams(speckles_file_params),\n        m_pictureZones(picture_zones),\n        m_fillZones(fill_zones)''',
'''        m_specklesFileParams(speckles_file_params),\n        m_pictureZones(picture_zones),\n        m_fillZones(fill_zones),\n        m_archiveScannerBackgroundScore(archive_scanner_background_score)''', 'OutputParams ctor init')
t = replace_once(t,
'''        m_specklesFileParams(el.namedItem("speckles").toElement()),\n        m_pictureZones(el.namedItem("zones").toElement(), PictureZonePropFactory()),\n        m_fillZones(el.namedItem("fill-zones").toElement(), FillZonePropFactory())''',
'''        m_specklesFileParams(el.namedItem("speckles").toElement()),\n        m_pictureZones(el.namedItem("zones").toElement(), PictureZonePropFactory()),\n        m_fillZones(el.namedItem("fill-zones").toElement(), FillZonePropFactory()),\n        m_archiveScannerBackgroundScore(el.attribute("archive-scanner-background-score", "0").toDouble())''', 'OutputParams xml init')
t = replace_once(t,
'''    el.appendChild(m_fillZones.toXml(doc, "fill-zones"));\n    return el;''',
'''    el.appendChild(m_fillZones.toXml(doc, "fill-zones"));\n    el.setAttribute("archive-scanner-background-score", QString::number(m_archiveScannerBackgroundScore, 'f', 6));\n    return el;''', 'OutputParams xml write')
write(p, t)

# --- OutputImageParams: force old outputs to regenerate once for new geometry rules. ---
p = 'src/core/filters/output/OutputImageParams.h'
t = read(p)
t = replace_once(t,
'''    /** ScanTailor Archive Page Layout fill color. */\n    QString m_archiveMarginFill;''',
'''    /** ScanTailor Archive Page Layout fill color. */\n    QString m_archiveMarginFill;\n\n    /** Invalidate cached output when archive geometry rules change. */\n    QString m_archiveGeometryVersion;''', 'OutputImageParams geometry member')
write(p, t)

p = 'src/core/filters/output/OutputImageParams.cpp'
t = read(p)
t = replace_once(t,
'''        m_TiffCompression(TiffCompression),\n        m_archiveMarginFill(archiveMarginFill)''',
'''        m_TiffCompression(TiffCompression),\n        m_archiveMarginFill(archiveMarginFill),\n        m_archiveGeometryVersion(QStringLiteral("binding-polygon-qc-v1"))''', 'OutputImageParams ctor version')
t = replace_once(t,
'''        m_TiffCompression(el.attribute("tiff-compression")),\n        m_archiveMarginFill(el.attribute("archive-margin-fill", "WHITE"))''',
'''        m_TiffCompression(el.attribute("tiff-compression")),\n        m_archiveMarginFill(el.attribute("archive-margin-fill", "WHITE")),\n        m_archiveGeometryVersion(el.attribute("archive-geometry-version"))''', 'OutputImageParams xml version init')
t = replace_once(t,
'''    el.setAttribute("archive-margin-fill", m_archiveMarginFill);''',
'''    el.setAttribute("archive-margin-fill", m_archiveMarginFill);\n    el.setAttribute("archive-geometry-version", m_archiveGeometryVersion);''', 'OutputImageParams xml version write')
t = replace_once(t,
'''    if (m_archiveMarginFill != other.m_archiveMarginFill) {\n        return false;\n    }''',
'''    if (m_archiveMarginFill != other.m_archiveMarginFill) {\n        return false;\n    }\n\n    if (m_archiveGeometryVersion != other.m_archiveGeometryVersion) {\n        return false;\n    }''', 'OutputImageParams version match')
write(p, t)

# --- Output page ordering: scanner background on top. ---
p = 'src/core/filters/output/Filter.cpp'
t = read(p)
t = replace_once(t,
'''#include "OrderBySourceColor.h"\n#include "version.h"''',
'''#include "OrderBySourceColor.h"\n#include "PageOrderProvider.h"\n#include "version.h"''', 'Filter include provider')
marker = '''namespace output\n{\n\nFilter::Filter('''
insert = '''namespace output\n{\n\nnamespace\n{\nclass OrderByScannerBackground : public PageOrderProvider\n{\npublic:\n    explicit OrderByScannerBackground(IntrusivePtr<Settings> const& settings)\n        : m_settings(settings) {}\n\n    bool precedes(PageId const& lhs, bool lhs_incomplete,\n                  PageId const& rhs, bool rhs_incomplete) const override\n    {\n        if (lhs_incomplete != rhs_incomplete) {\n            return !lhs_incomplete;\n        }\n        const double ls = score(lhs);\n        const double rs = score(rhs);\n        if (ls != rs) {\n            return ls > rs;\n        }\n        return lhs < rhs;\n    }\n\n    QString hint(PageId const& page) const override\n    {\n        std::unique_ptr<OutputParams> params(m_settings->getOutputParams(page));\n        if (!params) {\n            return QObject::tr("not processed");\n        }\n        return QObject::tr("scanner background: %1%").arg(\n            params->archiveScannerBackgroundScore(), 0, 'f', 2\n        );\n    }\n\nprivate:\n    double score(PageId const& page) const\n    {\n        std::unique_ptr<OutputParams> params(m_settings->getOutputParams(page));\n        return params ? params->archiveScannerBackgroundScore() : -1.0;\n    }\n\n    IntrusivePtr<Settings> m_settings;\n};\n}\n\nFilter::Filter('''
t = replace_once(t, marker, insert, 'Filter order class')
t = replace_once(t,
'''    m_pageOrderOptions.push_back(PageOrderOption(tr("Grayscale sources on top"), order_by_source_color,\n                                 tr("Groups the pages by presence\\nof a non grey color in the source files")));''',
'''    m_pageOrderOptions.push_back(PageOrderOption(tr("Grayscale sources on top"), order_by_source_color,\n                                 tr("Groups the pages by presence\\nof a non grey color in the source files")));\n    m_pageOrderOptions.push_back(PageOrderOption(\n        tr("Scanner background on top"),\n        ProviderPtr(new OrderByScannerBackground(m_ptrSettings)),\n        tr("Pages with the longest continuous dark edge are shown first")\n    ));''', 'Filter add order option')
write(p, t)

# --- Output geometry: physical sheet intersected with Page Split pre-crop polygon. ---
p = 'src/core/filters/output/Task.cpp'
t = read(p)
start = t.find('void protectScannerBackground(QImage& image, Qt::GlobalColor fillColor)')
end = t.find('void fillArchiveLayoutMargins(', start)
if start < 0 or end < 0:
    raise SystemExit('protectScannerBackground block not found')
new_helpers = r'''QPolygonF archiveAllowedPagePolygon(FilterData const& data, ImageTransformation const& xform)
{
    QPainterPath allowed;
    bool haveAllowed = false;

    const QPolygonF physicalOrig = detectPhysicalPagePolygon(data.origImage());
    if (physicalOrig.size() == 4) {
        const QPolygonF physicalOut = xform.transform().map(physicalOrig);
        QPainterPath physicalPath;
        physicalPath.addPolygon(physicalOut);
        physicalPath.closeSubpath();
        allowed = physicalPath;
        haveAllowed = true;
    }

    // Page Split already knows the binding / cutter geometry.  The resulting
    // pre-crop area is the selected page polygon after that cutter, so it is
    // a hard production boundary even when Select Content was edited manually.
    const QPolygonF splitPage = xform.resultingPreCropArea();
    if (splitPage.size() >= 3) {
        QPainterPath splitPath;
        splitPath.addPolygon(splitPage);
        splitPath.closeSubpath();
        allowed = haveAllowed ? allowed.intersected(splitPath) : splitPath;
        haveAllowed = true;
    }

    return haveAllowed ? allowed.toFillPolygon() : QPolygonF();
}

void applyArchivePageGeometry(QImage& image, QPolygonF const& allowedPage,
                              Qt::GlobalColor fillColor)
{
    if (image.isNull() || allowedPage.size() < 3) {
        return;
    }

    QPainterPath full;
    full.addRect(QRectF(image.rect()));
    QPainterPath inside;
    inside.addPolygon(allowedPage);
    inside.closeSubpath();

    QPainter painter(&image);
    painter.setRenderHint(QPainter::Antialiasing, false);
    painter.fillPath(full.subtracted(inside), fillColor);
}

double archiveScannerBackgroundScore(QImage const& image, QRect const& contentRect,
                                     QPolygonF const& allowedPage)
{
    if (image.isNull()) {
        return 0.0;
    }
    const QRect r = contentRect.intersected(image.rect());
    if (r.width() < 8 || r.height() < 8) {
        return 0.0;
    }

    QPainterPath allowed;
    if (allowedPage.size() >= 3) {
        allowed.addPolygon(allowedPage);
        allowed.closeSubpath();
    }

    auto isDarkAllowed = [&](int x, int y) {
        if (!allowed.isEmpty() && !allowed.contains(QPointF(x + 0.5, y + 0.5))) {
            return false;
        }
        return qGray(image.pixel(x, y)) < 55;
    };

    auto horizontalScore = [&](int y) {
        int longest = 0;
        int run = 0;
        for (int x = r.left(); x <= r.right(); ++x) {
            if (isDarkAllowed(x, y)) {
                longest = std::max(longest, ++run);
            } else {
                run = 0;
            }
        }
        return 100.0 * longest / std::max(1, r.width());
    };

    auto verticalScore = [&](int x) {
        int longest = 0;
        int run = 0;
        for (int y = r.top(); y <= r.bottom(); ++y) {
            if (isDarkAllowed(x, y)) {
                longest = std::max(longest, ++run);
            } else {
                run = 0;
            }
        }
        return 100.0 * longest / std::max(1, r.height());
    };

    double score = 0.0;
    const int depth = 3;
    for (int d = 0; d < depth; ++d) {
        score = std::max(score, horizontalScore(std::min(r.bottom(), r.top() + d)));
        score = std::max(score, horizontalScore(std::max(r.top(), r.bottom() - d)));
        score = std::max(score, verticalScore(std::min(r.right(), r.left() + d)));
        score = std::max(score, verticalScore(std::max(r.left(), r.right() - d)));
    }
    return score;
}

'''
t = t[:start] + new_helpers + t[end:]

t = replace_once(t,
'''    QImage out_img;\n    BinaryImage automask_img;\n    BinaryImage speckles_img;''',
'''    QImage out_img;\n    BinaryImage automask_img;\n    BinaryImage speckles_img;\n    double archiveScannerBackground = 0.0;''', 'Task score variable')

t = replace_once(t,
'''        // ScanTailor Archive: literal Page Layout paint.\n        const Qt::GlobalColor archiveFill = archiveMarginFillColor();\n        protectScannerBackground(out_img, archiveFill);\n        fillArchiveLayoutMargins(out_img, generator.outputContentRect(), archiveFill);''',
'''        // ScanTailor Archive: hard geometry.  The allowed source is the\n        // intersection of the detected physical sheet and Page Split's page\n        // polygon (binding / cutter included).  This applies to AUTO and MANUAL\n        // content rectangles alike and preserves slanted paper edges.\n        const Qt::GlobalColor archiveFill = archiveMarginFillColor();\n        const QPolygonF archiveAllowedPage = archiveAllowedPagePolygon(data, new_xform);\n        archiveScannerBackground = archiveScannerBackgroundScore(\n            out_img, generator.outputContentRect(), archiveAllowedPage\n        );\n        applyArchivePageGeometry(out_img, archiveAllowedPage, archiveFill);\n        fillArchiveLayoutMargins(out_img, generator.outputContentRect(), archiveFill);''', 'Task final geometry')

t = replace_once(t,
'''                new_picture_zones, new_fill_zones\n            );''',
'''                new_picture_zones, new_fill_zones,\n                archiveScannerBackground\n            );''', 'Task OutputParams score')
write(p, t)

print('geometry QC edits applied')
