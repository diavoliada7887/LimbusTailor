# LimbusTailor patch set

Apply these patches in numeric order to ScanTailor Universal 0.2.13.

1. `0001-output-formats.patch`
2. `0002-content-padding-mm.patch`
3. `0003-sparse-page-protection.patch`
4. `0004-modern-windows-portable-build.patch`
5. `0005-modern-exiv2-windows.patch` — Windows compatibility only; the Linux CI build intentionally skips it.
6. `0006-hard-page-boundary-and-output-ui.patch`

Patch 0006 contains the current archive-production behavior and is amended in place rather than split into later experimental patch numbers.

Current 0006 behavior detects the physical sheet against a dark scanner bed before AUTO content analysis. The real slanted four-edge sheet polygon is passed into ContentBoxFinder as its page mask, so scanner-bed triangles are excluded before shadow and content detection. Added content-safety margins, sparse-page restoration, and the optional top-right mark protection are all constrained by that same physical sheet boundary.

`Protect top-right mark` is opt-in. When enabled, the AUTO content rectangle is extended toward the physical sheet's upper-right corner without attempting to recognize faint pencil itself; the physical-page clamp still prevents that extension from crossing the sheet edge.
