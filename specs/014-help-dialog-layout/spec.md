# Feature specification: Usable help dialog

**Folder**: `014-help-dialog-layout` | **Status**: Implemented | **Created**: 2026-11-19

## Problem

The Ajuda action uses a message box for a long rich-text guide. Its fixed
message-box layout can become narrow, excessively tall and extend beyond the
screen.

## Acceptance scenarios

1. **Given** the sidebar is open, **when** the user selects Ajuda, **then** the
   guide opens in a wide dialog with a minimum usable width.
2. **Given** the guide is longer than the available height, **then** its main
   content scrolls instead of overflowing offscreen.
3. **Given** the guide is open, **then** the user can resize it and close it
   with the Fechar action.
4. **Given** either theme, **then** the guide uses the active application theme.
