# Daily 09:00 recurring updates

- The recurrence question is the Skill's first user-facing question.
- Create nothing until the user explicitly answers yes and the degree program and target-term behavior are known.
- Use the host platform's documented recurring-task feature to create a standalone scheduled task/project at 09:00 in the user's local timezone. On Codex, use its automation tool. On another platform, use only an equivalent first-party capability that is actually available. Do not write raw directives or install an OS cron/launch agent.
- The scheduled prompt must invoke `$tum-selecting-elective-courses`, name the confirmed program, choose Enter without login, enforce next-semester-only filtering, use public read-only pages, update the same normalized JSON and HTML paths, and summarize additions, removals, schedule changes, and unresolved data.
- If scheduling is unavailable, explain that the one-off planner still works and do not simulate recurrence or block the rest of the Skill.
- Each recurring run remains low-frequency: at most 100 rows per page, relevant details only, no bulk cache, login, enrollment, messages, or background scraping beyond the scheduled user-authorized run.
