from __future__ import annotations

from collections.abc import Sequence

from app.analysis_modules.base import AnalysisCapability, AnalysisModule


STUDENT_SCORE_ANALYSIS_CAPABILITIES: tuple[AnalysisCapability, ...] = (
    AnalysisCapability(id="student_count", name="学生数量分析", all_of=("student_id",)),
    AnalysisCapability(id="score_summary", name="成绩概览", all_of=("score",)),
    AnalysisCapability(
        id="subject_score",
        name="学科成绩分析",
        all_of=("subject", "score"),
    ),
    AnalysisCapability(
        id="class_score",
        name="班级成绩分析",
        all_of=("class_name", "score"),
    ),
    AnalysisCapability(
        id="student_score",
        name="学生成绩分析",
        all_of=("student_id", "score"),
    ),
    AnalysisCapability(
        id="exam_trend",
        name="考试趋势分析",
        any_of=(("exam_date", "score"), ("exam_name", "score")),
    ),
)


class StudentScoreModule(AnalysisModule):
    id = "student_score"
    name = "学生成绩分析"

    _SIGNALS: tuple[frozenset[str], ...] = (
        frozenset(("student_id", "score")),
        frozenset(("student_name", "score")),
        frozenset(("subject", "score")),
        frozenset(("class_name", "score")),
        frozenset(("exam_date", "score")),
        frozenset(("exam_name", "score")),
    )

    def capabilities(self) -> Sequence[AnalysisCapability]:
        return STUDENT_SCORE_ANALYSIS_CAPABILITIES

    def match_score(self, available_fields: set[str]) -> float:
        matched_signal_count = sum(
            signal <= available_fields for signal in self._SIGNALS
        )
        if not matched_signal_count:
            return 0.0
        return min(1.0, 0.65 + (matched_signal_count - 1) * 0.1)
