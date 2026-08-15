from __future__ import annotations

import re
import unicodedata

import pandas as pd


class CanonicalFieldMapper:
    """Map deterministic header aliases on an in-memory analysis copy only."""

    ORDER_ALIASES: dict[str, tuple[str, ...]] = {
        "order_id": ("订单编号", "订单号", "order id", "order_id", "orderid"),
        "product": ("商品", "商品名称", "产品", "产品名称", "product"),
        "quantity": ("数量", "商品数量", "件数", "quantity"),
        "unit_price": ("单价", "商品单价", "unit price", "unit_price"),
        "sales_amount": ("销售额", "销售金额", "订单金额", "成交金额", "sales amount", "sales_amount", "sales"),
        "customer_id": ("客户编号", "客户ID", "customer id", "customer_id"),
        "region": ("区域", "地区", "大区", "region"),
        "status": ("状态", "订单状态", "order status", "status"),
        "date": ("日期", "订单日期", "交易日期", "date"),
        "target_amount": ("目标额", "目标金额", "target amount", "target_amount", "target"),
    }
    STUDENT_SCORE_ALIASES: dict[str, tuple[str, ...]] = {
        "student_id": ("学号", "学生编号", "student id", "student_id"),
        "student_name": ("学生姓名", "姓名", "student name", "student_name"),
        "subject": ("科目", "学科", "课程", "subject"),
        "score": ("成绩", "分数", "得分", "score"),
        "class_name": ("班级", "班级名称", "class", "class name", "class_name"),
        "grade": ("年级", "年级名称", "grade"),
        "exam_name": ("考试", "考试名称", "测试名称", "exam name", "exam_name"),
        "exam_date": ("考试日期", "测试日期", "exam date", "exam_date"),
    }

    def __init__(self) -> None:
        self._aliases = self._build_alias_index()

    def map_dataframe(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[object]]]:
        """Return a renamed copy and JSON-serializable mapping metadata."""
        source_columns = [str(column) for column in frame.columns]
        canonical_columns = {target for target in self._aliases.values() if target in source_columns}
        candidates: dict[str, list[str]] = {}
        recognized_columns: set[str] = set(canonical_columns)

        for source in source_columns:
            target = self._aliases.get(self._normalize_header(source))
            if target is None:
                continue
            recognized_columns.add(source)
            if source != target:
                candidates.setdefault(target, []).append(source)

        rename_by_source: dict[str, str] = {}
        mappings: list[dict[str, str]] = []
        conflicts: list[dict[str, object]] = []
        for target in self._ordered_targets():
            target_candidates = candidates.get(target, [])
            if target in canonical_columns:
                if target_candidates:
                    conflicts.append({
                        "target": target,
                        "sources": [target, *target_candidates],
                        "reason": "canonical field already exists",
                    })
                continue
            if len(target_candidates) == 1:
                source = target_candidates[0]
                rename_by_source[source] = target
                mappings.append({"source": source, "target": target})
            elif len(target_candidates) > 1:
                conflicts.append({
                    "target": target,
                    "sources": target_candidates,
                    "reason": "multiple alias columns map to the same canonical field",
                })

        mapped = frame.copy()
        mapped.columns = [rename_by_source.get(str(column), column) for column in frame.columns]
        return mapped, {
            "mappings": mappings,
            "unmapped_columns": [source for source in source_columns if source not in recognized_columns],
            "conflicts": conflicts,
        }

    def _build_alias_index(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for target in self._ordered_targets():
            aliases[self._normalize_header(target)] = target
            for alias in self._all_aliases()[target]:
                normalized = self._normalize_header(alias)
                existing = aliases.get(normalized)
                if existing is not None and existing != target:
                    raise ValueError(f"Ambiguous canonical alias: {alias}")
                aliases[normalized] = target
        return aliases

    @classmethod
    def _all_aliases(cls) -> dict[str, tuple[str, ...]]:
        return {**cls.ORDER_ALIASES, **cls.STUDENT_SCORE_ALIASES}

    @classmethod
    def _ordered_targets(cls) -> tuple[str, ...]:
        return tuple(cls._all_aliases())

    @staticmethod
    def _normalize_header(value: object) -> str:
        normalized = unicodedata.normalize("NFKC", str(value)).strip().casefold()
        return re.sub(r"[\s_-]+", "", normalized)
