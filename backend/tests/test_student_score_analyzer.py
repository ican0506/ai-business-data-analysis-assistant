from __future__ import annotations

import pandas as pd

from app.analysis_modules.student_score import STUDENT_SCORE_ANALYSIS_CAPABILITIES
from app.services.analysis_planner import AnalysisPlanner
from app.services.student_score_analyzer import StudentScoreAnalyzer


def analyze(data: dict[str, list[object]]) -> dict:
    frame = pd.DataFrame(data)
    plan = AnalysisPlanner().plan(
        AnalysisPlanner.available_fields_from_dataframe(frame),
        STUDENT_SCORE_ANALYSIS_CAPABILITIES,
    )
    return StudentScoreAnalyzer().analyze(frame, plan)


def test_student_count_counts_each_non_empty_student_id_once() -> None:
    result = analyze(
        {"student_id": ["S-1", "S-1", "S-2", None, ""], "score": [90, 80, 70, 60, 50]}
    )

    assert result["student_count"] == 2


def test_score_summary_ignores_invalid_scores_without_converting_them_to_zero() -> None:
    result = analyze({"score": [90, "abc", None, 80, ""]})

    assert result["score_summary"] == {
        "count": 2,
        "average": 85.0,
        "maximum": 90.0,
        "minimum": 80.0,
        "median": 85.0,
    }


def test_score_summary_is_none_when_no_score_is_convertible() -> None:
    result = analyze({"score": ["excellent", "abc", None]})

    assert result["score_summary"] is None


def test_real_zero_scores_are_calculated_not_treated_as_unavailable() -> None:
    result = analyze({"score": [0, 0, 0]})

    assert result["score_summary"] == {
        "count": 3,
        "average": 0.0,
        "maximum": 0.0,
        "minimum": 0.0,
        "median": 0.0,
    }


def test_subject_and_class_aggregations_are_deterministic() -> None:
    result = analyze(
        {
            "subject": ["math", "english", "math", "english", None],
            "class_name": ["A", "B", "A", "B", "A"],
            "score": [90, 90, 80, 70, 100],
        }
    )

    assert result["subject_score"] == [
        {"name": "math", "count": 2, "average": 85.0, "maximum": 90.0, "minimum": 80.0},
        {"name": "english", "count": 2, "average": 80.0, "maximum": 90.0, "minimum": 70.0},
    ]
    assert result["class_score"] == [
        {"name": "A", "count": 3, "average": 90.0, "maximum": 100.0, "minimum": 80.0},
        {"name": "B", "count": 2, "average": 80.0, "maximum": 90.0, "minimum": 70.0},
    ]


def test_student_aggregation_keeps_working_without_student_name() -> None:
    result = analyze(
        {"student_id": ["S-2", "S-1", "S-1", "S-2"], "score": [80, 90, 70, 80]}
    )

    assert result["student_score"] == [
        {"student_id": "S-1", "score_count": 2, "average": 80.0, "maximum": 90.0, "minimum": 70.0},
        {"student_id": "S-2", "score_count": 2, "average": 80.0, "maximum": 80.0, "minimum": 80.0},
    ]


def test_exam_date_is_used_first_and_sorted_ascending() -> None:
    result = analyze(
        {
            "exam_date": ["2026-04-01", "2026-03-01", "bad"],
            "exam_name": ["April", "March", "Fallback"],
            "score": [80, 70, 100],
        }
    )

    assert result["exam_trend"] == [
        {"name": "2026-03-01", "average": 70.0, "count": 1},
        {"name": "2026-04-01", "average": 80.0, "count": 1},
    ]


def test_exam_name_is_used_in_first_appearance_order_when_dates_are_unusable() -> None:
    result = analyze(
        {
            "exam_date": ["bad", "still-bad", None],
            "exam_name": ["midterm", "final", "midterm"],
            "score": [80, 90, 100],
        }
    )

    assert result["exam_trend"] == [
        {"name": "midterm", "average": 90.0, "count": 2},
        {"name": "final", "average": 90.0, "count": 1},
    ]


def test_unsupported_capabilities_keep_null_or_empty_result_shapes() -> None:
    result = analyze({"student_id": ["S-1"]})

    assert result == {
        "student_count": 1,
        "score_summary": None,
        "subject_score": [],
        "class_score": [],
        "student_score": [],
        "exam_trend": [],
    }
