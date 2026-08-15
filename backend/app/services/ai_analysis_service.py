import json

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.services.metrics_service import MetricsService


class AIAnalysisService:
    def __init__(self) -> None:
        self.metrics_service = MetricsService()

    def generate_report(self, db, dataset: Dataset) -> dict:
        metrics = self.metrics_service.build_metrics(db, dataset)
        return {**self.analyze_metrics(metrics), "metrics": metrics}

    def analyze_metrics(self, metrics: dict) -> dict:
        """Convert calculated metrics into a capability-aware business insight."""
        analysis_context = self.build_analysis_context(metrics)
        fallback = self._build_rule_report(metrics, analysis_context)
        settings = get_settings()
        if settings.llm_provider == "deepseek" and settings.llm_api_key:
            return self._generate_with_deepseek(metrics, analysis_context, fallback)
        return fallback

    @staticmethod
    def build_analysis_context(metrics: dict) -> dict:
        """Expose only capabilities with real Python-calculated result values."""
        plan_by_id = {
            item["id"]: item for item in metrics.get("analysis_plan", [])
        }
        calculated_metrics = {
            "order_count": metrics.get("order_count"),
            "product_quantity": metrics.get("product_quantity"),
            "sales_total": metrics.get("sales_amount"),
            "region_sales": metrics.get("top_regions"),
            "sales_trend": metrics.get("growth_rate"),
            "target_completion": metrics.get("completion_rate"),
        }
        supported: dict[str, object] = {}
        for capability_id, value in calculated_metrics.items():
            plan_item = plan_by_id.get(capability_id)
            planned_as_supported = plan_item is None or bool(plan_item.get("supported"))
            if planned_as_supported and value is not None and value != []:
                supported[capability_id] = value

        skipped: list[dict] = []
        for item in metrics.get("analysis_plan", []):
            if item["id"] not in supported:
                skipped.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "missing_fields": item.get("missing_fields", []),
                        "reason": item.get("reason") or "未产生可用计算结果",
                    }
                )

        return {
            "available_fields": metrics.get("available_fields", []),
            "supported_analyses": supported,
            "skipped_analyses": skipped,
        }

    def _build_rule_report(self, metrics: dict, analysis_context: dict) -> dict:
        supported = analysis_context["supported_analyses"]
        sales_amount = supported.get("sales_total")
        completion_rate = supported.get("target_completion")
        growth_rate = supported.get("sales_trend")
        top_regions = supported.get("region_sales", [])
        highest_region = metrics.get("highest_sales_region")
        lowest_region = metrics.get("lowest_sales_region")
        volatility_data = metrics.get("sales_volatility")
        volatility = volatility_data.get("coefficient_of_variation") if volatility_data else None
        anomalies: list[str] = []
        problems: list[str] = []
        recommendations: list[str] = []
        summary_parts = [f"本次分析覆盖 {metrics['total_rows']} 条有效记录"]

        if "order_count" in supported:
            summary_parts.append(f"可统计订单数量 {supported['order_count']}")
        if "product_quantity" in supported:
            leading_product = supported["product_quantity"][0]
            summary_parts.append(
                f"商品销量排名第一为 {leading_product['name']}（{leading_product['value']}）"
            )
        if isinstance(sales_amount, dict):
            summary_parts.append(
                f"销售额总计 {sales_amount['total']}，平均销售额 {sales_amount.get('average')}"
            )

        if completion_rate is not None and completion_rate < 80:
            anomalies.append(f"整体目标完成率为 {completion_rate}%，低于 80% 预警线。")
            problems.append("销售产出与既定目标存在明显差距。")
            recommendations.append("优先复盘低完成率区域的客户覆盖、线索转化和资源投入。")

        if growth_rate is not None and growth_rate < 0:
            anomalies.append(f"销售额环比下降 {abs(growth_rate)}%，需关注最近销售节奏。")
            problems.append("近期销售趋势承压，存在增长动能不足风险。")
            recommendations.append("分析最近下降日期对应的客户、产品和渠道，制定短期追销计划。")

        if top_regions:
            low_completion_regions = [
                region
                for region in metrics.get("region_performance", [])
                if region["completion_rate"] is not None and region["completion_rate"] < 80
            ]
            if low_completion_regions:
                names = "、".join(region["name"] for region in low_completion_regions)
                anomalies.append(f"{names} 区域完成率偏低，需列入重点改进清单。")
                problems.append(f"{names} 区域的目标达成能力偏弱。")
                recommendations.append(f"为 {names} 设置周度追踪目标，并配置客户覆盖与销售辅导资源。")

            if (
                highest_region
                and lowest_region
                and highest_region["value"] > 0
                and highest_region["value"] >= lowest_region["value"] * 2
            ):
                anomalies.append(
                    f"区域销售差异明显：{highest_region['name']} 为 {highest_region['value']}，"
                    f"{lowest_region['name']} 为 {lowest_region['value']}。"
                )
                problems.append("区域经营效率不均衡，有效方法尚未完成复制。")
                recommendations.append(
                    f"沉淀 {highest_region['name']} 的客户开发流程，向 {lowest_region['name']} 开展对标赋能。"
                )

            if highest_region:
                recommendations.append(
                    f"保持 {highest_region['name']} 区域优势，并评估其经验的可复制性。"
                )

        if isinstance(sales_amount, dict) and volatility is not None and volatility >= 30:
            anomalies.append(f"销售波动系数为 {volatility}%，销售节奏稳定性偏低。")
            recommendations.append("建立日度异常监控与商机备案机制，降低收入集中波动。")

        if not anomalies:
            anomalies.append("当前已完成的可分析指标未触发预设风险规则，建议随数据补充持续复盘。")

        overview = "，".join(summary_parts) + "。"
        return {
            "mode": "rule_based",
            "summary": overview,
            "anomalies": anomalies,
            "business_problems": problems or ["当前可分析指标未显示明确业务风险，应持续积累数据并按周期复盘。"],
            "recommendations": recommendations or ["建立按周复盘机制，持续跟踪当前可分析指标。"],
            "report": "\n".join(
                [
                    f"数据概览：{overview}",
                    f"异常分析：{'；'.join(anomalies)}",
                    f"业务问题：{'；'.join(problems)}",
                    f"优化建议：{'；'.join(recommendations)}",
                ]
            ),
            "analysis_context": analysis_context,
        }

    @staticmethod
    def _generate_with_deepseek(metrics: dict, analysis_context: dict, fallback: dict) -> dict:
        from openai import OpenAI

        settings = get_settings()
        prompt = (
            "你是一名企业运营数据分析师。只可基于 Python 已计算的真实分析结果生成中文报告。"
            "只能分析 supported_analyses 和提供的 metrics；不得推断 skipped_analyses。"
            "缺失字段不代表数值为 0；不得编造销售额、完成率、区域、客户或退款数据。"
            "所有数字必须来自输入 metrics；真实为 0 的指标可以正常说明。"
            "可以说明某项因缺少字段未分析，但不得评价该项业务表现，也不得根据字段名称自行补充指标。"
            "返回 JSON：summary, anomalies, business_problems, recommendations, report。\n"
            f"分析上下文：{analysis_context}\n"
            f"真实指标：{metrics}"
        )
        try:
            response = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url).chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            generated = json.loads(response.choices[0].message.content or "{}")
            return {**fallback, **generated, "mode": "deepseek"}
        except Exception:
            return fallback
