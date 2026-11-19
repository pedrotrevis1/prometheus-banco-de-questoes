# Feature specification: Official application icon

**Folder**: `016-official-app-icon` | **Status**: Implemented | **Created**: 2026-11-19

## Acceptance scenarios

1. **Given** the source application is launched, **then** QApplication uses the
   official PNG from `icon/prometheus-icon-apple Exports/` as its window icon.
2. **Given** a Windows build is produced, **then** PyInstaller applies the
   official `.ico` to the executable and bundles the PNG for runtime windows.
3. **Given** a macOS build is produced on macOS, **then** PyInstaller applies
   the official PNG (converted by Pillow to the platform bundle icon format),
   uses the stable bundle identifier, and bundles the PNG for runtime windows.
4. **Given** the app is running, **then** the main window and dialogs inherit
   the application icon through QApplication.

## Scope

Packaging and application identity only. No question-bank or export behavior
changes.
