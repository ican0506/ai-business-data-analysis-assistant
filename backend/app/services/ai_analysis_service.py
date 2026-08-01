import json

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.services.metrics_service import MetricsService


class AIAnalysisService:
    def __init__(self) -> None:
        self.metrics_service = MetricsService()

    def generate_report(self, db, dataset: Dataset) -> dict:
        metrics = self.metrics_service.build_metrics(db, dataset)
        fallback = self._build_rule_report(metrics)
        settings = get_settings()
        if settings.llm_provider == "deepseek" and settings.llm_api_key:
            return self._generate_with_deepseek(metrics, fallback)
        return fallback

    def _build_rule_report(self, metrics: dict) -> dict:
        completion_rate = metrics["completion_rate"]
        top_region = metrics["top_regions"][0] if metrics["top_regions"] else None
        anomalies = []
        problems = []
        recommendations = []
        if completion_rate is not None and completion_rate < 80:
            anomalies.append(f"整体目标完成率为 {completion_rate}%，低于 80% 预警线。")
            problems.append("销售产出与既定目标存在明显差距。")
            recommendations.append("优先复盘低完成区域的客户覆盖、线索转化和资源投入。")
        if top_region:
            recommendations.append(f"沉淀 {top_region['name']} 区域的有效打法，并评估向其他区域复制。")
        if not anomalies:
            anomalies.append("当前未发现触发预警阈值的关键指标。")
        return {
            "mode": "rule_based",
            "summary": f"本次分析覆盖 {metrics['total_rows']} 条有效记录，销售额总计 {metrics['sales_amount']['total']}。",
            "anomalies": anomalies,
            "business_problems": problems or ["核心指标运行平稳，建议持续跟踪趋势变化。"],
            "recommendations": recommendations or ["保持当前节奏，并建立按周复盘机制。"],
            "report": "\n".join(["数据摘要：" + f"有效记录 {metrics['total_rows']} 条。", "异常发现：" + "；".join(anomalies), "优化建议：" + "；".join(recommendations or ["持续监控核心指标。"])],),
            "metrics": metrics,
        }

    @staticmethod
    def _generate_with_deepseek(metrics: dict, fallback: dict) -> dict:
        from openai import OpenAI

        settings = get_settings()
        prompt = (
            "你是一名企业运营数据分析师。基于以下真实指标生成中文报告，"
            "不得编造数据。返回 JSON：summary, anomalies, business_problems, recommendations, report。\n"
            f"指标：{metrics}"
        )
        try:
            response = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url).chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            generated = json.loads(response.choices[0].message.content or "{}")
            return {**fallback, **generated, "mode": "deepseek", "metrics": metrics}
        except Exception:
            return fallback
