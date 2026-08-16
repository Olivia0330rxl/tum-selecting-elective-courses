#!/usr/bin/env python3
"""Build the verified 106-row MMT WS 2026/27 public-course example."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OBSERVED = "2026-08-16T19:00:00+08:00"
COURSES_URL = "https://campus.tum.de/tumonline/ee/ui/ca2/app/desktop/#/slc.tm.cp/student/courses"
PROGRAM_URL = "https://www.mgt.tum.de/de/programs/graduate-programs/master-in-management-technology"

ROWS = r"""
950943786|Course 0000005567 (title truncated in TUMonline list)|0000005567|No registration procedures for this course
950942887|Advanced Analytical Techniques (CH4115)|0000004763|No registration procedures for this course
950940783|Advanced Computer Architecture (IN2076)|0000002972|No registration procedures for this course
950944676|Advanced Concepts of Programming Languages (CIT3230000)|0000001928|No registration procedures for this course
950976463|Advanced Environmental and Natural Resource Economics - Lecture (WZ2757, English)|WZ002757VL|No registration procedures for this course
950976464|Advanced Environmental and Natural Resource Economics - Seminar (WZ2757, English)|WZ002757SE|No registration procedures for this course
950942688|Advanced Practical Course - Developing innovative services at the example of SAP technologies (IN2128, IN2106, IN212802)|0000000486|No registration procedures for this course
950942111|Advanced Seminar - Digital Transformation (IN2107, IN2396, IN4831)|0000001359|No registration procedures for this course
950944204|Advanced Seminar Economics & Policy (MGT001313, English): Productivity, Efficiency and Risk (Limited Places)|MGT001313S|No registration procedures for this course
950942355|Advanced Topics of SW Engineering (IN2309, IN2126)|0000000521|No registration procedures for this course
950940088|Analytical Chemistry (CH0107)|0820046473|No registration procedures for this course
950942596|Applied Statistics and Econometrics (WZ1705, English)|WZ001705UE|No registration procedures for this course
950942597|Applied Statistics and Econometrics (WZ1705, English)|WZ001705VO|No registration procedures for this course
950941480|Automatic Control - Revision Course|0000000710|Registration possible from 28.08.2026
950941215|Basic Principles: Operating Systems and System Software, Exercise Session (IN0009)|0000004057|No registration procedures for this course
950941216|Basic Principles: Operating Systems and System Software, Exercise Session (IN0009)|0000003531|No registration procedures for this course
950940769|Basic Principles: Operating Systems and System Software (IN0009)|0240984991|Registration possible from 07.09.2026
950942804|Basics of Electrical Energy Storage|0000002649|Registration possible from 01.09.2026
950942803|Basics of Electrical Energy Storage|0000002515|Registration possible from 01.09.2026
950940859|Basics of Physical Chemistry 1, Exercise (CH1091/CH7201)|0249985413|No registration procedures for this course
950942800|Batteriespeicher|0000002949|Registration possible from 01.09.2026
950942799|Batteriespeicher|0000002687|Registration possible from 01.09.2026
950940666|Biochemistry, Exercises (CH4117)|0240869707|No registration procedures for this course
950940350|Biological Chemistry and Biochemistry (CH4117)|0240048948|No registration procedures for this course
950940083|Biology for Chemists (CH0106)|0220039141|No registration procedures for this course
950946239|Bioprocess Engineering|0000002444|No registration procedures for this course
950945095|Central Exercise: Advanced Topics of Software Engineering (IN2309, IN2126)|0000001455|No registration procedures for this course
950941433|Clinical Applications of Computational Medicine|0000002166|Course open for registration
950944893|Cloud Information Systems (CIT3230002)|0000001259|No registration procedures for this course
950942443|Communication Acoustics|0000001090|No registration procedures for this course
950941680|Communication Networks|0000000736|Registration possible from 09.09.2026
950943345|Construction Chemicals and Materials 1 - Inorganic Binders (CH3151a)|0000001548|No registration procedures for this course
950943407|Construction Chemicals and Materials 1 - Inorganic Binders (CH3151b)|0000002474|No registration for this course
950940552|Construction Chemicals 1|0240680849|No registration procedures for this course
950943408|Construction Chemistry 1 (CH3153b)|0000002527|No registration for this course
950942369|Data Analysis and Visualization in R (IN2339)|0000000283|No registration procedures for this course
950942275|Data Driven Innovation|0000004113|No registration for this course
950942274|Data Driven Innovations|0000000610|No registration procedures for this course
950943770|Data Networking|0000005128|Registration possible from 09.09.2026
950945315|Development of Wind Energy Projects|0000004972|No registration procedures for this course
950944540|Development of Wind Energy Projects|0000002273|No registration procedures for this course
950942466|Econometric Impact Analysis (WZ1564, English)|WZ001564VO|No registration procedures for this course
950944718|Exercise - Advanced Concepts of Programming Languages (CIT3230000)|0000000275|No registration procedures for this course
950942618|Exercise Course to Materials Sciences (MS&E)|0000000519|No registration procedures for this course
950952069|Extended Reality for Value Creation for Businesses (MGT001523, English) (Limited places)|MGT001523S|unknown
950944516|Fundamentals of Artificial Intelligence (IN2406)|0000001604|No registration procedures for this course
950940741|Fundamentals of Databases (IN0008)|240952278|No registration procedures for this course
950940868|Fundamentals of Physical Chemistry 1 (CH1091/CH7201)|0249997741|No registration procedures for this course
950940462|General and Inorganic Chemistry (CH6202a)|0240392020|No registration procedures for this course
950940495|General and Inorganic Chemistry, Exercises (CH6202b)|0240503265|No registration procedures for this course
950944543|Hydrogen Mobility|0000002291|No registration procedures for this course
950940071|Industrial Chemical Processes 1 - Catalysis for Energy (CH3094)|0220022816|No registration procedures for this course
950940825|Industrial Energy Economy|0249943827|Registration possible from 01.09.2026
950942663|Inorganic Solid State and Organometallic Chemistry (CH4107)|0000001997|No registration procedures for this course
950942664|Inorganic Solid State and Organometallic Chemistry (CH4107)|0000002004|No registration procedures for this course
950941519|Inside my iPhone - Technology analysis of a smart phone|0000000667|Registration possible from 23.09.2026
950943633|Interdisciplinary Project X|0000004924|No registration procedures for this course
950941668|Introduction in Flight System Dynamics and Flight Control|0000000308|Registration possible from 17.08.2026
950941669|Introduction in Flight System Dynamics and Flight Control|0000000310|Registration possible from 17.08.2026
950940683|Introduction into Computer Science (for non Informatics studies, TUM BWL) (IN8005)|0240905438|No registration procedures for this course
950940728|Introduction to Computer Architecture (IN0004)|240941859|No registration procedures for this course
950942542|Introduction to Deep Learning (IN2346)|0000000673|Course open for registration
950944691|Introduction to Programming (CIT5230000)|0000003492|No registration procedures for this course
950944511|IT Sicherheit (IN0042)|0000001429|Course open for registration
950944804|Lab Energy Informatics|0000004541|Registration possible from 01.09.2026
950945441|Machine Learning in Energy Management|0000001114|Registration possible from 01.09.2026
950941862|Materials and Process Technologies for Carbon Composites|0000001599|No registration procedures for this course
950941863|Materials and Process Technologies for Carbon Composites|0000001672|No registration procedures for this course
950942617|Materials Sciences (MS&E)|0000000459|No registration procedures for this course
950944791|Molecular Medicine (CH0226)|0000004125|No registration procedures for this course
950941777|Nanosystems|0000002663|Course open for registration
950940120|Network Planning|0820092070|Registration possible from 09.09.2026
950940686|Network Security (IN2101)|240905670|No registration procedures for this course
950941618|Pharmaceutical Radiochemistry 1 (CH3301)|0000003432|No registration procedures for this course
950944544|Piston Engines 1|0000002297|No registration procedures for this course
950943286|(POL60102) Science Communication and Public Engagement|0000004522|No registration procedures for this course
950941206|(POL70044) Business Ethics|0000003707|No registration procedures for this course
950977628|(POL700450) Master Seminar Business Ethics|0000002432|No registration procedures for this course
950943932|(POL7004511) Master Seminar Business Ethics|0000005656|No registration procedures for this course
950941541|Practical Course - Designing IT-based Learning (IN0012, IN4138)|0000002163|No registration procedures for this course
950942985|Practical Course - Internet Lab - IlabX (IN0012, IN2106, IN4240)|0000001334|unknown
950940279|Practical Course - iPraktikum, iOS Praktikum (IN0012, IN2106, IN2175, IN2128, IN4049)|0821025259|No registration procedures for this course
950942931|Praktikum - Interactive Learning (IN0012, IN2106, IN2175, IN4234)|0000003696|No registration procedures for this course
950945839|Project Course Health Economics|MHP0001201|Course open for registration
950941072|Project: Economic aspects of Nanotechnology|0000000555|Course open for registration
950940322|Reactivity of Organic Compounds (CH0115)|0240010051|No registration procedures for this course
950940317|Reactivity of Organic Compounds, Exercises (CH0115)|0240006609|No registration procedures for this course
950941141|Real-Time Systems, Exercise Session (IN2060)|0000001018|No registration for this course
950940755|Real-Time Systems (IN2060)|0240965614|No registration procedures for this course
950943138|Risk Theory and Modeling - Exercises (WZ0043, English)|WZ000043UE|No registration procedures for this course
950943137|Risk Theory and Modeling - Lecture (WZ0043, English)|WZ000043VO|No registration procedures for this course
950940690|Robotics (IN2067)|240911148|No registration procedures for this course
950943470|Scientific Seminar on Energy Economy and Application Technology|0000005232|Registration possible from 01.09.2026
950974596|Seminar - Behavioral Insights in the Age of Big Data (IN0014, IN2107, IN2396, IN4424)|0000005412|unknown
950942622|Seminar - Security and Privacy Economics (IN0014, IN2107, IN2396, IN4892)|0000000437|unknown
950943829|Seminar Health Care Management|MH16002401|Course open for registration
950941404|Software Engineering in Industrial Practice (IN2235)|0240917954|Registration possible from 30.08.2026
950941937|Sponsorship-linked marketing (online-course)|MHV0001301|Course open for registration
950941938|Sponsorship-linked marketing (online-Kurs)|MHV0001302|Course open for registration
950944598|Strategic IT Management (CIT4230000)|0000001839|Registration possible from 30.08.2026
950946161|Sustainability in Automotive Engineering|0000001707|No registration procedures for this course
950944538|Sustainable Mobile Drivetrains|0000002254|No registration procedures for this course
950945390|Sustainable production engineering and product development|0000000232|Registration possible from 30.08.2026
950941969|Think.Make.Start.|0000000509|No registration procedures for this course
950941666|Uncertainty Modeling in Engineering (Vorlesung + Übung)|0000002843|No registration procedures for this course
950940053|Water Chemistry I (CH1062)|0820005191|No registration procedures for this course
""".strip()


TRACK_SPECS = [
    ("management", "Management electives", "Management"),
    ("informatics", "Informatics", "Technology option"),
    ("chemistry", "Chemistry", "Technology option"),
    ("electrical", "Electrical & Information Technology", "Technology option"),
    ("mechanical", "Mechanical Engineering", "Technology option"),
    ("computer-engineering", "Computer Engineering", "Technology option"),
    ("industrial", "Industrial Engineering", "Technology option"),
    ("sustainable-energies", "Sustainable Energies", "Technology option"),
]


def source(kind: str, label: str, url: str) -> dict:
    return {"kind": kind, "label": label, "url": url, "observed_at": OBSERVED}


def registration(label: str) -> dict:
    if label == "Course open for registration":
        return {"status": "open", "opens_at": None, "closes_at": None, "label": label}
    match = re.search(r"Registration possible from (\d{2})\.(\d{2})\.(\d{4})", label)
    if match:
        day, month, year = match.groups()
        return {"status": "upcoming", "opens_at": f"{year}-{month}-{day}", "closes_at": None, "label": label}
    if label.lower().startswith("no registration"):
        return {"status": "none", "opens_at": None, "closes_at": None, "label": label}
    return {"status": "unknown", "opens_at": None, "closes_at": None, "label": None}


def track_ids(title: str, number: str) -> list[str]:
    text = f"{title} {number}".lower()
    result: list[str] = []
    if re.search(r"\b(mgt|pol|mh|econom|business|marketing|management|innovation|sponsorship|ethics)", text):
        result.append("management")
    if re.search(r"\b(in\d|cit\d|software|database|programming|informatics|deep learning|machine learning|robotics|it sicherheit)", text):
        result.extend(["informatics", "computer-engineering"])
    if re.search(r"\b(ch\d|chem|biochem|molecular medicine|radiochemistry|catalysis)", text):
        result.append("chemistry")
    if re.search(r"electrical|communication|network|control|acoustic|energy informatics", text):
        result.append("electrical")
    if re.search(r"automotive|drivetrain|flight|piston|production engineering|carbon composites|materials science", text):
        result.append("mechanical")
    if re.search(r"industrial|production|project|value creation|process", text):
        result.append("industrial")
    if re.search(r"energy|battery|batteries|wind|hydrogen|sustainable", text):
        result.append("sustainable-energies")
    return list(dict.fromkeys(result))


def main() -> None:
    rows = [line.split("|", 3) for line in ROWS.splitlines()]
    program_source = source("public_course", "TUMonline Courses — Management and Technology [20251], Master of Science", f"{COURSES_URL}?curriculumVersionId=5386&objTermId=207&orgId=1")
    track_source = source("public_degree_programme", "TUM School of Management — MMT management specializations and technology options", PROGRAM_URL)
    categories = [
        {"id": "management", "label": "Management", "min_ects": None, "max_ects": None, "color": "#007C91", "source": track_source},
        {"id": "technology", "label": "Technology", "min_ects": None, "max_ects": None, "color": "#D97706", "source": track_source},
        {"id": "unresolved", "label": "Track mapping pending", "min_ects": None, "max_ects": None, "color": "#64748B", "source": program_source},
    ]
    courses = []
    for course_id, title, number, registration_label in rows:
        mapped_tracks = track_ids(title, number)
        category_id = "management" if "management" in mapped_tracks else ("technology" if mapped_tracks else "unresolved")
        meetings = []
        schedule_status = "unverified"
        if course_id == "950945390":
            schedule_status = "published"
            meetings = [
                {"day": 2, "start": "10:00", "end": "12:00", "type": "course meeting", "location": None, "weeks": "2026-10-13 to 2027-02-02"},
                {"day": 4, "start": "12:00", "end": "13:00", "type": "course meeting", "location": None, "weeks": "2026-10-15 to 2027-02-04"},
            ]
        groups = [{"id": f"{course_id}-published", "label": "Published dates", "meetings": meetings}] if meetings else []
        courses.append({
            "id": course_id,
            "module_code": None,
            "title": title,
            "ects": None,
            "category_id": category_id,
            "track_ids": mapped_tracks,
            "term": "WS-2026-27",
            "term_id": 207,
            "status": "candidate",
            "selected_group_id": groups[0]["id"] if groups else None,
            "session_groups": groups,
            "schedule_status": schedule_status,
            "registration": registration(registration_label),
            "source": source("public_course", f"TUMonline course {course_id} — target-term list row", f"{COURSES_URL}/{course_id}"),
        })
    plan = {
        "schema_version": "1.0",
        "planning_term": {"current": {"code": "SS-2026", "label": "Summer Semester 2026", "term_id": None}, "target": {"code": "WS-2026-27", "label": "Winter Semester 2026/27", "term_id": 207}, "method": "next_official_tum_semester", "derived_from": "2026-08-16"},
        "program": {"name": "Management and Technology", "degree": "Master of Science", "curriculum_version_id": 5386, "source": program_source},
        "default_selected": True,
        "catalog_audit": {"visible_total": 106, "collected_count": 106, "page_size": 100, "pages_read": 2, "pagination_exhausted": True, "course_ids": [row[0] for row in rows]},
        "categories": categories,
        "tracks": [{"id": item[0], "label": item[1], "group": item[2], "source": track_source} for item in TRACK_SPECS],
        "aggregate_requirements": [],
        "courses": courses,
        "offerings_status": "partial",
        "offerings_message": "Course index complete (106/106). One Dates and Groups detail was verified; remaining course details are explicitly marked unverified, not unpublished. Track buttons demonstrate the interaction, but per-course assignments inferred from titles/module codes must be replaced with Degree Program curriculum-tree evidence before publication.",
        "conflicts": [],
        "generated_at": OBSERVED,
    }
    output = ROOT / "examples" / "mmt-ws-2026-27.json"
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
