# Implementation plan: Question editing

**Spec**: [spec.md](spec.md) | **Status**: In progress

## Approach

Use a backup-protected forward migration from schema 1 to 2 to add a nullable
last-modified timestamp; do not invent timestamps for existing questions. Keep
all question serialization, validation, dirty-state comparison, and SQL in
Qt-free domain/storage modules. Widget methods collect values, render forms,
route events and display Portuguese messages. Preserve rich HTML and embedded
images on an unchanged edit, rather than relying on a lossy HTML round trip.

Question cards expose edit and duplicate actions. The registration form tracks
its mode and a saved snapshot to detect unsaved changes. Opening another
question, switching banks or closing the app requests confirmation before
replacing a dirty form. Updating a question retains its ID and the selection.
An absent category is reported; it is not silently assigned elsewhere.

Formatting and equation insertion target the last focused supported editor;
clicking a toolbar control must not lose that target. Existing registration and
export behavior remains covered by tests. Format timestamps for Brazilian users
without changing the stored stable representation.

## Ordered verification

- Exercise migration/backup and rollback using synthetic temporary databases;
  do not access personal banks. Verify legacy rows and column order stay intact.
- Unit test validation, edit/duplicate behavior, timestamps, preserved rich
  HTML, category handling and dirty-state rules without Qt.
- Use offscreen UI tests for toolbar focus, edit/cancel/duplicate, discard
  confirmation, filtered paging, selection and export round trips.
- Update the baseline, roadmap and help. Windows checks and release tagging
  remain pending until they can actually be performed.

## Constitution check

Data is protected by the existing pre-migration backup and transaction. No
network or new dependency is introduced. Business rules and persistence remain
outside widgets and are tested; user-facing text is Brazilian Portuguese.
