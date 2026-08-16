# Public browser and privacy workflow

## Anonymous Degree Programs flow

1. Open a new dedicated tab at `https://campus.tum.de/tumonline/` and choose **Enter without login**.
2. Open **Degree Programs** and select the confirmed program. Use it for the curriculum tree, labels, credit rules, version, and module/category mappings—not for real semester offerings.
3. Open **Courses** for actual offerings and details. Follow [tumonline-courses.md](tumonline-courses.md), visibly select the target term, organisation, 100-row page size, then Curriculum, and record `objTermId`, `orgId`, and `curriculumVersionId`; never guess or reuse identifiers.
4. Request at most 100 rows per page. Continue only while relevant target-semester results remain, deduplicate by stable identifier, and open details only for shortlisted courses.
5. Record public URL, observation time, target term, and curriculum version. Do not collect teacher contact details.

## Conflict and failure behavior

- Do not log in. If anonymous navigation is unavailable, report the limitation instead of requesting credentials.
- Prefer the selected public Degree Program; use an official Module Outline only for missing fields and show both sources when values conflict.
- Do not invent category membership, ECTS, schedules, term IDs, or curriculum versions.
- If a category cannot be evidenced, set `category_id` to `null` and display it as unclassified.
- If next-semester offerings are unpublished or cannot be verified, set `offerings_status` to `unavailable`, leave `courses` empty, and do not substitute the current term or generic module catalogue.
- Never enroll, deregister, bookmark, message, or submit a form.

## Legal and operational boundary

The repository's original code and templates use the Personal Non-Commercial License in `LICENSE`; TUM data and marks are not licensed by the repository. Generated plans are for personal, non-commercial use only. Information may be incomplete, outdated, or incorrect, and TUMonline plus applicable official TUM documents are authoritative. This workflow is local, read-only, user-triggered planning support and is not legal advice. Follow TUM's password guidance, IT rules, data-protection information, and any updated TUMonline terms.
