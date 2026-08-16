# TUMonline Courses: verified anonymous workflow

Use Degree Programs for the curriculum tree and category rules. Use **Courses** for real term offerings, course IDs, teaching types, registration state, dates, groups, locations, and descriptions.

## State and URL parameters

Open `https://campus.tum.de/tumonline/`, choose **Continue without login**, then open **Courses**. Treat the selected controls as authoritative and record the hash URL only after the UI settles.

- `objTermId`: semester ID used by the UI. Verified on 2026-08-16: `207` displays `2026 W` / Winter semester 2026/27.
- `orgId`: selected organisation. `1` displays Technische Universität München.
- `curriculumVersionId`: internal ID created after selecting a Curriculum option. It is not the bracketed curriculum year/version shown to users.
- `q`: course number/title/person search text. It intersects with the selected curriculum; a global result can disappear after the curriculum is applied.
- `$top`: page size; the UI supports 20, 50, and 100.
- `$skip`: zero-based result offset. For 100-row pages use 0, 100, 200, and so on; also verify the visible range text and Next-page state.

Never assume these example IDs generalize. Select controls visibly for every run, then read the resulting URL and labels.

## Interaction order and state reset

The hash URL is not a reliable cold-start API. On a fresh page, directly supplied `curriculumVersionId` may be cleared during SPA initialization. Changing the Entries-per-page control may also reset Curriculum to **All**.

Use this order:

1. Select the target term and verify its label and `objTermId`.
2. Select organisation and verify its label and `orgId`.
3. Set Entries per page to 100 by clicking the Material combobox and choosing option `100` (it is not a native `<select>`).
4. Open Curriculum, choose the exact confirmed program/version, wait for results, and verify both the displayed selection and non-empty `curriculumVersionId` in the URL.
5. After every page-size, term, organisation, search, sort, or page change, re-check all three selectors and the URL. If Curriculum became All or the ID became empty, reselect it before reading rows.

If the Curriculum option cannot be restored after selecting 100, keep the verified Curriculum and use the working 20- or 50-row size. Page size is a performance optimization, not permission to drop the curriculum filter. Never read the visible `1 - 100 from 2564` global result as program-filtered data.

Do not use a direct REST call without the anonymous SPA context as the primary workflow. The browser session establishes the public state needed by the page.

## Course list and detail extraction

- Before accepting a catalogue, record a `catalog_audit`: visible result total, unique collected course-ID count, requested page size, visited offsets, and whether Next is disabled on the last page. Validation must fail unless `visible_total == collected_count` and pagination is exhausted.
- Deduplicate list rows by the numeric course ID in `/slc.tm.cp/student/courses/{courseId}`, not by title or module code. Lecture and exercise rows can share a module code but have different course IDs and schedules.
- Preserve every course ID as source evidence, then normalize lecture, exercise, term-paper, and other components belonging to one official module into one planner `Course`. Attach component schedules to that module's session groups and count module ECTS once.
- Open details only for relevant candidates. Verify `Offered in` exactly matches the target semester.
- Extract title, course number, teaching type, SWS, language, description, dates/groups, weekday, start/end, date range, and location.
- Read **Status within Curriculum** as additional evidence, but do not assume it lists every mapping shown by the list filter.
- Preserve the registration label shown in the list or detail, including open-now, a future registration start date, or no registration procedure. Display it both on course cards and calendar events.
- Use three schedule states: `published` when Dates and Groups has extracted meetings, `unpublished` only when the opened detail explicitly says no fixed time, and `unverified` when the detail was not opened. Unverified courses belong in a separate “detail verification pending” area, never under “no time published”.
- Course detail can show `ECTS credits: -`. In that case take ECTS from the linked official module/curriculum evidence and store both sources; never convert SWS to ECTS.
- Do not collect lecturer contact data. Names visible on a course are not needed in the planner model.

## Verified Bioinformatics example

Observed anonymously on 2026-08-16:

- Confirmed curriculum label for the complete FPSO-2021 catalogue run: `Bioinformatics [20161], Master of Science`
- `curriculumVersionId=4564`, `objTermId=207`, `orgId=1`
- Pagination returned `1 - 20 from 22`, then `21 - 22 from 22` with `$skip=20&$top=20`; both pages retained the curriculum, term, and organisation parameters.
- The 22 TUMonline course rows normalize into 17 planner module candidates because IN2379, IN2309, CIT4230001, IN2230, and ME2648 each have two course components whose ECTS must not be counted twice.
- Example detail: `Advanced Data Handling and Visualization Techniques (IN2379)`, lecture course ID `950943958`; exercise course ID `950943959` is retained as component evidence.
- Detail: Winter semester 2026/27; lecture; English; Friday 10:00–12:00; 2026-10-16 through 2027-02-05; room `00.13.009A, Seminarraum (5613.EG.009A)`
- Course ECTS is `-`; the official Bioinformatics module catalogue supplies 6 ECTS.

Curriculum options are query-dependent. A different run displayed `Bioinformatics [20261], Master of Science` with internal ID `5455`, but this is not sufficient evidence that it is the student's applicable FPSO or that it exposes the complete target catalogue. Clear `q` before final program selection, and when multiple Master curriculum versions exist, ask the user to confirm the visible bracketed version instead of choosing the numerically newest one. Internal IDs must always be read from the settled UI URL and never inferred from bracketed labels.

## Verified Management and Technology pagination example

Observed anonymously on 2026-08-16 for `Management and Technology [20251], Master of Science`:

- `curriculumVersionId=5386`, `objTermId=207`, `orgId=1`, `$top=100`
- Page 1 showed `1 - 100 from 106`; page 2 showed `101 - 106 from 106`; the final Next arrow was disabled.
- The audit therefore collected 106 unique course IDs from a visible total of 106. The second-page IDs were `950946161`, `950944538`, `950945390`, `950941969`, `950941666`, and `950940053`.
- Example detail course `950945390`, *Sustainable production engineering and product development*, showed registration possible from 30.08.2026 and meetings Tuesday 10:00–12:00 (13.10.2026–02.02.2027) and Thursday 12:00–13:00 (15.10.2026–04.02.2027).
- Other details in the demo remain `unverified`; the complete 106-row index must not be misrepresented as complete schedule extraction.

The same public selector showed multiple curriculum versions (`[20101]`, `[20171]`, `[20181]`, `[20221]`, `[20231]`, `[20251]`). Always ask which version applies.
