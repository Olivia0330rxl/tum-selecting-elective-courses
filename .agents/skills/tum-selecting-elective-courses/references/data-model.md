# Planner data model

The canonical schema is `schemas/planner.schema.json` at the repository root.

## Required invariants

- `schema_version` is `1.0`.
- `planning_term.target` is the next semester unless the user explicitly overrides it.
- Every course `term` and non-null `term_id` matches the target term.
- Category IDs are arbitrary stable strings. Never encode assumptions about the number or names of categories.
- `aggregate_requirements` expresses a numeric rule spanning multiple real category IDs; it is not itself a category.
- `category_id: null` means unresolved, not a general-elective category.
- Only `planned` and `enrolled` courses contribute ECTS to progress.
- Multiple session groups for one course never multiply its ECTS.
- A session group may contain several meetings, such as a lecture plus tutorial.
- Every material classification includes a `source` with `kind`, `label`, optional `url`, and `observed_at`.
- Use a course's optional `evidence` array when offering/schedule and ECTS/category come from different public pages.
- `catalog_audit` proves list completeness independently of later module normalization: visible total, collected unique raw course IDs, page size, offsets, and exhausted-pagination state must agree.
- `default_selected: true` means every target-term course initially participates in the local calendar; users remove courses individually or deselect the currently visible Track/filter result.
- `tracks` are dynamic program structures. A course can reference several `track_ids`, but uncertain mappings remain empty rather than inferred.
- `schedule_status` distinguishes `published`, `unpublished`, and `unverified`; only `published` can contain extracted meetings.
- `registration` carries a normalized state plus the original public label and optional start/end timestamps.

## Status values

- `candidate`: visible for consideration but not counted.
- `planned`: selected in the generated planner and counted.
- `enrolled`: already present for the target semester and counted.

## Source precedence

Use the selected anonymous TUMonline Degree Program, then an official Module Outline for fields absent from the public tree, then explicit manual confirmation. Retain disagreeing evidence in `conflicts`; do not log in to resolve it.

## Privacy

Do not include names, student IDs, email addresses, grades, examination results, credentials, tokens, cookies, or raw authenticated-page dumps. The builder recursively removes prohibited key names as a second line of defense; source collection must still minimize data before writing JSON.
