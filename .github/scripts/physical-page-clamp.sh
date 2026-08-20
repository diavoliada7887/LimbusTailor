#!/usr/bin/env bash
set -euxo pipefail

ROOT="$PWD"
rm -rf /tmp/stu
git clone https://github.com/trufanov-nok/scantailor-universal.git /tmp/stu
cd /tmp/stu
git checkout c1a7d797160c12aef32a19e7e08f2e099c8f3292
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

for p in 0001-output-formats.patch 0002-content-padding-mm.patch 0003-sparse-page-protection.patch 0004-modern-windows-portable-build.patch 0005-modern-exiv2-windows.patch; do
  git apply "$ROOT/patches/$p"
done
git add -A
git commit -m "baseline after patches 0001-0005"
BASE=$(git rev-parse HEAD)

git apply "$ROOT/patches/0006-hard-page-boundary-and-output-ui.patch"

python3 - <<'PY'
from pathlib import Path

path = Path('/tmp/stu/src/core/filters/select_content/Task.cpp')
text = path.read_text()

include_old = '''#include <QObject>\n#include <QTransform>\n#include <QDebug>\n\n#include <iostream>\n'''
include_new = '''#include <QObject>\n#include <QTransform>\n#include <QDebug>\n#include <QImage>\n#include <QPolygonF>\n#include <algorithm>\n#include <cmath>\n#include <limits>\n#include <vector>\n\n#include <iostream>\n'''
if include_old not in text:
    raise SystemExit('include marker not found')
text = text.replace(include_old, include_new, 1)

ns_marker = '''namespace select_content\n{\n\n'''
helper = r'''namespace
{
struct ArchiveLinearFit
{
    double a = 0.0;
    double b = 0.0;
    bool valid = false;
};

ArchiveLinearFit archiveFitLine(std::vector<QPointF> const& points, bool xFromY)
{
    if (points.size() < 4) {
        return ArchiveLinearFit();
    }

    auto solve = [xFromY](std::vector<QPointF> const& pts) {
        ArchiveLinearFit fit;
        double sumT = 0.0;
        double sumV = 0.0;
        double sumTT = 0.0;
        double sumTV = 0.0;
        for (QPointF const& p : pts) {
            const double t = xFromY ? p.y() : p.x();
            const double v = xFromY ? p.x() : p.y();
            sumT += t;
            sumV += v;
            sumTT += t * t;
            sumTV += t * v;
        }
        const double n = static_cast<double>(pts.size());
        const double denom = n * sumTT - sumT * sumT;
        if (std::abs(denom) < 1e-9) {
            return fit;
        }
        fit.a = (n * sumTV - sumT * sumV) / denom;
        fit.b = (sumV - fit.a * sumT) / n;
        fit.valid = true;
        return fit;
    };

    ArchiveLinearFit first = solve(points);
    if (!first.valid) {
        return first;
    }

    std::vector<double> residuals;
    residuals.reserve(points.size());
    for (QPointF const& p : points) {
        const double t = xFromY ? p.y() : p.x();
        const double v = xFromY ? p.x() : p.y();
        residuals.push_back(std::abs(v - (first.a * t + first.b)));
    }
    std::vector<double> sorted = residuals;
    std::sort(sorted.begin(), sorted.end());
    const double median = sorted[sorted.size() / 2];
    const double limit = std::max(3.0, median * 3.0);

    std::vector<QPointF> filtered;
    filtered.reserve(points.size());
    for (size_t i = 0; i < points.size(); ++i) {
        if (residuals[i] <= limit) {
            filtered.push_back(points[i]);
        }
    }
    return filtered.size() >= 4 ? solve(filtered) : first;
}

bool archiveFindBrightRun(QImage const& gray, int fixed, bool horizontal, bool reverse,
                          int threshold, int* edge)
{
    const int length = horizontal ? gray.width() : gray.height();
    const int run = std::max(4, length / 300);
    int count = 0;

    for (int step = 0; step < length; ++step) {
        const int pos = reverse ? length - 1 - step : step;
        const int x = horizontal ? pos : fixed;
        const int y = horizontal ? fixed : pos;
        if (qGray(gray.pixel(x, y)) >= threshold) {
            ++count;
            if (count >= run) {
                *edge = reverse ? pos + run - 1 : pos - run + 1;
                return true;
            }
        } else {
            count = 0;
        }
    }
    return false;
}

QPointF archiveIntersectLines(ArchiveLinearFit const& vertical,
                              ArchiveLinearFit const& horizontal)
{
    const double denom = 1.0 - horizontal.a * vertical.a;
    if (std::abs(denom) < 1e-9) {
        return QPointF();
    }
    const double y = (horizontal.a * vertical.b + horizontal.b) / denom;
    const double x = vertical.a * y + vertical.b;
    return QPointF(x, y);
}

QPolygonF archiveDetectPhysicalPagePolygon(QImage const& image)
{
    if (image.width() < 64 || image.height() < 64) {
        return QPolygonF();
    }

    const int maxDim = 1800;
    const double scale = std::min(
        1.0, maxDim / static_cast<double>(std::max(image.width(), image.height()))
    );
    QImage small = scale < 1.0
        ? image.scaled(qRound(image.width() * scale), qRound(image.height() * scale),
                       Qt::IgnoreAspectRatio, Qt::SmoothTransformation)
        : image;
    QImage gray = small.convertToFormat(QImage::Format_Grayscale8);

    std::vector<int> borderValues;
    std::vector<int> centerValues;
    const int w = gray.width();
    const int h = gray.height();
    const int stride = std::max(1, std::min(w, h) / 120);
    for (int x = 0; x < w; x += stride) {
        borderValues.push_back(qGray(gray.pixel(x, 0)));
        borderValues.push_back(qGray(gray.pixel(x, h - 1)));
    }
    for (int y = 0; y < h; y += stride) {
        borderValues.push_back(qGray(gray.pixel(0, y)));
        borderValues.push_back(qGray(gray.pixel(w - 1, y)));
    }
    for (int y = h / 3; y < (2 * h) / 3; y += stride) {
        for (int x = w / 3; x < (2 * w) / 3; x += stride) {
            centerValues.push_back(qGray(gray.pixel(x, y)));
        }
    }
    if (borderValues.empty() || centerValues.empty()) {
        return QPolygonF();
    }

    std::sort(borderValues.begin(), borderValues.end());
    std::sort(centerValues.begin(), centerValues.end());
    const int bg = borderValues[borderValues.size() / 2];
    const int paper = centerValues[centerValues.size() / 2];
    if (paper - bg < 30) {
        return QPolygonF();
    }
    const int threshold = qBound(20, bg + qRound((paper - bg) * 0.42), 235);

    std::vector<QPointF> leftPts, rightPts, topPts, bottomPts;
    const int samples = 31;
    for (int i = 2; i < samples - 2; ++i) {
        const int y = qRound((i / static_cast<double>(samples - 1)) * (h - 1));
        int left = 0, right = 0;
        if (archiveFindBrightRun(gray, y, true, false, threshold, &left)) {
            leftPts.emplace_back(left, y);
        }
        if (archiveFindBrightRun(gray, y, true, true, threshold, &right)) {
            rightPts.emplace_back(right, y);
        }

        const int x = qRound((i / static_cast<double>(samples - 1)) * (w - 1));
        int top = 0, bottom = 0;
        if (archiveFindBrightRun(gray, x, false, false, threshold, &top)) {
            topPts.emplace_back(x, top);
        }
        if (archiveFindBrightRun(gray, x, false, true, threshold, &bottom)) {
            bottomPts.emplace_back(x, bottom);
        }
    }

    const ArchiveLinearFit left = archiveFitLine(leftPts, true);
    const ArchiveLinearFit right = archiveFitLine(rightPts, true);
    const ArchiveLinearFit top = archiveFitLine(topPts, false);
    const ArchiveLinearFit bottom = archiveFitLine(bottomPts, false);
    if (!left.valid || !right.valid || !top.valid || !bottom.valid) {
        return QPolygonF();
    }

    QPolygonF poly;
    poly << archiveIntersectLines(left, top)
         << archiveIntersectLines(right, top)
         << archiveIntersectLines(right, bottom)
         << archiveIntersectLines(left, bottom);

    const QRectF bounds = poly.boundingRect();
    if (!bounds.isValid() || bounds.width() < w * 0.25 || bounds.height() < h * 0.25
        || bounds.left() < -w * 0.1 || bounds.top() < -h * 0.1
        || bounds.right() > w * 1.1 || bounds.bottom() > h * 1.1) {
        return QPolygonF();
    }

    if (scale < 1.0) {
        QTransform back;
        back.scale(1.0 / scale, 1.0 / scale);
        poly = back.map(poly);
    }
    return poly;
}

QPolygonF archiveCanonicalPage(QPolygonF const& poly)
{
    if (poly.size() != 4) {
        return QPolygonF();
    }

    double minSum = std::numeric_limits<double>::infinity();
    double maxSum = -std::numeric_limits<double>::infinity();
    double minDiff = std::numeric_limits<double>::infinity();
    double maxDiff = -std::numeric_limits<double>::infinity();
    QPointF tl, tr, br, bl;
    for (QPointF const& p : poly) {
        const double sum = p.x() + p.y();
        const double diff = p.x() - p.y();
        if (sum < minSum) { minSum = sum; tl = p; }
        if (sum > maxSum) { maxSum = sum; br = p; }
        if (diff > maxDiff) { maxDiff = diff; tr = p; }
        if (diff < minDiff) { minDiff = diff; bl = p; }
    }

    QPolygonF out;
    out << tl << tr << br << bl;
    if (!out.boundingRect().isValid() || out.boundingRect().width() < 16.0
        || out.boundingRect().height() < 16.0) {
        return QPolygonF();
    }
    return out;
}

bool archiveYAtX(QPointF const& a, QPointF const& b, double x, double* y)
{
    const double dx = b.x() - a.x();
    if (std::abs(dx) < 1e-9) {
        return false;
    }
    *y = a.y() + (x - a.x()) * (b.y() - a.y()) / dx;
    return std::isfinite(*y);
}

bool archiveXAtY(QPointF const& a, QPointF const& b, double y, double* x)
{
    const double dy = b.y() - a.y();
    if (std::abs(dy) < 1e-9) {
        return false;
    }
    *x = a.x() + (y - a.y()) * (b.x() - a.x()) / dy;
    return std::isfinite(*x);
}

QRectF archiveClampPaddingToPhysicalPage(QRectF const& baseContent,
                                         QRectF const& expandedContent,
                                         QPolygonF const& mappedPage,
                                         double insetX, double insetY)
{
    const QPolygonF page = archiveCanonicalPage(mappedPage);
    if (page.size() != 4) {
        return baseContent;
    }

    const QPointF tl = page[0];
    const QPointF tr = page[1];
    const QPointF br = page[2];
    const QPointF bl = page[3];
    QRectF out = expandedContent;

    for (int pass = 0; pass < 2; ++pass) {
        double topL = 0.0, topR = 0.0, bottomL = 0.0, bottomR = 0.0;
        if (!archiveYAtX(tl, tr, out.left(), &topL)
            || !archiveYAtX(tl, tr, out.right(), &topR)
            || !archiveYAtX(bl, br, out.left(), &bottomL)
            || !archiveYAtX(bl, br, out.right(), &bottomR)) {
            return baseContent;
        }
        const double topLimit = std::max(topL, topR) + insetY;
        const double bottomLimit = std::min(bottomL, bottomR) - insetY;
        out.setTop(std::min(baseContent.top(), std::max(out.top(), topLimit)));
        out.setBottom(std::max(baseContent.bottom(), std::min(out.bottom(), bottomLimit)));

        double leftT = 0.0, leftB = 0.0, rightT = 0.0, rightB = 0.0;
        if (!archiveXAtY(tl, bl, out.top(), &leftT)
            || !archiveXAtY(tl, bl, out.bottom(), &leftB)
            || !archiveXAtY(tr, br, out.top(), &rightT)
            || !archiveXAtY(tr, br, out.bottom(), &rightB)) {
            return baseContent;
        }
        const double leftLimit = std::max(leftT, leftB) + insetX;
        const double rightLimit = std::min(rightT, rightB) - insetX;
        out.setLeft(std::min(baseContent.left(), std::max(out.left(), leftLimit)));
        out.setRight(std::max(baseContent.right(), std::min(out.right(), rightLimit)));
    }

    if (!out.isValid() || out.isEmpty()) {
        return baseContent;
    }
    return out;
}
} // anonymous namespace

'''
if ns_marker not in text:
    raise SystemExit('namespace marker not found')
text = text.replace(ns_marker, ns_marker + helper, 1)

old = r'''                    const double px_per_mm_x = content_rect.width() / content_mm.width();
                    const double px_per_mm_y = content_rect.height() / content_mm.height();
                    content_rect.adjust(
                        -pad_left_mm * px_per_mm_x,
                        -pad_top_mm * px_per_mm_y,
                        pad_right_mm * px_per_mm_x,
                        pad_bottom_mm * px_per_mm_y
                    );

                    // Never create pixels beyond the physical page box.
                    content_rect = content_rect.intersected(page_rect);
'''
new = r'''                    const double px_per_mm_x = content_rect.width() / content_mm.width();
                    const double px_per_mm_y = content_rect.height() / content_mm.height();
                    const QRectF base_content_rect(content_rect);
                    QRectF expanded_content_rect(content_rect);
                    expanded_content_rect.adjust(
                        -pad_left_mm * px_per_mm_x,
                        -pad_top_mm * px_per_mm_y,
                        pad_right_mm * px_per_mm_x,
                        pad_bottom_mm * px_per_mm_y
                    );

                    // LimbusTailor: detect the real sheet against the dark
                    // scanner bed and clamp only the EXTRA safety margin.
                    const QPolygonF physical_page_orig = archiveDetectPhysicalPagePolygon(data.origImage());
                    if (physical_page_orig.size() == 4) {
                        const QPolygonF physical_page = data.xform().transform().map(physical_page_orig);
                        const double inset_mm = 0.5;
                        content_rect = archiveClampPaddingToPhysicalPage(
                            base_content_rect,
                            expanded_content_rect,
                            physical_page,
                            inset_mm * px_per_mm_x,
                            inset_mm * px_per_mm_y
                        );
                    } else {
                        // Fail safe: if the page edge is uncertain, keep the
                        // original detector box rather than capture scanner bed.
                        content_rect = base_content_rect;
                    }

                    // ScanTailor's own page geometry remains the final guard.
                    content_rect = content_rect.intersected(page_rect);
'''
if old not in text:
    raise SystemExit('padding block marker not found')
text = text.replace(old, new, 1)
path.write_text(text)
PY

git diff --binary "$BASE" -- . > "$ROOT/patches/0006-hard-page-boundary-and-output-ui.patch"
test -s "$ROOT/patches/0006-hard-page-boundary-and-output-ui.patch"

cd "$ROOT"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add patches/0006-hard-page-boundary-and-output-ui.patch
git commit -m "feat: clamp content padding to physical page edges"
git push origin HEAD:work/physical-page-clamp
