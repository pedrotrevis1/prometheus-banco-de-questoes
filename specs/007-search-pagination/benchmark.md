# Search pagination benchmark

Measured 2026-11-17 on the owner's MacBook Air (arm64, macOS 27.2), Python
3.14.5, PySide6/Qt 6.11.1, with the offscreen Qt platform. Synthetic data was
held in memory; no personal bank was opened. Each dataset used one cold page
and ten subsequent page turns. The table shows milliseconds; full time includes
Qt event processing and deferred card deletion. Query time includes the count
and bounded content fetch. Card time covers construction; layout and rendering
are included in full time, not isolated as a separate measurement.

| Rows | Content | Cold query / HTML / cards / full | Warm median query / HTML / cards / full | Warm max full | Max live cards |
|---:|---|---|---|---:|---:|
| 2,500 | Rich | 1.04 / 6.48 / 25.05 / 588.86 | 0.50 / 6.18 / 24.42 / 582.94 | 588.26 | 50 |
| 5,000 | Rich | 0.71 / 6.18 / 24.04 / 574.19 | 0.76 / 6.21 / 24.54 / 585.12 | 656.58 | 50 |
| 2,500 | Light | 0.25 / 1.42 / 19.82 / 153.46 | 0.22 / 1.07 / 18.89 / 157.64 | 203.88 | 50 |
| 5,000 | Light | 0.23 / 1.04 / 17.38 / 153.59 | 0.24 / 1.05 / 17.65 / 155.19 | 158.76 | 50 |

Rich records had a 2,199-character HTML prompt with a 128×128 synthetic PNG
(379 encoded bytes) and five 307-character alternatives. Light records had a
20-character prompt, 18-character alternatives and no image. Every page
fetched at most 50 full records. This is an offscreen synthetic measurement,
not a Windows benchmark or a guarantee for larger real-world images.

Reproduce from the repository root with the development environment active:

```sh
PYTHONPATH=. QT_QPA_PLATFORM=offscreen python specs/007-search-pagination/benchmark.py
PYTHONPATH=. QT_QPA_PLATFORM=offscreen python specs/007-search-pagination/benchmark.py --light
```
