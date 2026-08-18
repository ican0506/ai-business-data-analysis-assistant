from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping

import pandas as pd

ORDER_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "order_id": ("订单编号", "订单号", "order id", "order_id", "orderid"),
    "product": ("商品", "商品名称", "产品", "产品名称", "product"),
    "quantity": ("数量", "商品数量", "件数", "quantity"),
    "unit_price": ("单价", "商品单价", "unit price", "unit_price"),
    "sales_amount": ("销售额", "销售金额", "订单金额", "成交金额", "订单实付金额", "order amount", "order_amount", "sales amount", "sales_amount", "sales"),
    "customer_id": ("客户编号", "客户ID", "用户编号", "用户ID", "user id", "user_id", "customer id", "customer_id"),
    "customer_name": ("客户姓名", "客户名称", "用户姓名", "用户名", "user name", "user_name", "customer name", "customer_name"),
    "phone": ("phone", "mobile", "mobile_phone", "mobile phone", "tel", "telephone", "手机号", "手机号码", "手机", "联系电话", "联系电话号码", "电话"),
    "email": ("email", "e-mail", "mail", "email_address", "email address", "邮箱", "电子邮箱", "电子邮件"),
    "category": ("商品类别", "商品品类", "订单品类", "分类", "商品分类", "产品分类", "品类", "category"),
    "region": ("区域", "地区", "大区", "城市", "city", "region"),
    "status": ("状态", "订单状态", "order status", "order_status", "status"),
    "date": ("日期", "订单日期", "交易日期", "下单时间", "订单时间", "order time", "order_time", "date"),
    "discount": ("折扣", "折扣率", "discount"),
    "payment_method": ("支付方式", "付款方式", "支付渠道", "payment method", "payment_method"),
    "gender": ("性别", "gender"),
    "age": ("年龄", "age"),
    "target_amount": ("目标额", "目标金额", "target amount", "target_amount", "target"),
}
STUDENT_SCORE_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "student_id": ("学号", "学生编号", "student id", "student_id"),
    "student_name": ("学生姓名", "姓名", "student name", "student_name"),
    "subject": ("科目", "学科", "课程", "subject"),
    "score": ("成绩", "分数", "得分", "score"),
    "class_name": ("班级", "班级名称", "class", "class name", "class_name"),
    "grade": ("年级", "年级名称", "grade"),
    "exam_name": ("考试", "考试名称", "测试名称", "exam name", "exam_name"),
    "exam_date": ("考试日期", "测试日期", "exam date", "exam_date"),
}
INVENTORY_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "product_id": ("商品编号", "产品编号", "SKU", "sku", "product id", "product_id"),
    "product_name": ("商品名称", "产品名称", "商品", "产品", "product name", "product_name"),
    "category": ("分类", "商品分类", "产品分类", "品类", "商品类别", "商品品类", "订单品类", "category"),
    "stock_quantity": ("库存", "库存数量", "当前库存", "库存量", "stock", "stock quantity", "stock_quantity"),
    "safety_stock": ("安全库存", "最低库存", "库存下限", "safety stock", "safety_stock"),
    "unit_cost": ("成本", "单位成本", "单价成本", "unit cost", "unit_cost"),
    "warehouse": ("仓库", "仓库名称", "库房", "warehouse"),
    "supplier": ("供应商", "supplier"),
    "inbound_quantity": ("入库数量", "入库量", "inbound quantity", "inbound_quantity"),
    "outbound_quantity": ("出库数量", "出库量", "outbound quantity", "outbound_quantity"),
    "inventory_date": ("库存日期", "盘点日期", "inventory date", "inventory_date"),
}
KNOWN_CANONICAL_FIELDS: tuple[str, ...] = tuple(
    {**ORDER_FIELD_ALIASES, **STUDENT_SCORE_FIELD_ALIASES, **INVENTORY_FIELD_ALIASES}
)

class CanonicalFieldMapper:
    """Map deterministic header aliases on an in-memory analysis copy only."""

    ORDER_ALIASES = ORDER_FIELD_ALIASES
    STUDENT_SCORE_ALIASES = STUDENT_SCORE_FIELD_ALIASES
    INVENTORY_ALIASES = INVENTORY_FIELD_ALIASES

    def __init__(self) -> None:
        self._ambiguous_aliases: dict[str, tuple[str, ...]] = {}
        self._aliases = self._build_alias_index()

    def map_dataframe(
        self,
        frame: pd.DataFrame,
        overrides: Mapping[str, str] | None = None,
    ) -> tuple[pd.DataFrame, dict[str, list[object]]]:
        """Return a renamed copy and JSON-serializable mapping metadata."""
        source_columns = [str(column) for column in frame.columns]
        normalized_overrides = dict(overrides or {})
        self.validate_overrides(frame, normalized_overrides)
        canonical_columns = set(KNOWN_CANONICAL_FIELDS).intersection(source_columns)
        candidates: dict[str, list[str]] = {}
        recognized_columns: set[str] = set(canonical_columns).union(normalized_overrides)

        for source in source_columns:
            target = self._target_for_source(source, source_columns)
            if target is None:
                continue
            recognized_columns.add(source)
            if source in normalized_overrides:
                continue
            if source != target:
                candidates.setdefault(target, []).append(source)

        rename_by_source = dict(normalized_overrides)
        mappings: list[dict[str, str]] = [
            {"source": source, "target": target, "method": "override"}
            for source, target in normalized_overrides.items()
        ]
        conflicts: list[dict[str, object]] = []
        for target in self._ordered_targets():
            target_candidates = candidates.get(target, [])
            override_sources = [
                source for source, override_target in normalized_overrides.items()
                if override_target == target
            ]
            if override_sources:
                if target_candidates:
                    conflicts.append({
                        "target": target,
                        "sources": [*override_sources, *target_candidates],
                        "reason": "automatic mapping suppressed by override",
                    })
                continue
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
                mappings.append({"source": source, "target": target, "method": "automatic"})
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

    def validate_overrides(self, frame: pd.DataFrame, overrides: Mapping[str, str]) -> None:
        source_columns = {str(column) for column in frame.columns}
        targets = list(overrides.values())
        for source, target in overrides.items():
            if source not in source_columns:
                raise ValueError(f"source column does not exist in dataset: {source}")
            if target not in KNOWN_CANONICAL_FIELDS:
                raise ValueError(f"unknown canonical target field: {target}")
            if source in KNOWN_CANONICAL_FIELDS and source != target:
                raise ValueError("source column is already a canonical field")
            if target in source_columns and source != target:
                raise ValueError("target canonical field already exists in dataset")
        duplicates = sorted({target for target in targets if targets.count(target) > 1})
        if duplicates:
            raise ValueError(
                f'multiple source columns map to canonical field "{duplicates[0]}"'
            )

    def _build_alias_index(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for target in self._ordered_targets():
            aliases[self._normalize_header(target)] = target
            for alias in self._all_aliases()[target]:
                normalized = self._normalize_header(alias)
                existing = aliases.get(normalized)
                if existing is not None and existing != target:
                    self._ambiguous_aliases[normalized] = tuple(
                        dict.fromkeys((*self._ambiguous_aliases.get(normalized, (existing,)), target))
                    )
                    aliases.pop(normalized, None)
                    continue
                aliases[normalized] = target
        return aliases

    @classmethod
    def _all_aliases(cls) -> dict[str, tuple[str, ...]]:
        return {**cls.ORDER_ALIASES, **cls.STUDENT_SCORE_ALIASES, **cls.INVENTORY_ALIASES}

    def _target_for_source(self, source: str, source_columns: list[str]) -> str | None:
        normalized = self._normalize_header(source)
        target = self._aliases.get(normalized)
        if target is not None:
            return target
        candidates = self._ambiguous_aliases.get(normalized)
        if not candidates:
            return None
        static_targets = {
            self._aliases.get(self._normalize_header(column))
            for column in source_columns
        }
        has_inventory_context = bool(
            static_targets.intersection({"product_id", "stock_quantity", "safety_stock", "unit_cost", "warehouse", "supplier", "inbound_quantity", "outbound_quantity", "inventory_date"})
        )
        has_order_context = bool(
            static_targets.intersection({"order_id", "quantity", "unit_price", "sales_amount", "customer_id", "region", "status", "date", "target_amount"})
        )
        if has_inventory_context and not has_order_context and "product_name" in candidates:
            return "product_name"
        if "product" in candidates:
            return "product"
        return None

    @classmethod
    def _ordered_targets(cls) -> tuple[str, ...]:
        return tuple(cls._all_aliases())

    @staticmethod
    def _normalize_header(value: object) -> str:
        normalized = unicodedata.normalize("NFKC", str(value)).strip().casefold()
        return re.sub(r"[\s_-]+", "", normalized)
