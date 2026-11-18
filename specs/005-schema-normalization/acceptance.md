# Acceptance verification: Schema normalization

**Date**: 2026-11-18 | **Result**: Passed

The owner approved exhaustive automated comparison of the before/after bank
copies, combined with representative manual card and Word checks. No personal
bank was migrated, edited or copied into the repository during this audit.

## Bank identity and counts

| Copy | Schema | Actual question count | Highest question ID |
|---|---|---|---|
| `biologia_ANTES.db` | 3 | 2,597 | 2605 |
| `biologia_TESTE_005.db` | 5 | 2,600 | 2609 |

The owner's initial count was the highest ID, which is different from the row
count because IDs have gaps. All 2,597 original IDs remain present. The after
copy has three additional test questions: 2607, 2608 and 2609.

SHA-256 of the audited inputs:

- Before: `dbfdccd42de2127597b4672b4d3269fc8fc93623c8758f4fa2005e5b0fdf3c02`
- After: `20427d6923050964c5894fe4af1f1884f45ebbe1f9b7f59e08ae58d5ea4ff2fd`

Both file hashes were unchanged at the end of the audit. SQLite connections
used `mode=ro`, `PRAGMA query_only=ON`, and read transactions.

## Automated comparison

Every original question was compared against the normalized data using explicit
expected legacy-to-code mappings and the specified year/category semantics.
Checks covered rich statements, searchable plain text, type, difficulty,
category IDs, segments, school years, ordered alternatives and correct flags,
expected answers, source, numeric and raw source years, timestamps and the
alternative-order flag. All 149 category IDs, names and parent links match.
Every original archived row also matches its before-bank row exactly.

The only active-record differences are on question 2605. The owner confirmed
editing and saving this question during manual verification. Its rich statement
was serialized as Qt HTML, its unused multiple-choice expected-answer field
changed from NULL to an empty string, and its modification timestamp was set.
The statement's visible text and image payload remain unchanged. These changes
also produce identical exam and answer-key documents.

The question-card presenter was exercised for all original IDs, with no errors
and matching statement, alternatives and answer content. This is a data-boundary
check; the owner supplied the visual card checks below.

For every original ID, the existing legacy reader and normalized reader each
fed the current document exporter, generating one exam and one separate answer
key in memory. All 2,597 document pairs match exactly in body XML, footer XML,
and embedded image bytes. No export error or acknowledged missing-image bypass
occurred. The original rich fields contain 1,230 image references across 1,014
questions. This verifies stored document structure and embedded assets; it
does not replace the owner's visual inspection in Word.

Both input banks returned `ok` from SQLite `integrity_check`, with no
`foreign_key_check` violations.

## Upgrade report

The only reported item is question 24, difficulty `Baixa`. That exact value is
already present in the before bank. It is outside the defined mapping of
`Fácil`, `Médio`, and `Difícil`, so the normalized difficulty is NULL, the raw
value remains in the retained original row, and the upgrade report identifies
it. The complete report matches the independently expected unmappable values.
No guessed difficulty was assigned. The owner can choose a supported difficulty
when reviewing this question; this is data cleanup, not a migration defect.

## Owner verification and regression evidence

The owner reported completing the manual checklist, inspecting IDs 1, 108 and
120, and passing editing/categories/search, shuffled answer keys, reopening and
backup checks. No Word differences were reported. The owner also confirmed the
manual edit of question 2605 when the automated comparison identified it.

The previous review passed all 317 automated tests. Python application and test
sources are unchanged since that run; this acceptance follow-up changes only
documentation. Existing normalized schema-4/schema-5 coverage includes migration
recovery and rollback, category refresh, editing, pagination, selection,
source-year filtering and exports with two to five alternatives.

Spec 005 acceptance is complete for the supplied biology bank. This result does
not claim that other, unaudited personal banks were compared. Spec 006 can be
planned and implemented next; committing, merging and release packaging remain
separate work.
