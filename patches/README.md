# LimbusTailor patch set

Apply these patches in numeric order to ScanTailor Universal 0.2.13.

1. `0001-output-formats.patch`
2. `0002-content-padding-mm.patch`
3. `0003-sparse-page-protection.patch`
4. `0004-modern-windows-portable-build.patch`
5. `0005-modern-exiv2-windows.patch` — Windows compatibility only; the Linux CI build intentionally skips it.
6. `0006-hard-page-boundary-and-output-ui.patch`
7. `0007-arkhivum-ui-localization.patch`

Patch 0006 contains the current archive-production behavior and remains the functional geometry / output / QC layer.

Current 0006 behavior detects the physical sheet against a dark scanner bed before AUTO content analysis. The real slanted four-edge sheet polygon is passed into ContentBoxFinder as its page mask, so scanner-bed triangles are excluded before shadow and content detection. Added content-safety margins, sparse-page restoration, and the optional top-right mark protection are constrained by that physical sheet boundary.

At Output, the permitted source area is the intersection of the detected physical sheet and Page Split's resulting pre-crop polygon. This makes the detected binding / cutter a hard boundary even after MANUAL content-box enlargement and preserves slanted physical paper edges instead of carrying rectangular scanner-bed wedges into the output.

`Protect top-right mark` is opt-in. When enabled, the AUTO content rectangle is extended toward the physical sheet's upper-right corner without attempting to recognize faint pencil itself; the hard physical-page geometry still prevents that extension from crossing the sheet edge.

Output also stores a scanner-background edge score based on the longest continuous dark run along the content edges. The `Scanner background on top` page-order option uses that score to bring the most suspicious processed pages to the top for quality control.

Patch 0007 is deliberately separate from production geometry. It adds the Arkhivum light visual theme, makes it the one-time default without locking users out of the existing style settings, and extends the existing Russian translation with LimbusTailor-specific controls. English source strings remain unchanged.
