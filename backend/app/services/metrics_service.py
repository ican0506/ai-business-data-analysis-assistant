from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.models.dataset_cleaning import DatasetCleaningRun


class MetricsService:
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
        sales = self._numeric(frame, "sales_amount")
        targets = self._numeric(frame, "target_amount")
        total_sales = float(sales.sum())
        result = {
            "dataset_id": dataset.id,
            "total_rows": len(frame.index),
            "sales_amount": self._summary(sales),
            "growth_rate": self._growth_rate(frame, sales),
            "completion_rate": round(total_sales / float(targets.sum()) * 100, 2) if float(targets.sum()) else None,
            "top_regions": self._top_regions(frame),
        }
        return result

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
        if "region" not in frame or "sales_amount" not in frame:
            return []
        rows = frame.assign(_sales=pd.to_numeric(frame["sales_amount"], errors="coerce")).dropna(subset=["region", "_sales"])
        grouped = rows.groupby("region", as_index=False)["_sales"].sum().sort_values("_sales", ascending=False).head(10)
        return [
            {"name": str(row["region"]), "value": round(float(row["_sales"]), 2)}
            for _, row in grouped.iterrows()
        ]
