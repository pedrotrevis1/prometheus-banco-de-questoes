# Search pagination benchmark

Remeasured 2026-11-17 on the owner's MacBook Air (arm64, macOS 27.2), Python
3.14.5, PySide6/Qt 6.11.1, using offscreen Qt. Synthetic banks were held in
memory; no personal bank was opened. Each dataset used one cold page and ten
subsequent page turns. Every iteration checked the exact page IDs, total count,
and 50 visible and live cards after deferred deletion. The benchmark stops on
any application/search error.

Times are milliseconds. Full time includes Qt event processing and deferred
card deletion. Query time includes count and bounded content fetch; card time
covers construction. Layout/rendering are part of full time, not separately
isolated. The earlier measurements predate the current schema and are replaced
by this run.

| Rows | Content | Cold query / HTML / cards / full | Warm median query / HTML / cards / full | Warm max full | Max live cards |
|---:|---|---|---|---:|---:|
| 2,500 | Rich | 1.20 / 7.39 / 40.52 / 448.61 | 0.58 / 6.97 / 31.80 / 453.06 | 559.05 | 50 |
| 5,000 | Rich | 1.21 / 6.91 / 34.69 / 424.14 | 1.89 / 7.65 / 35.53 / 513.50 | 1143.68 | 50 |
| 2,500 | Light | 0.35 / 1.50 / 25.29 / 145.57 | 0.22 / 1.04 / 20.26 / 145.69 | 172.86 | 50 |
| 5,000 | Light | 0.26 / 1.13 / 22.77 / 137.46 | 0.25 / 1.03 / 20.13 / 143.95 | 145.87 | 50 |

Rich records had a 2,199-character HTML prompt with a 128×128 synthetic PNG
(379 bytes) and five 307-character alternatives. Light records had a
20-character prompt, 18-character alternatives and no image. This is an
offscreen synthetic measurement, not a Windows benchmark or a guarantee for
larger real-world images.

Reproduce from the repository root with the development environment active:

```sh
PYTHONPATH=. QT_QPA_PLATFORM=offscreen python specs/007-search-pagination/benchmark.py
PYTHONPATH=. QT_QPA_PLATFORM=offscreen python specs/007-search-pagination/benchmark.py --light
```
