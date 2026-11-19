# Feature specification: Dark-theme surface consistency

**Folder**: `013-dark-theme-consistency` | **Status**: Implemented | **Created**: 2026-11-19

## Problem

The generate tab's scroll content and the search tab's "Uso em provas" combo
popup can retain light surfaces while the application is in dark mode.

## Acceptance scenarios

1. **Given** dark mode, **when** the third tab is displayed, **then** its
   scroll content uses the dark application background rather than white.
2. **Given** dark mode, **when** the "Uso em provas" combo is opened, **then**
   its popup uses the dark combo surface and light text.
3. **Given** light mode, **when** either surface is displayed, **then** the
   existing light-theme appearance is preserved.

## Scope

Use the existing theme system and combo-popup helper. Do not change filtering
behavior or introduce a new dependency.
