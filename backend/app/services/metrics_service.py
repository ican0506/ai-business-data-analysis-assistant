from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.models.dataset_cleaning import DatasetCleaningRun
from app.services.analysis_engine import AnalysisEngine
from app.services.field_mapping_override_service import FieldMappingOverrideService
from app.services.inventory_analyzer import InventoryAnalyzer
from app.services.student_score_analyzer import StudentScoreAnalyzer


class MetricsService:
    def __init__(self, override_service: FieldMappingOverrideService | None = None) -> None:
        self._override_service = override_service or FieldMappingOverrideService()

    def build_metrics(self, db: Session, dataset: Dataset) -> dict:
        run = db.scalar(
            select(DatasetCleaningRun)
            .where(DatasetCleaningRun.dataset_id == dataset.id)
            .order_by(DatasetCleaningRun.id.desc())
            .limit(1)
        )
        if run is None:
            raise ValueError("请先完成数据清洗，再进行统计分析")
        path = get_settings().resolved_storage_root / Path(run.cleaned_storage_path)
        if not path.is_file():
            raise ValueError("清洗后的数据文件不存在，请重新清洗")
        frame = pd.read_csv(path, encoding="utf-8-sig")
        return self._build_metrics_from_frame(
            frame,
            dataset_id=dataset.id,
            field_overrides=self._override_service.get_overrides(db, dataset.id),
        )

    def _build_metrics_from_frame(
        self,
        frame: pd.DataFrame,
        dataset_id: int,
        field_overrides: dict[str, str] | None = None,
    ) -> dict:
        engine = AnalysisEngine()
        analysis_frame, analysis_context = engine.prepare_context(
            frame, field_overrides=field_overrides
        )
        selected_module = analysis_context["selected_module"]
        available_fields = analysis_context["available_fields"]
        analysis_plan = analysis_context["analysis_plan"]
        field_mapping = analysis_context["field_mapping"]

        if selected_module["id"] != "order":
            return self._build_non_order_metrics(
                analysis_frame,
                dataset_id,
                selected_module,
                available_fields,
                analysis_plan,
                field_mapping,
                engine,
            )

        plan_by_id = {item["id"]: item for item in analysis_plan}
        analysis_frame = analysis_frame.copy()

        if self._is_supported(plan_by_id, "sales_total"):
            matched_fields = plan_by_id["sales_total"].get("matched_fields", [])
            if matched_fields == ["unit_price", "quantity"]:
                analysis_frame["sales_amount"] = (
                    pd.to_numeric(analysis_frame["unit_price"], errors="coerce")
                    * pd.to_numeric(analysis_frame["quantity"], errors="coerce")
                )

        sales = (
            self._numeric(analysis_frame, "sales_amount")
            if self._is_supported(plan_by_id, "sales_total")
            else None
        )
        targets = self._numeric(analysis_frame, "target_amount")
        region_ranking = (
            self._region_ranking(analysis_frame)
            if self._is_supported(plan_by_id, "region_sales")
            else []
        )
        completion_rate = self._completion_rate(
            sales,
            targets,
            self._is_supported(plan_by_id, "target_completion"),
        )
        result = {
            "dataset_id": dataset_id,
            "total_rows": len(analysis_frame.index),
            "selected_module": selected_module,
            "available_fields": available_fields,
            "analysis_plan": analysis_plan,
            "field_mapping": field_mapping,
            "generic_analysis": None,
            "student_score_analysis": None,
            "inventory_analysis": None,
            "sales_amount": self._summary(sales) if sales is not None else None,
            "growth_rate": (
                self._growth_rate(analysis_frame, sales)
                if sales is not None and self._is_supported(plan_by_id, "sales_trend")
                else None
            ),
            "completion_rate": completion_rate,
            "top_regions": region_ranking[:10],
            "region_ranking": region_ranking,
            "highest_sales_region": region_ranking[0] if region_ranking else None,
            "lowest_sales_region": region_ranking[-1] if region_ranking else None,
            "region_performance": (
                self._region_performance(analysis_frame)
                if self._is_supported(plan_by_id, "region_sales")
                else []
            ),
            "sales_volatility": self._sales_volatility(sales) if sales is not None else None,
            "order_count": self._order_count(analysis_frame) if self._is_supported(plan_by_id, "order_count") else None,
            "product_quantity": (
                self._product_quantity(analysis_frame)
                if self._is_supported(plan_by_id, "product_quantity")
                else []
            ),
        }
        return result

    @staticmethod
    def _build_non_order_metrics(
        frame: pd.DataFrame,
        dataset_id: int,
        selected_module: dict[str, object],
        available_fields: list[str],
        analysis_plan: list[dict[str, object]],
        field_mapping: dict[str, object],
        engine: AnalysisEngine,
    ) -> dict:
        """Keep the legacy metrics shape while preventing cross-domain calculations."""
        is_generic = selected_module["id"] == "generic"
        is_student_score = selected_module["id"] == "student_score"
        is_inventory = selected_module["id"] == "inventory"
        return {
            "dataset_id": dataset_id,
            "total_rows": len(frame.index),
            "selected_module": selected_module,
            "available_fields": available_fields,
            "analysis_plan": analysis_plan,
            "field_mapping": field_mapping,
            "generic_analysis": engine.build_generic_analysis(frame) if is_generic else None,
            "student_score_analysis": (
                StudentScoreAnalyzer().analyze(frame, analysis_plan)
                if is_student_score
                else None
            ),
            "inventory_analysis": (
                InventoryAnalyzer().analyze(frame, analysis_plan)
                if is_inventory
                else None
            ),
            "sales_amount": None,
            "growth_rate": None,
            "completion_rate": None,
            "top_regions": [],
            "region_ranking": [],
            "highest_sales_region": None,
            "lowest_sales_region": None,
            "region_performance": [],
            "sales_volatility": None,
            "order_count": None,
            "product_quantity": [],
        }

    @staticmethod
    def _is_supported(plan_by_id: dict[str, dict[str, object]], capability_id: str) -> bool:
        return bool(plan_by_id[capability_id]["supported"])

    @staticmethod
    def _completion_rate(
        sales: pd.Series | None,
        targets: pd.Series,
        supported: bool,
    ) -> float | None:
        if not supported or sales is None:
            return None
        total_target = float(targets.sum())
        return round(float(sales.sum()) / total_target * 100, 2) if total_target else None

    @staticmethod
    def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
        return pd.to_numeric(frame[column], errors="coerce").dropna() if column in frame else pd.Series(dtype=float)

    @staticmethod
    def _summary(series: pd.Series) -> dict:
        if series.empty:
            return {"total": 0, "average": None, "maximum": None, "minimum": None}
        return {"total": round(float(series.sum()), 2), "average": round(float(series.mean()), 2), "maximum": round(float(series.max()), 2), "minimum": round(float(series.min()), 2)}

    @staticmethod
    def _growth_rate(frame: pd.DataFrame, sales: pd.Series) -> float | None:
        if "date" not in frame or "sales_amount" not in frame:
            return None
        rows = frame.assign(_date=pd.to_datetime(frame["date"], errors="coerce"), _sales=pd.to_numeric(frame["sales_amount"], errors="coerce")).dropna(subset=["_date", "_sales"])
        if len(rows.index) < 2 or float(rows.iloc[0]._sales) == 0:
            return None
        rows = rows.sort_values("_date")
        return round((float(rows.iloc[-1]._sales) - float(rows.iloc[0]._sales)) / float(rows.iloc[0]._sales) * 100, 2)

    @staticmethod
    def _top_regions(frame: pd.DataFrame) -> list[dict]:
        return MetricsService._region_ranking(frame)[:10]

    @staticmethod
    def _region_ranking(frame: pd.DataFrame) -> list[dict]:
        if "region" not in frame or "sales_amount" not in frame:
            return []
        rows = frame.assign(_sales=pd.to_numeric(frame["sales_amount"], errors="coerce")).dropna(subset=["region", "_sales"])
        grouped = rows.groupby("region", as_index=False)["_sales"].sum().sort_values("_sales", ascending=False)
        return [
            {"name": str(row["region"]), "value": round(float(row["_sales"]), 2)}
            for _, row in grouped.iterrows()
        ]

    @staticmethod
    def _region_performance(frame: pd.DataFrame) -> list[dict]:
        if "region" not in frame or "sales_amount" not in frame:
            return []
        rows = frame.assign(
            _sales=pd.to_numeric(frame["sales_amount"], errors="coerce"),
        ).dropna(subset=["region", "_sales"])
        if "target_amount" in rows:
            rows = rows.assign(_target=pd.to_numeric(rows["target_amount"], errors="coerce"))
            grouped = rows.groupby("region", as_index=False).agg(
                sales_amount=("_sales", "sum"),
                target_amount=("_target", "sum"),
            )
        else:
            grouped = rows.groupby("region", as_index=False).agg(sales_amount=("_sales", "sum"))
            grouped["target_amount"] = None
        grouped = grouped.sort_values("sales_amount", ascending=False)
        return [
            {
                "name": str(row["region"]),
                "sales_amount": round(float(row["sales_amount"]), 2),
                "target_amount": round(float(row["target_amount"]), 2)
                if pd.notna(row["target_amount"])
                else None,
                "completion_rate": round(float(row["sales_amount"]) / float(row["target_amount"]) * 100, 2)
                if pd.notna(row["target_amount"]) and float(row["target_amount"])
                else None,
            }
            for _, row in grouped.iterrows()
        ]

    @staticmethod
    def _sales_volatility(sales: pd.Series) -> dict:
        if len(sales.index) < 2 or float(sales.mean()) == 0:
            return {"standard_deviation": None, "coefficient_of_variation": None}
        standard_deviation = float(sales.std(ddof=0))
        return {
            "standard_deviation": round(standard_deviation, 2),
            "coefficient_of_variation": round(standard_deviation / float(sales.mean()) * 100, 2),
        }

    @staticmethod
    def _order_count(frame: pd.DataFrame) -> int:
        return int(frame["order_id"].notna().sum())

    @staticmethod
    def _product_quantity(frame: pd.DataFrame) -> list[dict]:
        rows = frame.assign(_quantity=pd.to_numeric(frame["quantity"], errors="coerce")).dropna(
            subset=["product", "_quantity"]
        )
        grouped = rows.groupby("product", as_index=False)["_quantity"].sum().sort_values(
            "_quantity", ascending=False, kind="stable"
        )
        return [
            {"name": str(row["product"]), "value": round(float(row["_quantity"]), 2)}
            for _, row in grouped.iterrows()
        ]
