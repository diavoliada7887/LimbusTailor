# LimbusTailor patch set

Apply these patches in numeric order to ScanTailor Universal 0.2.13.

1. `0001-output-formats.patch`
2. `0002-content-padding-mm.patch`
3. `0003-sparse-page-protection.patch`
4. `0004-modern-windows-portable-build.patch`
5. `0005-modern-exiv2-windows.patch` — Windows compatibility only; the Linux CI build intentionally skips it.
6. `0006-hard-page-boundary-and-output-ui.patch`

Patch 0006 contains the current archive-production behavior and is amended in place rather than split into later experimental patch numbers.
