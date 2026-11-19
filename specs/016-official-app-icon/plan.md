# Implementation plan: Official application icon

Use the supplied 1024px Apple export as the single source of truth. Set it on
QApplication for source and frozen execution, pass platform-specific packaging
options to the Windows and macOS build commands, bundle the runtime PNG, and
use a stable macOS bundle identifier. Pillow is added to development
requirements because PyInstaller uses it to convert a non-native PNG icon when
building the macOS bundle.

## Constitution check

- No database, user data, or runtime behavior is changed.
- The new build script is explicit about macOS-only execution.
- The icon source remains in the user-provided `icon/` folder.
