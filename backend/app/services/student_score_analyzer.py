from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


class StudentScoreAnalyzer:
    """Calculate only the student-score facts enabled by an analysis plan."""

    def analyze(
        self,
        frame: pd.DataFrame,
        analysis_plan: Sequence[Mapping[str, object]],
    ) -> dict[str, object]:
        supported = {
            str(item["id"]): bool(item["supported"])
            for item in analysis_plan
        }
        return {
            "student_count": self._student_count(frame)
            if supported.get("student_count", False)
            else None,
            "score_summary": self._score_summary(frame)
            if supported.get("score_summary", False)
            else None,
            "subject_score": self._group_score(frame, "subject")
            if supported.get("subject_score", False)
            else [],
            "class_score": self._group_score(frame, "class_name")
            if supported.get("class_score", False)
            else [],
            "student_score": self._student_score(frame)
            if supported.get("student_score", False)
            else [],
            "exam_trend": self._exam_trend(frame)
            if supported.get("exam_trend", False)
            else [],
        }

    @staticmethod
    def _student_count(frame: pd.DataFrame) -> int:
        student_ids = StudentScoreAnalyzer._non_empty_values(frame, "student_id")
        return int(student_ids.astype(str).nunique())

    @staticmethod
    def _score_summary(frame: pd.DataFrame) -> dict[str, int | float] | None:
        scores = StudentScoreAnalyzer._scores(frame)
        if scores.empty:
            return None
        return {
            "count": int(scores.count()),
            "average": StudentScoreAnalyzer._rounded(scores.mean()),
            "maximum": StudentScoreAnalyzer._rounded(scores.max()),
            "minimum": StudentScoreAnalyzer._rounded(scores.min()),
            "median": StudentScoreAnalyzer._rounded(scores.median()),
        }

    @staticmethod
    def _group_score(frame: pd.DataFrame, column: str) -> list[dict[str, int | float | str]]:
        rows = StudentScoreAnalyzer._score_rows(frame)
        if rows.empty or column not in rows:
            return []
        labels = rows[column]
        rows = rows.loc[StudentScoreAnalyzer._non_empty_mask(labels)].copy()
        if rows.empty:
            return []
        rows["_label"] = rows[column].astype(str).str.strip()
        grouped = rows.groupby("_label", sort=False)["_score"]
        result = [
            {
                "name": str(name),
                "count": int(scores.count()),
                "average": StudentScoreAnalyzer._rounded(scores.mean()),
                "maximum": StudentScoreAnalyzer._rounded(scores.max()),
                "minimum": StudentScoreAnalyzer._rounded(scores.min()),
            }
            for name, scores in grouped
        ]
        return sorted(result, key=lambda item: (-float(item["average"]), str(item["name"])))

    @staticmethod
    def _student_score(frame: pd.DataFrame) -> list[dict[str, int | float | str]]:
        rows = StudentScoreAnalyzer._score_rows(frame)
        if rows.empty or "student_id" not in rows:
            return []
        rows = rows.loc[StudentScoreAnalyzer._non_empty_mask(rows["student_id"])].copy()
        if rows.empty:
            return []
        rows["_student_id"] = rows["student_id"].astype(str).str.strip()
        result: list[dict[str, int | float | str]] = []
        for student_id, scores in rows.groupby("_student_id", sort=False):
            item: dict[str, int | float | str] = {
                "student_id": str(student_id),
                "score_count": int(scores["_score"].count()),
                "average": StudentScoreAnalyzer._rounded(scores["_score"].mean()),
                "maximum": StudentScoreAnalyzer._rounded(scores["_score"].max()),
                "minimum": StudentScoreAnalyzer._rounded(scores["_score"].min()),
            }
            if "student_name" in scores:
                names = scores.loc[
                    StudentScoreAnalyzer._non_empty_mask(scores["student_name"]),
                    "student_name",
                ]
                if not names.empty:
                    item["student_name"] = str(names.iloc[0]).strip()
            result.append(item)
        return sorted(
            result,
            key=lambda item: (-float(item["average"]), str(item["student_id"])),
        )

    @staticmethod
    def _exam_trend(frame: pd.DataFrame) -> list[dict[str, int | float | str]]:
        rows = StudentScoreAnalyzer._score_rows(frame)
        if rows.empty:
            return []

        if "exam_date" in rows:
            dated_rows = rows.assign(
                _exam_date=pd.to_datetime(
                    rows["exam_date"],
                    errors="coerce",
                    format="mixed",
                )
            ).dropna(subset=["_exam_date"])
            if not dated_rows.empty:
                grouped = dated_rows.groupby("_exam_date", sort=True)["_score"]
                return [
                    {
                        "name": pd.Timestamp(date).strftime("%Y-%m-%d"),
                        "average": StudentScoreAnalyzer._rounded(scores.mean()),
                        "count": int(scores.count()),
                    }
                    for date, scores in grouped
                ]

        if "exam_name" not in rows:
            return []
        named_rows = rows.loc[StudentScoreAnalyzer._non_empty_mask(rows["exam_name"])].copy()
        if named_rows.empty:
            return []
        named_rows["_exam_name"] = named_rows["exam_name"].astype(str).str.strip()
        grouped = named_rows.groupby("_exam_name", sort=False)["_score"]
        return [
            {
                "name": str(name),
                "average": StudentScoreAnalyzer._rounded(scores.mean()),
                "count": int(scores.count()),
            }
            for name, scores in grouped
        ]

    @staticmethod
    def _scores(frame: pd.DataFrame) -> pd.Series:
        if "score" not in frame:
            return pd.Series(dtype=float)
        return pd.to_numeric(frame["score"], errors="coerce").dropna()

    @staticmethod
    def _score_rows(frame: pd.DataFrame) -> pd.DataFrame:
        if "score" not in frame:
            return frame.iloc[0:0].copy().assign(_score=pd.Series(dtype=float))
        rows = frame.copy()
        rows["_score"] = pd.to_numeric(rows["score"], errors="coerce")
        return rows.dropna(subset=["_score"])

    @staticmethod
    def _non_empty_values(frame: pd.DataFrame, column: str) -> pd.Series:
        if column not in frame:
            return pd.Series(dtype=object)
        values = frame[column]
        return values.loc[StudentScoreAnalyzer._non_empty_mask(values)]

    @staticmethod
    def _non_empty_mask(values: pd.Series) -> pd.Series:
        return values.notna() & values.astype(str).str.strip().ne("")

    @staticmethod
    def _rounded(value: float) -> float:
        return round(float(value), 2)
