# Resize reproduction

On the owner's clarification, only the question card or page content grows;
the issue occurs in collapsed or expanded state. Reproduced 2026-11-17 with
Python 3.14.5 and PySide6/Qt 6.11.1, macOS arm64, offscreen Qt, light theme,
1250×850 logical-pixel window, three synthetic long essay questions, result
scroll at top and no personal bank. The shared handle also serves registration
editors and category trees.

Press the first card's handle, then send global pointer movements of +100,
+300, +600 and +1000 pixels, allowing the event loop to settle between moves.
In collapsed state, the preview heights were 150, 250, 450, 750 and 1150 pixels
while the result viewport stayed 567 pixels high. The first card grew from 266
to 1266 pixels. Window, sidebar, footer and result scroll position remained
unchanged. The unbounded card/page growth matches the owner's clarification.

In expanded state, starting from 300 pixels, the same moves produced 400, 600,
900, then 300 pixels: the automatic document-fit callback overrode the manual
drag. These are observed failures of the specified bounds and manual resizing
precedence; a visible platform check remains pending.
