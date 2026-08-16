# TUM selecting elective courses

A local-first, platform-neutral Agent Skill that plans **the next TUM semester**, maps electives to program-specific curriculum categories, and generates a self-contained interactive weekly calendar.

The category model is dynamic: it does not assume Methodology, Technology, Management, or any fixed number of requirement groups.

## What it does

- Matches a degree program using the public TUMonline Curriculum selector.
- Derives the next official semester and refuses to mix in current or historical offerings.
- Starts by asking whether to create a standalone daily 09:00 update task.
- Uses **Enter without login → Degree Programs** for the category tree and ECTS rules, then **Courses** for real target-semester offerings, schedules, teaching groups, and details.
- Supports both per-category credit rules and aggregate rules spanning several real categories.
- Verifies catalogue pagination against TUMonline's visible total (including 100-row pages and the final Next state).
- Generates an offline HTML planner with all courses selected by default, dynamic Track filters, individual/bulk deselection, registration badges, section choices, unscheduled/unverified areas, and time-conflict detection.
- Provides working whole-page font scaling, complete scheduled-course titles, and a 50–200% weekly-calendar width control (70% default); it deliberately omits a Credit Progress panel.
- Requires no TUM login and never handles credentials.

## Quick start

Invoke `tum-selecting-elective-courses` from any Agent Skills-compatible host, or build the included example directly:

```bash
python3 scripts/build_calendar.py examples/sample-plan.json tum-next-semester-plan.html
python3 scripts/build_calendar.py examples/bioinformatics-ws-2026-27.json output/bioinformatics-ws-2026-27.html
python3 scripts/build_mmt_example.py
```

Open `tum-next-semester-plan.html` or a generated file under `output/` in a browser. Do not open `assets/weekly-calendar/template.html` as the finished planner: it contains build placeholders and is not a standalone preview. No server, CDN, analytics, or network access is required after generation.

Useful deterministic commands:

```bash
python3 scripts/planner_core.py next-term --date 2026-08-16
python3 scripts/planner_core.py match-program "Management and Digital Technology" programs.json
python3 -m unittest discover -s tests -v
```

## Platform support

The core does not depend on Codex APIs: it uses Markdown Skill instructions, Python 3 standard-library scripts, JSON Schema, and self-contained HTML/CSS/JavaScript without CDN or telemetry. Clone the whole repository, open its root as the host workspace, and register `.agents/skills/tum-selecting-elective-courses` using that host's documented Agent Skills mechanism. Keep `scripts`, `schemas`, and `assets` in their repository-relative locations.

Daily 09:00 recurrence is optional. Codex can create a scheduled task through its automation feature; other hosts should use an equivalent documented scheduler if present. If scheduling or browser control is unavailable, the one-off workflow and deterministic JSON-to-HTML builder still work.

## Data and privacy

The v1 workflow is anonymous and public-only. It chooses **Enter without login**, reads the selected public Degree Program, and does not open My Studies. It never reads or stores passwords, MFA codes, cookies, tokens, grades, student IDs, or contact details.

Public lookups must be low-frequency and user-triggered. This project does not mirror TUMonline or republish a TUM course dataset. Repository code and original templates are available only under the [Personal Non-Commercial License](LICENSE); this is not an OSI-approved open-source license. It does not license TUM content, data, names, or marks.

Relevant TUM guidance:

- [Handling TUM credentials](https://www.it.tum.de/it/sicher/weitergabe-zugangsdaten/)
- [TUM IT policies](https://www.it.tum.de/it/information-hilfe/richtlinien/)
- [TUM data protection](https://www.datenschutz.tum.de/)

This is personal, non-commercial planning support, not an official degree audit or legal advice. Information can be incomplete, outdated, or incorrect; **TUMonline and applicable official TUM documents are authoritative**.

## 中文说明

本项目帮助 TUM 学生规划**下一学期**的选修课，并生成完全离线的交互式周课表。课程大类与学分要求来自学生自己的培养方案，不固定为三种分类。

Skill 的第一个问题是“是否需要每天 09:00 自动更新下一学期课程数据？”。之后询问专业名称并确认下一学期，再通过 **Enter without login → Degree Programs** 读取培养方案树与学分要求，通过 **Courses** 获取真实的目标学期课程、时间和教学班。整个 v1 流程无需登录，也不接触密码、MFA、Cookie、成绩、学号或邮箱。

如果下一学期课程尚未发布，页面会明确显示“课程尚未开放”，不会用当前学期课程替代。

本项目仅限个人、非商业使用。信息可能不完整、过期或有误，一切以 TUMonline 和适用的 TUM 官方文件为准。核心生成器只依赖 Python 3 标准库和浏览器原生 HTML/CSS/JavaScript；其他支持 Agent Skills 的平台可以运行一次性流程，定时更新能力则按平台是否提供调度功能自动降级。
