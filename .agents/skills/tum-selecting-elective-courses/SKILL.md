---
name: tum-selecting-elective-courses
description: Plan TUM elective courses for the next official semester using the public TUMonline Degree Programs and course pages without login, match the student's degree program, read its dynamic curriculum categories and ECTS rules, and generate a private interactive weekly-calendar HTML file. Use for TUM course selection, next-semester timetable planning, curriculum-category credit checks, course conflict detection, or requests mentioning TUMonline, Degree Programs, Curriculum, Module Outline, electives, Stundenplan, Wahlfach, or Studiengang.
---

# TUM next-semester elective planning

Create a traceable, public-data-only next-semester plan without guessing curriculum facts or handling credentials.

## Workflow

1. Before asking anything else, ask: `是否需要每天 09:00 自动更新下一学期课程数据？` (or the equivalent in the conversation language).
   - If no, continue as a one-off run.
   - If yes, collect the program name and other required choices, then use the host platform's supported scheduled-task capability to create a **standalone recurring task/project** at 09:00 in the user's local timezone. Its prompt must invoke this Skill by name, use only public read-only TUMonline data, update the same local plan artifact, and report what changed. Never invent a scheduler or install an OS cron job. If the host has no scheduler, explain that recurrence is unavailable while continuing the one-off plan. Read [recurring-updates.md](references/recurring-updates.md) first.
2. Ask for the degree-program name.
3. Determine the current TUM semester from today's date and propose the next official semester. Ask the user to confirm or override it. Never silently substitute the current semester when next-semester offerings are unavailable.
4. Open a new dedicated TUMonline tab. Choose **Enter without login**, open **Degree Programs**, and match the program:
   - Accept an exact normalized match.
   - For one high-confidence candidate, ask exactly `是不是这个专业：{candidate}？` in Chinese or `Is this your degree program: {candidate}?` in English.
   - For ambiguity, show at most three candidates.
   - After rejection or no candidates, reply exactly `未检索到相关专业` for a Chinese conversation, or `No matching degree program was found.` for English.
5. Read the selected public Degree Program's visible curriculum tree, course-to-category membership, numeric ECTS rules, curriculum version, and any official Track/Technology-option structure. Do not assume any fixed taxonomy. If several curriculum versions are visible, ask the user to confirm the bracketed version instead of choosing the newest one. Use an official Module Outline only for fields absent from the public tree.
6. Collect actual offerings from **Courses**, not Degree Programs. Read [tumonline-courses.md](references/tumonline-courses.md) before interacting with the Courses page. Carry the visible `objTermId`, `orgId`, and `curriculumVersionId` through list pagination and details. Set Entries per page to 100 when the selector remains stable, follow the Next arrow until disabled, and require the visible total to equal the count of unique collected course IDs. A failed `catalog_audit` is a hard error, not a partial success. Mark detail pages as `published`, `unpublished`, or `unverified`; never call an unopened detail page “no time” and never fall back to older terms.
7. Normalize to `schemas/planner.schema.json`. Default every collected target-term course to selected unless the user explicitly requests otherwise (`default_selected: true`). Populate dynamic `tracks` only from Degree Program/module evidence; uncertain course-to-track mappings stay unassigned. Preserve registration state/window from the list or detail page. Use `aggregate_requirements` for rules spanning several real categories; never invent a fake category for a total-credit rule. Run `python3 scripts/build_calendar.py INPUT.json OUTPUT.html`. Verify that the font-size slider visibly changes all `rem`-based text and that every scheduled course has its complete title in the calendar or the scheduled-course summary.
8. Report the output path, unresolved classifications, conflicts, and source limitations.

## Browser and privacy rules

- Read [browser-and-privacy.md](references/browser-and-privacy.md) before opening TUMonline.
- Do not log in. If a page asks for credentials, stop and return to **Enter without login**.
- Never inspect or export cookies, storage, tokens, passwords, OTPs, grades, student IDs, email addresses, or personal study records.
- Keep requests user-triggered, sequential, and low-frequency. Read at most 100 list rows per page and open details only for relevant courses. Never build a bulk TUM dataset.

## Deterministic helpers

- Use `scripts/planner_core.py` for semester calculation, program-name matching, privacy filtering, and validation.
- Use `scripts/build_calendar.py` to produce the self-contained offline HTML.
- Use `examples/bioinformatics-ws-2026-27.json` for a public-only example with category and aggregate requirements.
- Use `examples/mmt-ws-2026-27.json` for the verified 106-row Management and Technology pagination/UI example. Its catalogue index is complete, but its course-detail coverage remains explicitly partial; do not treat heuristic or unverified track mappings as official evidence.
- Read [data-model.md](references/data-model.md) when creating or debugging normalized JSON.

The core workflow is platform-neutral: use any host's browser/navigation tools for the visible anonymous steps and any shell capable of Python 3 for deterministic scripts. Codex-specific UI metadata is optional and must not be required for one-off generation. The generated artifact is personal, non-commercial planning support, not an official degree audit. Information may be incomplete or wrong; TUMonline is authoritative. Preserve evidence URLs and timestamps for every material classification.
