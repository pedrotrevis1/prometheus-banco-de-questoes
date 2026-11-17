# Feature specification: Project foundation

**Folder**: `001-project-foundation` | **Status**: Draft | **Created**: 2026-11-14

## Why

Nothing in the project can be tested without opening the window, the build is
not reproducible from the repository, and the version lives in a file name.
Every later iteration needs these fixed first. This iteration changes **no
user-visible behavior**.

## User stories

### US1 — A contributor can run and test the project from a clean clone (P1)

As a developer, I clone the repository, follow the README and have the app
running and the tests passing.

**Acceptance scenarios**

1. **Given** a clean clone and Python 3.14, **when** I install the listed
   dependencies and run the documented start command, **then** the app opens.
2. **Given** the same environment, **when** I run `pytest`, **then** the suite
   runs without opening a window and passes.

### US2 — The existing pure logic is protected by tests (P1)

As a maintainer, I can change the version-shuffling, school-year and HTML
clean-up rules knowing a test will fail if I break them.

**Acceptance scenarios**

1. **Given** five alternatives with correct answer `C`, **when** alternatives
   are shuffled, **then** the reported answer letter points to the same content.
2. **Given** a legacy JSON school-year value, **when** it is parsed, **then**
   the normalized labels are returned.

### US3 — The owner can build the Windows executable with one command (P2)

**Acceptance scenarios**

1. **Given** the build dependencies, **when** the documented build command is
   run, **then** an executable is produced that starts and shows the Pix QR
   code in "Sobre".

### US4 — A teacher notices no difference (P1)

**Acceptance scenarios**

1. **Given** a bank created with v1.1, **when** it is opened with the new
   build, **then** all questions, categories and disciplines appear unchanged
   and every baseline requirement (BL-001 to BL-062) still holds.

## Requirements

- **FR-001** The source is organized as an importable package with a single
  entry point; the version number is no longer part of any file name.
- **FR-002** The application version is defined in exactly one place and shown
  in "Sobre".
- **FR-003** Runtime and development dependencies are declared in the
  repository with pinned versions.
- **FR-004** The repository ignores virtual environments, caches, build output
  and `.db` files.
- **FR-005** Version generation, school-year parsing/formatting, HTML fragment
  clean-up and equation markup are callable without Qt and have unit tests.
- **FR-006** The Pix QR image is a file asset, not source code.
- **FR-007** The executable build is a documented, repeatable command.
- **FR-008** The README's developer instructions match the repository.
- **FR-009** The release is identified by a git tag when released.

## Success criteria

- A new contributor reaches a running app and a green test run in under ten
  minutes using only the README.
- The source file that held the app shrinks by the ~700 lines of embedded image.
- No baseline requirement changes.

## Out of scope

Splitting the UI class, changing storage, fixing any known defect.

## Owner decisions

- Establish and document a new Windows PyInstaller command; the old command is unknown.
- All rights are reserved; no open-source license is granted.
- macOS is officially supported and tested before each release.
