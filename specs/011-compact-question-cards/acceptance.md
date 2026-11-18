# Acceptance: Compact question cards

## Before implementation (T002)

On macOS, Qt offscreen, synthetic standalone cards with short preview and identical metadata produced the following header heights in logical pixels (0 / 2 / 1,000 uses): 640 width: 75 / 105 / 193; 900 width: 60 / 75 / 193; 1200 width: 60 / 75 / 193. Screenshots were captured temporarily under `/private/tmp/spec011-before-*.png`; these are offscreen measurements, not native acceptance. The 1,000-use label was clipped by the fixed initial card height. Source inspection confirms one `question_usages` detail query per displayed normalized card in `load_questions`, including unused cards. No personal database was opened. Prerequisite specs 006 and 010 are implemented; 006 release checks remain pending. No clarification markers were found in 011 or those prerequisites.

T003: extracted the existing metadata fields and fallbacks into `domain.card_data`; `pytest -q tests/domain/test_card_metadata.py tests/domain/test_school_years.py tests/ui/test_preview_resize.py` passed (21 tests). Existing semicolon replacement spacing is deliberately preserved.

T004: a failing aggregate regression was demonstrated before adding the page-ID-scoped query and presentation helpers. `pytest -q tests/storage/test_saved_exams.py tests/domain/test_card_metadata.py tests/domain/test_usage_history_presentation.py` passed (15 tests).

T004 completed: added the count query and deferred callback to page loading. The new UI regression failed first (one eager detail query) and then passed alongside storage/domain checks (14 tests). An aggregate failure follows the existing search-error path before the old page is disposed.

T005: new hierarchy, escaped field values and a stacked action column are in place; a Qt-free width decision handles narrow cards. The new assertions failed before implementation. Domain, card hierarchy and preview regressions passed (20 tests). Preview chrome now measures the laid-out header geometry rather than its width-independent size hint, which otherwise falsely reduced the expanded preview's available drag range.

T006: offscreen tests cover deferred reads, retry after a visible error, zero/unavailable states without reads, keyboard activation/Escape, outside-click dismissal, long-history scrolling, screen bounds, hover and popup disposal on page/bank replacement. These are automated adapter checks, not native platform acceptance.

T007: replaced the inline-history assertion and verified generation/deletion refresh, search, pagination, selection, edit/duplicate and prior preview tests. Offscreen regressions also cover literal metadata, 2 versus 1,000 count header heights, a 640-pixel card, long unbroken names and preview growth/reflow in both header orientations. Targeted tests passed (89 tests before the additional two reflow cases); full `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` passed (375 tests). No native platform acceptance is inferred from these tests.

## Native acceptance (T008)

A synthetic standalone window was inspected on macOS (Darwin arm64, default display scaling, light theme, 900 logical-pixel window). The labeled card and stacked actions were visible; clicking the usage count opened a bounded popup, mouse scrolling changed its position, Escape closed it and restored focus. A first native attempt showed that End did not move the popup. A subsequent code change handles scrolling keys; separate native checks confirmed Down and End move the popup scrollbar once the popup has opened. The first sandboxed GUI launch could not connect to macOS services; an isolated launch outside the sandbox succeeded. No personal bank or configuration was used.

A separate 360-logical-pixel dark-theme synthetic window showed wrapped metadata and actions below it. Pending: real pointer hover and handoff, remaining keyboard navigation, preview drag, additional widths and display scaling on macOS, and all Windows visual checks. Before/after screenshots have not been retained in the repository. On 2026-11-18 the owner explicitly authorized marking T008 done after the requested theme fixes, despite these checks remaining unperformed. They are not represented as having passed.

## Owner feedback and final verification

The owner reported a light usage-history surface in dark mode and requested a light green metadata background, then explicitly authorized closing T008. The popup now explicitly follows the active theme, including after theme changes; metadata has a light green surface with dark readable text. The new theme regression failed before the fix and passes after it. The preview regression suite and theme-switch test passed (19 tests); the full `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` suite passed (376 tests). The owner-authorized closure of T008 does not assert completion of the unperformed native checks above.

## Dark metadata follow-up

The owner requested that dark mode use the app's existing dark green metadata surface. Existing cards now update their background and text colors when the theme changes; light mode retains its light green surface. A regression first failed on the light background in dark mode and then passed.
