from __future__ import annotations

import copy
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_calendar import build  # noqa: E402
from planner_core import (  # noqa: E402
    PlannerValidationError,
    current_term,
    load_and_prepare,
    match_program,
    next_term,
    paginate_results,
    planning_terms,
    sanitize_personal_data,
    validate_plan,
)


class TermTests(unittest.TestCase):
    def test_summer_advances_to_same_year_winter(self):
        result = planning_terms(dt.date(2026, 8, 16))
        self.assertEqual(result["current"]["code"], "SS-2026")
        self.assertEqual(result["target"]["code"], "WS-2026-27")

    def test_winter_advances_to_next_year_summer(self):
        result = planning_terms(dt.date(2027, 2, 1))
        self.assertEqual(result["current"]["code"], "WS-2026-27")
        self.assertEqual(result["target"]["code"], "SS-2027")

    def test_boundary_dates(self):
        self.assertEqual(current_term(dt.date(2026, 3, 31)).code, "WS-2025-26")
        self.assertEqual(current_term(dt.date(2026, 4, 1)).code, "SS-2026")
        self.assertEqual(current_term(dt.date(2026, 9, 30)).code, "SS-2026")
        self.assertEqual(current_term(dt.date(2026, 10, 1)).code, "WS-2026-27")

    def test_invalid_term_kind(self):
        with self.assertRaises(ValueError):
            next_term(type("FakeTerm", (), {"kind": "spring", "start_year": 2026})())


class MatchTests(unittest.TestCase):
    def setUp(self):
        self.programs = [
            {"name": "Management and Digital Technology (M.Sc.)", "id": "mmdt"},
            {"name": "Management and Technology (M.Sc.)", "id": "mt"},
            {"name": "Information Systems (M.Sc.)", "id": "is"},
        ]

    def test_exact_normalized_match(self):
        result = match_program("Management & Digital Technology", self.programs)
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["candidate"]["id"], "mmdt")

    def test_unique_suggestion(self):
        result = match_program("Managment Digital Technolgy", self.programs)
        self.assertEqual(result["status"], "suggest")
        self.assertEqual(result["candidate"]["id"], "mmdt")

    def test_ambiguous_candidates_are_capped(self):
        programs = [f"Computational Science {letter}" for letter in "ABCDE"]
        result = match_program("Computational Science", programs, threshold=0.5, ambiguity_margin=0.5)
        self.assertEqual(result["status"], "ambiguous")
        self.assertLessEqual(len(result["candidates"]), 3)

    def test_not_found(self):
        result = match_program("Classical Archaeology", self.programs)
        self.assertEqual(result, {"status": "not_found", "candidates": []})


class PrivacyAndValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = json.loads((ROOT / "examples" / "sample-plan.json").read_text(encoding="utf-8"))

    def test_sample_is_valid_and_has_four_dynamic_categories(self):
        validate_plan(self.sample)
        self.assertEqual(len(self.sample["categories"]), 4)
        labels = {item["label"] for item in self.sample["categories"]}
        self.assertNotIn("Methodology", labels)

    def test_privacy_filter_removes_nested_sensitive_keys(self):
        unsafe = copy.deepcopy(self.sample)
        unsafe["full_name"] = "Private Student"
        unsafe["program"]["student_id"] = "12345678"
        unsafe["courses"][0]["grade"] = "1.0"
        unsafe["courses"][0]["nested"] = {"access_token": "secret"}
        safe = sanitize_personal_data(unsafe)
        serialized = json.dumps(safe)
        self.assertNotIn("Private Student", serialized)
        self.assertNotIn("12345678", serialized)
        self.assertNotIn("secret", serialized)
        validate_plan(safe)

    def test_rejects_current_term_course(self):
        invalid = copy.deepcopy(self.sample)
        invalid["courses"][0]["term"] = invalid["planning_term"]["current"]["code"]
        with self.assertRaisesRegex(PlannerValidationError, "does not belong to target term"):
            validate_plan(invalid)

    def test_rejects_mismatched_term_id(self):
        invalid = copy.deepcopy(self.sample)
        invalid["courses"][0]["term_id"] = "current-term-id"
        with self.assertRaisesRegex(PlannerValidationError, "different target term ID"):
            validate_plan(invalid)

    def test_unavailable_offerings_cannot_hide_fallback_courses(self):
        invalid = copy.deepcopy(self.sample)
        invalid["offerings_status"] = "unavailable"
        with self.assertRaisesRegex(PlannerValidationError, "must not contain fallback courses"):
            validate_plan(invalid)

    def test_unavailable_offerings_with_no_courses_is_valid(self):
        valid = copy.deepcopy(self.sample)
        valid["offerings_status"] = "unavailable"
        valid["offerings_message"] = "Target-semester catalogue is not published."
        valid["courses"] = []
        validate_plan(valid)

    def test_rejects_duplicate_course_ids(self):
        invalid = copy.deepcopy(self.sample)
        invalid["courses"].append(copy.deepcopy(invalid["courses"][0]))
        with self.assertRaisesRegex(PlannerValidationError, "Duplicate course id"):
            validate_plan(invalid)

    def test_result_pagination_is_bounded_to_one_hundred(self):
        pages = paginate_results(range(235))
        self.assertEqual([len(page) for page in pages], [100, 100, 35])
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            paginate_results(range(10), 101)

    def test_catalog_audit_rejects_incomplete_pagination(self):
        invalid = copy.deepcopy(self.sample)
        invalid["catalog_audit"]["visible_total"] = invalid["catalog_audit"]["collected_count"] + 1
        with self.assertRaisesRegex(PlannerValidationError, "pagination is incomplete"):
            validate_plan(invalid)

    def test_aggregate_requirement_must_reference_known_categories(self):
        invalid = copy.deepcopy(self.sample)
        invalid["aggregate_requirements"] = [{
            "id": "all-electives", "label": "All electives", "min_ects": 30, "max_ects": None,
            "category_ids": ["not-a-category"], "source": invalid["program"]["source"],
        }]
        with self.assertRaisesRegex(PlannerValidationError, "unknown category"):
            validate_plan(invalid)

    def test_rejects_unknown_selected_session_group(self):
        invalid = copy.deepcopy(self.sample)
        invalid["courses"][0]["selected_group_id"] = "not-a-real-group"
        with self.assertRaisesRegex(PlannerValidationError, "Unknown selected session group"):
            validate_plan(invalid)

    def test_multiple_session_groups_do_not_duplicate_course_record(self):
        course = self.sample["courses"][0]
        self.assertEqual(len(course["session_groups"]), 2)
        planned_ects = sum(item["ects"] or 0 for item in self.sample["courses"] if item["status"] in {"planned", "enrolled"})
        self.assertEqual(planned_ects, 11)

    def test_builder_creates_self_contained_privacy_safe_html(self):
        unsafe = copy.deepcopy(self.sample)
        unsafe["full_name"] = "Private Student"
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.html"
            input_path.write_text(json.dumps(unsafe), encoding="utf-8")
            build(input_path, output_path)
            html = output_path.read_text(encoding="utf-8")
        self.assertIn("TUM ELECTIVE PLANNER", html)
        self.assertIn("WS-2026-27", html)
        self.assertIn("Interdisciplinary Project", html)
        self.assertNotIn("Private Student", html)
        self.assertNotIn("__PLANNER_DATA__", html)
        self.assertNotIn("https://cdn", html)

    def test_load_and_prepare_filters_before_validation(self):
        unsafe = copy.deepcopy(self.sample)
        unsafe["email"] = "student@example.org"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(unsafe), encoding="utf-8")
            safe = load_and_prepare(path)
        self.assertNotIn("email", safe)

    def test_bioinformatics_public_only_example_builds_with_aggregate_rule(self):
        source = ROOT / "examples" / "bioinformatics-ws-2026-27.json"
        plan = json.loads(source.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bioinformatics.html"
            build(source, output)
            html = output.read_text(encoding="utf-8")
        self.assertIn("Bioinformatics", html)
        self.assertIn('"min_ects":78', html)
        self.assertIn("public_degree_programme", html)
        self.assertIn("public_course", html)
        self.assertIn("Advanced Data Handling and Visualization Techniques", html)
        self.assertIn("950943958-standard", html)
        self.assertNotIn("My Studies", html)
        self.assertEqual(plan["program"]["curriculum_version_id"], 4564)
        self.assertEqual(len(plan["courses"]), 17)
        self.assertEqual(len([course for course in plan["courses"] if course["module_code"] == "IN2379"]), 1)
        self.assertEqual(len([course for course in plan["courses"] if course["module_code"] == "IN2309"]), 1)
        self.assertEqual(len([course for course in plan["courses"] if course["module_code"] == "IN2230"]), 1)
        self.assertIn("22 target-term rows", plan["offerings_message"])

    def test_course_field_evidence_is_validated(self):
        invalid = copy.deepcopy(self.sample)
        invalid["courses"][0]["evidence"] = [{"kind": "not-real", "label": "Broken", "observed_at": "2026-08-16T10:00:00Z"}]
        with self.assertRaisesRegex(PlannerValidationError, r"evidence\[0\].kind"):
            validate_plan(invalid)

    def test_mmt_example_has_complete_index_and_interactive_controls(self):
        source = ROOT / "examples" / "mmt-ws-2026-27.json"
        plan = json.loads(source.read_text(encoding="utf-8"))
        validate_plan(plan)
        self.assertTrue(plan["default_selected"])
        self.assertEqual(plan["catalog_audit"]["visible_total"], 106)
        self.assertEqual(plan["catalog_audit"]["collected_count"], 106)
        self.assertTrue(plan["catalog_audit"]["pagination_exhausted"])
        self.assertEqual(len(plan["courses"]), 106)
        self.assertIn("curriculum-tree evidence before publication", plan["offerings_message"])
        detailed = next(course for course in plan["courses"] if course["id"] == "950945390")
        self.assertEqual(detailed["schedule_status"], "published")
        self.assertEqual(len(detailed["session_groups"][0]["meetings"]), 2)
        self.assertEqual(detailed["registration"]["status"], "upcoming")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "mmt.html"
            build(source, output)
            html = output.read_text(encoding="utf-8")
        self.assertIn('id="track-filters"', html)
        self.assertIn('id="calendar-scale"', html)
        self.assertIn('min="50" max="200" value="70"', html)
        self.assertIn('id="scheduled-summary"', html)
        self.assertIn('document.documentElement.style.fontSize = `${font}%`', html)
        self.assertIn("Personal, non-commercial planning support only", html)
        self.assertIn("Deselect visible", html)
        self.assertIn("Registration possible from 30.08.2026", html)

    def test_repository_license_is_personal_noncommercial(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(license_text.startswith("Personal Non-Commercial License 1.0"))
        self.assertIn("TUMONLINE", license_text)
        self.assertNotIn("MIT License", license_text)


if __name__ == "__main__":
    unittest.main()
