# Acceptance: Start a new exam

T002: on branch `012-new-exam-workflow`, 011 is complete; no unresolved clarification markers were found in 012. An isolated Qt offscreen window with an in-memory synthetic normalized bank had no "Nova prova" button. Selecting question 1 produced a dirty draft with count 2, multiple/shuffles off and answers included, confirming the documented startup defaults. No personal configuration or bank was opened. The owner also requested a titled panel matching "Opções da prova" for the new controls; FR-001 now records this.

T003: extracted draft copying, defaults, dirty comparison and prompt decisions to `domain.exam_session`, preserving order synchronization at the existing adapter. Core/order/guard tests passed (4 tests); existing close/open/bank-switch callers retain the same guard.

T004: the new fresh-state regression failed before implementation; `SearchViewState.reset` clears the original selection set in place and resets mode/page/applied filters, while the domain fresh-draft operation clears explicit order and returns independent defaults. Core/order/pagination tests passed (39 tests).

T005: the new UI regressions failed before implementation. They now pass for full draft/filter reset, clean snapshot, cancel preservation and the titled management panel. The guard prompts before state mutation; save uses existing persistence.

T006: tested retry after synthetic aggregate failure, stale card disposal, disabled no-bank action, empty bank, invalid pending years, category visibility/checks, filter defaults, repeated reset and retained editor text. The initial stale-card regression failed before the retry path was added.

T007: tested unnamed Save, name cancellation, save failure, Discard and Cancel; dirty saved-exam Save/Discard/Cancel; in-memory saved-table equality on discard; and generating A then B without restart. A's saved questions, usages and arrangements survived; B received its own ID and history. A further test generated two shuffled versions of A before New and verified that B received one independent arrangement. A cancelled transition now inspects a non-mutating order preview, preserving even a temporarily unsynchronized explicit order.

T008: targeted domain/order/saved-exam/search/preview/storage checks passed (123 tests); full `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` passed (398 tests). Tests use isolated configuration and synthetic in-memory databases.

After T008, an additional isolated UI check confirmed that the "Gerenciar provas" panel contains the requested controls, fits in the normal window and uses the existing light/dark panel colors. A synthetic failure reading a saved exam during Save now reports the error and preserves the draft; these five additional targeted checks passed.

## Native acceptance (T009 closed by owner)

A synthetic macOS window was launched with an in-memory bank and temporary configuration. The computer-control interface selected another already-running Python window rather than the synthetic test window, so no interaction was performed with that window and the synthetic process alone was closed. No native visual or interaction pass is claimed from that agent attempt. The owner subsequently reported that the visual test passed and, after verifying the filename fix, explicitly instructed that T009 be marked complete. The owner did not specify the platform, theme, scaling or individual scenarios exercised; no separate passes are asserted for those combinations.

Final automated rerun after the saved-exam failure handling and panel checks: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` — 400 passed. T010 updated the baseline, 006 cross-reference, roadmap and handoff after the owner authorized T009 closure.

## Owner visual feedback and filename correction

The owner reported that the visual test passed, and identified that the Word save dialog suggested the discipline-based filename instead of the name just entered for the exam. The saved exam name is now used for the editable suggestion, with cross-platform invalid filename characters replaced; legacy banks retain their prior default. Tests first reproduced the incorrect suggestion and then passed, including an open exam with a different picker selection, portable filename edge cases and the two-exam generation workflow. Targeted saved-exam/export checks passed (60 tests), followed by six relevant checks after adding the picker regression. The owner confirmed the filename fix works and explicitly directed closure of T009. The report does not establish which individual platform/scaling cases were exercised.

Final full-suite verification after the filename correction and owner acceptance: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` — 403 passed.
