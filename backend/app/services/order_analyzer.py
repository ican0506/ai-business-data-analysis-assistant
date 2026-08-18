from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


class OrderAnalyzer:
    """Build deterministic, privacy-safe business facts for order datasets."""

    _STATUS_MAP = {
        "待支付": "pending", "pending": "pending", "待付款": "pending",
        "已支付": "paid", "paid": "paid",
        "已完成": "completed", "completed": "completed", "complete": "completed",
        "已取消": "cancelled", "取消": "cancelled", "cancelled": "cancelled", "canceled": "cancelled",
        "退款中": "refund_in_progress", "refund in progress": "refund_in_progress",
        "已退款": "refunded", "退款": "refunded", "refunded": "refunded",
    }
    _REGION_MAP = {
        "郑州市": "郑州", "zhengzhou": "郑州",
        "洛阳市": "洛阳", "luoyang": "洛阳",
    }
    _SENSITIVE_COLUMNS = {"phone", "email", "remark"}

    def analyze(
        self,
        frame: pd.DataFrame,
        analysis_plan: Sequence[Mapping[str, object]],
    ) -> dict[str, object]:
        supported = {str(item["id"]): bool(item["supported"]) for item in analysis_plan}
        prepared, quality = self._prepare(frame)
        available = prepared.loc[~prepared["_duplicate_row"]].copy()
        trusted = available.loc[available["_trusted_amount"].notna()].copy()

        overview = self._overview(available, trusted, quality)
        result = {
            "overview": overview,
            "product_analysis": (
                self._product_analysis(available)
                if supported.get("product_sales") or supported.get("product_quantity")
                else []
            ),
            "category_analysis": self._category_analysis(available) if supported.get("category_analysis") else [],
            "region_analysis": self._region_analysis(available) if supported.get("region_sales") else [],
            "time_analysis": self._time_analysis(available) if supported.get("sales_trend") else {"daily_sales_trend": [], "monthly_sales_trend": [], "monthly_order_trend": []},
            "customer_analysis": self._customer_analysis(available) if supported.get("customer_analysis") else None,
            "status_analysis": self._status_analysis(available) if supported.get("status_analysis") else [],
            "status_summary": self._status_summary(available) if supported.get("status_analysis") else None,
            "payment_method_analysis": self._payment_analysis(available) if supported.get("payment_method_analysis") else [],
            "discount_analysis": self._discount_analysis(available) if supported.get("discount_analysis") else None,
            "demographic_analysis": self._demographic_analysis(available) if supported.get("demographic_analysis") else None,
            "data_quality": quality if supported.get("data_quality_analysis") else None,
        }
        return result

    def _prepare(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
        rows = frame.copy()
        rows["_duplicate_row"] = rows.duplicated(keep="first")
        rows["_order_id"] = self._text(rows, "order_id")
        rows["_customer_id"] = self._text(rows, "customer_id")
        rows["_product"] = self._text(rows, "product")
        rows["_category"] = self._text(rows, "category").fillna("未分类")
        rows["_region"] = self._text(rows, "region").map(self._normalize_region)
        rows["_date"] = self._date(rows, "date")
        rows["_unit_price"] = self._number(rows, "unit_price")
        rows["_quantity"] = self._number(rows, "quantity")
        rows["_discount"] = self._number(rows, "discount")
        rows["_raw_amount"] = self._number(rows, "sales_amount")
        rows["_status"] = self._text(rows, "status").map(self._normalize_status)

        has_discount_column = "discount" in rows
        valid_price = rows["_unit_price"].notna() & rows["_unit_price"].ge(0)
        valid_quantity = rows["_quantity"].notna() & rows["_quantity"].ge(0)
        valid_discount = (
            rows["_discount"].notna() & rows["_discount"].between(0, 1)
            if has_discount_column else pd.Series(True, index=rows.index)
        )
        rows["_expected_amount"] = pd.NA
        expected_mask = valid_price & valid_quantity & valid_discount
        multiplier = (
            rows["_discount"]
            if has_discount_column
            else pd.Series(1.0, index=rows.index, dtype=float)
        )
        rows.loc[expected_mask, "_expected_amount"] = (
            rows.loc[expected_mask, "_unit_price"]
            * rows.loc[expected_mask, "_quantity"]
            * multiplier.loc[expected_mask]
        )
        rows["_expected_amount"] = pd.to_numeric(rows["_expected_amount"], errors="coerce")
        valid_raw = rows["_raw_amount"].notna() & rows["_raw_amount"].ge(0)
        rows["_trusted_amount"] = rows["_expected_amount"].where(
            rows["_expected_amount"].notna(), rows["_raw_amount"].where(valid_raw)
        )
        rows["_amount_mismatch"] = (
            rows["_expected_amount"].notna()
            & valid_raw
            & ~rows["_expected_amount"].sub(rows["_raw_amount"]).abs().le(0.01)
        )

        missing = {
            str(column): int(rows[column].isna().sum())
            for column in frame.columns
            if int(rows[column].isna().sum()) > 0
        }
        valid_order_ids = rows["_order_id"].dropna()
        invalid_status = rows["_status"].eq("unknown")
        quality: dict[str, object] = {
            "row_count": int(len(rows)),
            "duplicate_row_count": int(rows["_duplicate_row"].sum()),
            "duplicate_order_id_count": int(valid_order_ids.duplicated(keep="first").sum()),
            "missing_value_summary": missing,
            "invalid_date_count": self._invalid_date_count(frame, rows),
            "invalid_unit_price_count": int((rows["_unit_price"].notna() & rows["_unit_price"].lt(0)).sum()),
            "zero_unit_price_count": int(rows["_unit_price"].eq(0).sum()),
            "invalid_quantity_count": int((rows["_quantity"].notna() & rows["_quantity"].lt(0)).sum()),
            "zero_quantity_count": int(rows["_quantity"].eq(0).sum()),
            "invalid_discount_count": int(
                (rows["_discount"].notna() & ~rows["_discount"].between(0, 1)).sum()
            ) if has_discount_column else 0,
            "invalid_age_count": self._invalid_age_count(rows),
            "invalid_status_count": int(invalid_status.sum()) if "status" in rows else 0,
            "amount_mismatch_count": int(rows.loc[~rows["_duplicate_row"], "_amount_mismatch"].sum()),
        }
        return rows, quality

    @staticmethod
    def _overview(rows: pd.DataFrame, trusted: pd.DataFrame, quality: Mapping[str, object]) -> dict[str, object]:
        values = trusted["_trusted_amount"]
        order_count = OrderAnalyzer._order_count(rows)
        valid_count = OrderAnalyzer._order_count(trusted)
        return {
            "record_count": int(quality["row_count"]),
            "order_count": order_count,
            "sales_total": OrderAnalyzer._round(values.sum()) if not values.empty else None,
            "average_order_value": OrderAnalyzer._round(values.mean()) if not values.empty else None,
            "maximum_order_value": OrderAnalyzer._round(values.max()) if not values.empty else None,
            "minimum_order_value": OrderAnalyzer._round(values.min()) if not values.empty else None,
            "median_order_value": OrderAnalyzer._round(values.median()) if not values.empty else None,
            "valid_sales_order_count": valid_count,
            "amount_mismatch_count": int(quality["amount_mismatch_count"]),
            "amount_mismatch_rate": OrderAnalyzer._round(
                int(quality["amount_mismatch_count"]) / valid_count * 100
            ) if valid_count else None,
            "gross_order_amount": OrderAnalyzer._round(values.sum()) if not values.empty else None,
            "completed_sales_amount": OrderAnalyzer._status_amount(rows, "completed"),
            "cancelled_order_amount": OrderAnalyzer._status_amount(rows, "cancelled"),
            "refund_related_amount": OrderAnalyzer._status_amount(rows, {"refund_in_progress", "refunded"}),
            "sales_volatility": OrderAnalyzer._volatility(values),
        }

    @staticmethod
    def _product_analysis(rows: pd.DataFrame) -> list[dict[str, object]]:
        return OrderAnalyzer._group_business(rows, "_product")

    @staticmethod
    def _category_analysis(rows: pd.DataFrame) -> list[dict[str, object]]:
        grouped = OrderAnalyzer._group_business(rows, "_category")
        total = sum(float(item["sales_amount"] or 0) for item in grouped)
        result = []
        for item in grouped:
            result.append({
                "category": item["name"],
                "order_count": item["order_count"],
                "quantity": item["quantity"],
                "sales_amount": item["sales_amount"],
                "sales_share": (
                    OrderAnalyzer._round(float(item["sales_amount"]) / total * 100)
                    if item["sales_amount"] is not None and total
                    else None
                ),
            })
        return result

    @staticmethod
    def _region_analysis(rows: pd.DataFrame) -> list[dict[str, object]]:
        grouped = OrderAnalyzer._group_business(rows, "_region")
        result = []
        for item in grouped:
            region_rows = rows.loc[rows["_region"] == item["name"]]
            targets = OrderAnalyzer._number(region_rows, "target_amount").dropna()
            target_amount = OrderAnalyzer._round(targets.sum()) if not targets.empty else None
            region_sales = item["sales_amount"]
            result.append({
                "name": item["name"], "region_order_count": item["order_count"],
                "region_sales": region_sales, "region_quantity": item["quantity"],
                "region_average_order_value": OrderAnalyzer._round(float(region_sales) / int(item["order_count"])) if region_sales is not None and item["order_count"] else None,
                "target_amount": target_amount,
                "completion_rate": OrderAnalyzer._round(float(region_sales) / float(target_amount) * 100) if region_sales is not None and target_amount else None,
                "value": region_sales,
            })
        return result

    @staticmethod
    def _time_analysis(rows: pd.DataFrame) -> dict[str, list[dict[str, object]]]:
        dated = rows.dropna(subset=["_date", "_trusted_amount"]).copy()
        if dated.empty:
            return {"daily_sales_trend": [], "monthly_sales_trend": [], "monthly_order_trend": []}
        daily = dated.groupby("_date", sort=True)
        daily_rows = [
            {"name": pd.Timestamp(date).strftime("%Y-%m-%d"), "value": OrderAnalyzer._round(group["_trusted_amount"].sum())}
            for date, group in daily
        ]
        month_groups = list(
            dated.assign(_month=dated["_date"].dt.to_period("M")).groupby("_month", sort=True)
        )
        monthly_sales = [{"name": str(month), "value": OrderAnalyzer._round(group["_trusted_amount"].sum())} for month, group in month_groups]
        monthly_orders = [{"name": str(month), "value": OrderAnalyzer._order_count(group)} for month, group in month_groups]
        return {
            "daily_sales_trend": daily_rows if len(daily_rows) >= 2 else [],
            "monthly_sales_trend": monthly_sales if len(monthly_sales) >= 2 else [],
            "monthly_order_trend": monthly_orders if len(monthly_orders) >= 2 else [],
        }

    @staticmethod
    def _customer_analysis(rows: pd.DataFrame) -> dict[str, object]:
        customers = rows.dropna(subset=["_customer_id"]).copy()
        if customers.empty:
            return {"unique_customer_count": 0, "repeat_customer_count": 0, "repeat_customer_rate": None, "average_orders_per_customer": None, "top_customers": []}
        result = []
        for customer_id, group in customers.groupby("_customer_id", sort=False):
            item: dict[str, object] = {
                "customer_id": str(customer_id),
                "order_count": OrderAnalyzer._order_count(group),
                "sales_amount": OrderAnalyzer._round(group["_trusted_amount"].dropna().sum()) if group["_trusted_amount"].notna().any() else None,
            }
            if "customer_name" in group:
                names = OrderAnalyzer._text(group, "customer_name").dropna()
                if not names.empty:
                    item["customer_name"] = str(names.iloc[0])
            result.append(item)
        result.sort(key=lambda item: (-float(item["sales_amount"] or 0), str(item["customer_id"])))
        repeats = [item for item in result if int(item["order_count"]) >= 2]
        count = len(result)
        return {
            "unique_customer_count": count,
            "repeat_customer_count": len(repeats),
            "repeat_customer_rate": OrderAnalyzer._round(len(repeats) / count * 100) if count else None,
            "average_orders_per_customer": OrderAnalyzer._round(sum(int(item["order_count"]) for item in result) / count) if count else None,
            "top_customers": result[:10],
        }

    @staticmethod
    def _status_analysis(rows: pd.DataFrame) -> list[dict[str, object]]:
        values = rows.dropna(subset=["_status"]).copy()
        if values.empty:
            return []
        grouped = []
        total_orders = OrderAnalyzer._order_count(values)
        for name, group in values.groupby("_status", sort=False):
            count = OrderAnalyzer._order_count(group)
            sales = group["_trusted_amount"].dropna()
            grouped.append({"name": str(name), "order_count": count, "sales_amount": OrderAnalyzer._round(sales.sum()) if not sales.empty else None, "share": OrderAnalyzer._round(count / total_orders * 100) if total_orders else None})
        return sorted(grouped, key=lambda item: (-int(item["order_count"]), str(item["name"])))

    @staticmethod
    def _status_summary(rows: pd.DataFrame) -> dict[str, object]:
        valid = rows.loc[rows["_status"].isin({"pending", "paid", "completed", "cancelled", "refund_in_progress", "refunded"})]
        denominator = OrderAnalyzer._order_count(valid)
        counts = {status: OrderAnalyzer._order_count(valid.loc[valid["_status"] == status]) for status in ("completed", "cancelled", "refund_in_progress", "refunded")}
        refund_count = counts["refund_in_progress"] + counts["refunded"]
        return {
            "completed_order_count": counts["completed"], "cancelled_order_count": counts["cancelled"], "refund_order_count": refund_count,
            "order_completion_rate": OrderAnalyzer._round(counts["completed"] / denominator * 100) if denominator else None,
            "cancellation_rate": OrderAnalyzer._round(counts["cancelled"] / denominator * 100) if denominator else None,
            "refund_rate": OrderAnalyzer._round(refund_count / denominator * 100) if denominator else None,
        }

    @staticmethod
    def _payment_analysis(rows: pd.DataFrame) -> list[dict[str, object]]:
        values = rows.copy()
        values["_payment"] = OrderAnalyzer._text(values, "payment_method")
        values = values.dropna(subset=["_payment"])
        if values.empty:
            return []
        total_orders = OrderAnalyzer._order_count(values)
        total_sales = values["_trusted_amount"].dropna().sum()
        result = []
        for name, group in values.groupby("_payment", sort=False):
            count = OrderAnalyzer._order_count(group)
            sales = group["_trusted_amount"].dropna()
            sales_total = OrderAnalyzer._round(sales.sum()) if not sales.empty else None
            result.append({"name": str(name), "order_count": count, "sales_amount": sales_total, "order_share": OrderAnalyzer._round(count / total_orders * 100) if total_orders else None, "sales_share": OrderAnalyzer._round(float(sales_total) / float(total_sales) * 100) if sales_total is not None and total_sales else None})
        return sorted(result, key=lambda item: (-float(item["sales_amount"] or 0), str(item["name"])))

    @staticmethod
    def _discount_analysis(rows: pd.DataFrame) -> dict[str, object] | None:
        if "discount" not in rows:
            return None
        valid = rows.loc[rows["_discount"].notna() & rows["_discount"].between(0, 1)].copy()
        if valid.empty:
            return {"valid_discount_count": 0, "discounted_order_count": 0, "discounted_order_rate": None, "average_discount": None, "average_discounted_order_value": None, "estimated_discount_amount": None}
        discounted = valid.loc[valid["_discount"].lt(1)]
        gross = valid.loc[valid["_expected_amount"].notna() & valid["_discount"].notna(), "_expected_amount"]
        before = valid.loc[valid["_expected_amount"].notna(), "_unit_price"] * valid.loc[valid["_expected_amount"].notna(), "_quantity"]
        values = discounted["_trusted_amount"].dropna()
        return {"valid_discount_count": int(len(valid)), "discounted_order_count": OrderAnalyzer._order_count(discounted), "discounted_order_rate": OrderAnalyzer._round(OrderAnalyzer._order_count(discounted) / OrderAnalyzer._order_count(valid) * 100) if OrderAnalyzer._order_count(valid) else None, "average_discount": OrderAnalyzer._round(valid["_discount"].mean()), "average_discounted_order_value": OrderAnalyzer._round(values.mean()) if not values.empty else None, "estimated_discount_amount": OrderAnalyzer._round((before - gross).sum()) if not gross.empty else None}

    @staticmethod
    def _demographic_analysis(rows: pd.DataFrame) -> dict[str, object] | None:
        result: dict[str, object] = {}
        if "gender" in rows:
            values = OrderAnalyzer._text(rows, "gender").fillna("unknown")
            result["gender"] = OrderAnalyzer._group_profile(rows.assign(_gender=values), "_gender")
        if "age" in rows:
            ages = OrderAnalyzer._number(rows, "age")
            valid = ages.where(ages.gt(0) & ages.lt(120))
            if valid.notna().any():
                bins = [0, 18, 25, 35, 45, 55, 65, float("inf")]
                labels = ["18以下", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
                result["age"] = OrderAnalyzer._group_profile(rows.assign(_age_group=pd.cut(valid, bins=bins, labels=labels, right=False).astype("string")), "_age_group")
        return result or None

    @staticmethod
    def _group_profile(rows: pd.DataFrame, column: str) -> list[dict[str, object]]:
        values = rows.dropna(subset=[column])
        return [
            {"name": str(name), "order_count": OrderAnalyzer._order_count(group), "customer_count": int(group["_customer_id"].dropna().nunique()), "sales_amount": OrderAnalyzer._round(group["_trusted_amount"].dropna().sum()) if group["_trusted_amount"].notna().any() else None}
            for name, group in values.groupby(column, sort=False)
        ]

    @staticmethod
    def _group_business(rows: pd.DataFrame, column: str) -> list[dict[str, object]]:
        values = rows.dropna(subset=[column]).copy()
        if values.empty:
            return []
        result = []
        for name, group in values.groupby(column, sort=False):
            quantities = group["_quantity"].where(group["_quantity"].ge(0)).dropna()
            sales = group["_trusted_amount"].dropna()
            result.append({"name": str(name), "order_count": OrderAnalyzer._order_count(group), "quantity": OrderAnalyzer._round(quantities.sum()) if not quantities.empty else None, "sales_amount": OrderAnalyzer._round(sales.sum()) if not sales.empty else None})
        return sorted(result, key=lambda item: (-float(item["sales_amount"] or 0), str(item["name"])))

    @staticmethod
    def _order_count(rows: pd.DataFrame) -> int:
        ids = rows["_order_id"].dropna() if "_order_id" in rows else pd.Series(dtype=object)
        return int(ids.nunique()) if not ids.empty else int(len(rows))

    @staticmethod
    def _status_amount(rows: pd.DataFrame, status: str | set[str]) -> float | None:
        statuses = {status} if isinstance(status, str) else status
        values = rows.loc[rows["_status"].isin(statuses), "_trusted_amount"].dropna()
        return OrderAnalyzer._round(values.sum()) if not values.empty else None

    @staticmethod
    def _text(rows: pd.DataFrame, column: str) -> pd.Series:
        if column not in rows:
            return pd.Series(pd.NA, index=rows.index, dtype="object")
        values = rows[column].where(rows[column].notna())
        values = values.astype("string").str.strip()
        return values.mask(values.eq(""))

    @staticmethod
    def _number(rows: pd.DataFrame, column: str) -> pd.Series:
        return pd.to_numeric(rows[column], errors="coerce") if column in rows else pd.Series(float("nan"), index=rows.index)

    @staticmethod
    def _date(rows: pd.DataFrame, column: str) -> pd.Series:
        return pd.to_datetime(rows[column], errors="coerce", format="mixed") if column in rows else pd.Series(pd.NaT, index=rows.index)

    @staticmethod
    def _invalid_date_count(frame: pd.DataFrame, rows: pd.DataFrame) -> int:
        return int((frame["date"].notna() & rows["_date"].isna()).sum()) if "date" in frame else 0

    @staticmethod
    def _invalid_age_count(rows: pd.DataFrame) -> int:
        ages = OrderAnalyzer._number(rows, "age")
        return int((ages.notna() & ~(ages.gt(0) & ages.lt(120))).sum())

    @classmethod
    def _normalize_region(cls, value: object) -> object:
        if pd.isna(value):
            return pd.NA
        text = str(value).strip()
        return cls._REGION_MAP.get(text.casefold(), text)

    @classmethod
    def _normalize_status(cls, value: object) -> str:
        if pd.isna(value):
            return "unknown"
        return cls._STATUS_MAP.get(str(value).strip().casefold(), "unknown")

    @staticmethod
    def _round(value: object) -> float:
        return round(float(value), 2)

    @staticmethod
    def _volatility(values: pd.Series) -> dict[str, float | None]:
        if len(values.index) < 2 or float(values.mean()) == 0:
            return {"standard_deviation": None, "coefficient_of_variation": None}
        standard_deviation = float(values.std(ddof=0))
        return {
            "standard_deviation": OrderAnalyzer._round(standard_deviation),
            "coefficient_of_variation": OrderAnalyzer._round(standard_deviation / float(values.mean()) * 100),
        }
