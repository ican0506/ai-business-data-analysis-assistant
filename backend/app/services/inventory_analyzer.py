from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


class InventoryAnalyzer:
    """Calculate only inventory facts enabled by the current capability plan."""

    def analyze(
        self,
        frame: pd.DataFrame,
        analysis_plan: Sequence[Mapping[str, object]],
    ) -> dict[str, object]:
        supported = {str(item["id"]): bool(item["supported"]) for item in analysis_plan}
        return {
            "inventory_count": self._inventory_count(frame)
            if supported.get("inventory_count", False)
            else None,
            "stock_summary": self._stock_summary(frame)
            if supported.get("stock_summary", False)
            else None,
            "low_stock_analysis": self._low_stock_analysis(frame)
            if supported.get("low_stock_analysis", False)
            else [],
            "inventory_value": self._inventory_value(frame)
            if supported.get("inventory_value", False)
            else None,
            "category_stock": self._group_stock(frame, "category")
            if supported.get("category_stock", False)
            else [],
            "warehouse_stock": self._group_stock(frame, "warehouse")
            if supported.get("warehouse_stock", False)
            else [],
            "supplier_stock": self._group_stock(frame, "supplier")
            if supported.get("supplier_stock", False)
            else [],
            "inventory_flow": self._inventory_flow(frame)
            if supported.get("inventory_flow", False)
            else None,
            "inventory_trend": self._inventory_trend(frame)
            if supported.get("inventory_trend", False)
            else [],
        }

    @staticmethod
    def _inventory_count(frame: pd.DataFrame) -> int:
        for column in ("product_id", "product_name"):
            values = InventoryAnalyzer._non_empty_values(frame, column)
            if not values.empty:
                return int(values.astype(str).str.strip().nunique())
        return 0

    @staticmethod
    def _stock_summary(frame: pd.DataFrame) -> dict[str, int | float] | None:
        stock = InventoryAnalyzer._numeric(frame, "stock_quantity")
        if stock.empty:
            return None
        return {
            "count": int(stock.count()),
            "total": InventoryAnalyzer._rounded(stock.sum()),
            "average": InventoryAnalyzer._rounded(stock.mean()),
            "maximum": InventoryAnalyzer._rounded(stock.max()),
            "minimum": InventoryAnalyzer._rounded(stock.min()),
            "median": InventoryAnalyzer._rounded(stock.median()),
        }

    @staticmethod
    def _low_stock_analysis(frame: pd.DataFrame) -> list[dict[str, str | float]]:
        rows = InventoryAnalyzer._paired_numeric_rows(frame, "stock_quantity", "safety_stock")
        if rows.empty:
            return []
        rows = rows.loc[rows["_left"] < rows["_right"]].copy()
        rows["_shortage"] = rows["_right"] - rows["_left"]
        result: list[dict[str, str | float]] = []
        for _, row in rows.iterrows():
            item: dict[str, str | float] = {
                "stock_quantity": InventoryAnalyzer._rounded(row["_left"]),
                "safety_stock": InventoryAnalyzer._rounded(row["_right"]),
                "shortage": InventoryAnalyzer._rounded(row["_shortage"]),
            }
            for column in ("product_id", "product_name"):
                if column in row and InventoryAnalyzer._is_non_empty(row[column]):
                    item[column] = str(row[column]).strip()
            result.append(item)
        return sorted(
            result,
            key=lambda item: (
                -float(item["shortage"]),
                str(item.get("product_id") or item.get("product_name") or ""),
            ),
        )

    @staticmethod
    def _inventory_value(frame: pd.DataFrame) -> dict[str, int | float] | None:
        rows = InventoryAnalyzer._paired_numeric_rows(frame, "stock_quantity", "unit_cost")
        if rows.empty:
            return None
        values = rows["_left"] * rows["_right"]
        return {
            "count": int(values.count()),
            "total": InventoryAnalyzer._rounded(values.sum()),
            "average": InventoryAnalyzer._rounded(values.mean()),
        }

    @staticmethod
    def _group_stock(frame: pd.DataFrame, group_column: str) -> list[dict[str, str | float]]:
        if group_column not in frame or "stock_quantity" not in frame:
            return []
        rows = frame.copy()
        rows["_stock"] = pd.to_numeric(rows["stock_quantity"], errors="coerce")
        rows = rows.dropna(subset=["_stock"])
        rows = rows.loc[InventoryAnalyzer._non_empty_mask(rows[group_column])].copy()
        if rows.empty:
            return []
        rows["_label"] = rows[group_column].astype(str).str.strip()
        grouped = rows.groupby("_label", sort=False)["_stock"].sum()
        return sorted(
            [
                {"name": str(name), "value": InventoryAnalyzer._rounded(value)}
                for name, value in grouped.items()
            ],
            key=lambda item: (-float(item["value"]), str(item["name"])),
        )

    @staticmethod
    def _inventory_flow(frame: pd.DataFrame) -> dict[str, float] | None:
        rows = InventoryAnalyzer._paired_numeric_rows(frame, "inbound_quantity", "outbound_quantity")
        if rows.empty:
            return None
        inbound = InventoryAnalyzer._rounded(rows["_left"].sum())
        outbound = InventoryAnalyzer._rounded(rows["_right"].sum())
        return {
            "total_inbound": inbound,
            "total_outbound": outbound,
            "net_change": InventoryAnalyzer._rounded(inbound - outbound),
        }

    @staticmethod
    def _inventory_trend(frame: pd.DataFrame) -> list[dict[str, str | float]]:
        if "inventory_date" not in frame or "stock_quantity" not in frame:
            return []
        rows = frame.copy()
        rows["_date"] = pd.to_datetime(rows["inventory_date"], errors="coerce", format="mixed")
        rows["_stock"] = pd.to_numeric(rows["stock_quantity"], errors="coerce")
        rows = rows.dropna(subset=["_date", "_stock"])
        if rows.empty:
            return []
        grouped = rows.groupby("_date", sort=True)["_stock"].sum()
        return [
            {"name": pd.Timestamp(date).strftime("%Y-%m-%d"), "value": InventoryAnalyzer._rounded(value)}
            for date, value in grouped.items()
        ]

    @staticmethod
    def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
        if column not in frame:
            return pd.Series(dtype=float)
        return pd.to_numeric(frame[column], errors="coerce").dropna()

    @staticmethod
    def _paired_numeric_rows(frame: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
        if left not in frame or right not in frame:
            return frame.iloc[0:0].copy()
        rows = frame.copy()
        rows["_left"] = pd.to_numeric(rows[left], errors="coerce")
        rows["_right"] = pd.to_numeric(rows[right], errors="coerce")
        return rows.dropna(subset=["_left", "_right"])

    @staticmethod
    def _non_empty_values(frame: pd.DataFrame, column: str) -> pd.Series:
        if column not in frame:
            return pd.Series(dtype=object)
        values = frame[column]
        return values.loc[InventoryAnalyzer._non_empty_mask(values)]

    @staticmethod
    def _non_empty_mask(values: pd.Series) -> pd.Series:
        return values.notna() & values.astype(str).str.strip().ne("")

    @staticmethod
    def _is_non_empty(value: object) -> bool:
        return bool(pd.notna(value) and str(value).strip())

    @staticmethod
    def _rounded(value: object) -> float:
        return round(float(value), 2)
