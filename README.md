# LimbusTailor

Archive-oriented ScanTailor derivative work built from ScanTailor Universal 0.2.13.

Upstream: `trufanov-nok/scantailor-universal`, tag `0.2.13`.

LimbusTailor currently keeps the upstream source external and applies a small ordered patch set during CI builds. This keeps the donor history clear while we develop archive-production features.

Current features include:

- final TIFF / JPEG / PNG output with JPEG quality control;
- per-side content safety margins in millimetres;
- sparse-page / hard-page-boundary protection;
- white / black Page Layout margin fill;
- content detection tuning;
- scanner-background QC ordering;
- Arkhivum light UI theme using the archive brand palette;
- Russian localization for LimbusTailor-specific controls while English remains the source-language interface;
- portable Windows build.

## Patch order

Apply `patches/0001` through `patches/0007` in numeric order to ScanTailor Universal 0.2.13.

## License and upstream attribution

ScanTailor Universal is GPL-3.0 licensed. LimbusTailor modifications derived from that code are distributed on the same GPL-compatible basis. Original copyright and license notices are retained in the patched source.
