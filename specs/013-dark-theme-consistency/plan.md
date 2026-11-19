# Implementation plan: Dark-theme surface consistency

Add an object name for the generate-tab scroll content so both theme stylesheets
can target it, and configure the usage filter with the existing themed combo
popup helper. Cover both regressions with focused offscreen UI tests.

## Constitution check

- The change is limited to Qt theme adaptation; no data or database behavior changes.
- The regression tests use the existing synthetic in-memory fixture.
- User-facing text remains Brazilian Portuguese and no dependency is added.
