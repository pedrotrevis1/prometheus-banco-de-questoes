# Implementation plan: Usable help dialog

Replace the long-form help message box with a resizable QDialog containing a
read-only QTextBrowser and an explicit close button. Keep the existing
Portuguese content and application stylesheet, and cover the layout contract
with an offscreen UI regression test.

## Constitution check

- This is a presentation-only change with no database or data mutation.
- The existing help content and theme system are reused.
- The test uses the existing synthetic UI fixture and targeted verification.
