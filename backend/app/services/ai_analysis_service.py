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
        """Convert sales-metrics JSON into structured business insight JSON."""
        fallback = self._build_rule_report(metrics)
        settings = get_settings()
        if settings.llm_provider == "deepseek" and settings.llm_api_key:
            return self._generate_with_deepseek(metrics, fallback)
        return fallback

    def _build_rule_report(self, metrics: dict) -> dict:
        completion_rate = metrics["completion_rate"]
        growth_rate = metrics["growth_rate"]
        highest_region = metrics.get("highest_sales_region")
        lowest_region = metrics.get("lowest_sales_region")
        low_completion_regions = [
            region
            for region in metrics.get("region_performance", [])
            if region["completion_rate"] is not None and region["completion_rate"] < 80
        ]
        volatility = metrics.get("sales_volatility", {}).get("coefficient_of_variation")
        anomalies: list[str] = []
        problems: list[str] = []
        recommendations: list[str] = []

        if completion_rate is not None and completion_rate < 80:
            anomalies.append(f"\u6574\u4f53\u76ee\u6807\u5b8c\u6210\u7387\u4e3a {completion_rate}%\uff0c\u4f4e\u4e8e 80% \u9884\u8b66\u7ebf\u3002")
            problems.append("\u9500\u552e\u4ea7\u51fa\u4e0e\u65e2\u5b9a\u76ee\u6807\u5b58\u5728\u660e\u663e\u5dee\u8ddd\u3002")
            recommendations.append("\u4f18\u5148\u590d\u76d8\u4f4e\u5b8c\u6210\u533a\u57df\u7684\u5ba2\u6237\u8986\u76d6\u3001\u7ebf\u7d22\u8f6c\u5316\u548c\u8d44\u6e90\u6295\u5165\u3002")

        if growth_rate is not None and growth_rate < 0:
            anomalies.append(f"\u9500\u552e\u989d\u73af\u6bd4\u4e0b\u964d {abs(growth_rate)}%\uff0c\u9700\u5173\u6ce8\u6700\u8fd1\u9500\u552e\u8282\u594f\u3002")
            problems.append("\u8fd1\u671f\u9500\u552e\u8d8b\u52bf\u627f\u538b\uff0c\u5b58\u5728\u589e\u957f\u52a8\u80fd\u4e0d\u8db3\u98ce\u9669\u3002")
            recommendations.append("\u5206\u6790\u6700\u8fd1\u4e0b\u964d\u65e5\u671f\u5bf9\u5e94\u7684\u5ba2\u6237\u3001\u4ea7\u54c1\u548c\u6e20\u9053\uff0c\u5236\u5b9a\u77ed\u671f\u8ffd\u9500\u8ba1\u5212\u3002")

        if low_completion_regions:
            names = "\u3001".join(region["name"] for region in low_completion_regions)
            anomalies.append(f"{names} \u533a\u57df\u5b8c\u6210\u7387\u504f\u4f4e\uff0c\u9700\u5217\u5165\u91cd\u70b9\u6539\u8fdb\u6e05\u5355\u3002")
            problems.append(f"{names} \u533a\u57df\u7684\u76ee\u6807\u8fbe\u6210\u80fd\u529b\u504f\u5f31\u3002")
            recommendations.append(f"\u4e3a {names} \u8bbe\u7f6e\u5468\u5ea6\u8ffd\u8e2a\u76ee\u6807\uff0c\u5e76\u914d\u7f6e\u5ba2\u6237\u8986\u76d6\u4e0e\u9500\u552e\u8f85\u5bfc\u8d44\u6e90\u3002")

        if highest_region and lowest_region and highest_region["value"] > 0 and highest_region["value"] >= lowest_region["value"] * 2:
            anomalies.append(
                f"\u533a\u57df\u9500\u552e\u5dee\u5f02\u660e\u663e\uff1a{highest_region['name']} \u4e3a {highest_region['value']}\uff0c"
                f"{lowest_region['name']} \u4e3a {lowest_region['value']}\u3002"
            )
            problems.append("\u533a\u57df\u7ecf\u8425\u6548\u7387\u4e0d\u5747\u8861\uff0c\u6709\u6548\u65b9\u6cd5\u5c1a\u672a\u5b8c\u6210\u590d\u5236\u3002")
            recommendations.append(f"\u6c89\u6dc0 {highest_region['name']} \u7684\u5ba2\u6237\u5f00\u53d1\u6d41\u7a0b\uff0c\u5411 {lowest_region['name']} \u5f00\u5c55\u5bf9\u6807\u8d4b\u80fd\u3002")

        if volatility is not None and volatility >= 30:
            anomalies.append(f"\u9500\u552e\u6ce2\u52a8\u7cfb\u6570\u4e3a {volatility}%\uff0c\u9500\u552e\u8282\u594f\u7a33\u5b9a\u6027\u504f\u4f4e\u3002")
            recommendations.append("\u5efa\u7acb\u65e5\u5ea6\u5f02\u5e38\u76d1\u63a7\u4e0e\u5546\u673a\u5907\u6848\u673a\u5236\uff0c\u964d\u4f4e\u6536\u5165\u96c6\u4e2d\u6ce2\u52a8\u3002")

        if not anomalies:
            anomalies.append(
                "\u5f53\u524d\u6307\u6807\u672a\u89e6\u53d1\u4f4e\u5b8c\u6210\u7387\u3001\u4e0b\u964d\u8d8b\u52bf\u6216\u9ad8\u6ce2\u52a8\u9884\u8b66\uff0c\u5efa\u8bae\u6301\u7eed\u6309\u5468\u590d\u76d8\u3002"
            )
        if highest_region:
            recommendations.append(f"\u4fdd\u6301 {highest_region['name']} \u533a\u57df\u4f18\u52bf\uff0c\u5e76\u8bc4\u4f30\u5176\u7ecf\u9a8c\u7684\u53ef\u590d\u5236\u6027\u3002")

        sales_amount = metrics["sales_amount"]
        overview = (
            f"\u672c\u6b21\u5206\u6790\u8986\u76d6 {metrics['total_rows']} \u6761\u6709\u6548\u8bb0\u5f55\uff0c"
            f"\u9500\u552e\u989d\u603b\u8ba1 {sales_amount['total']}\uff0c\u5e73\u5747\u9500\u552e\u989d {sales_amount['average']}\u3002"
        )
        return {
            "mode": "rule_based",
            "summary": overview,
            "anomalies": anomalies,
            "business_problems": problems or ["\u76ee\u524d\u5173\u952e\u6307\u6807\u7a33\u5b9a\uff0c\u5e94\u6301\u7eed\u4f18\u5316\u533a\u57df\u7ecf\u8425\u6548\u7387\u3002"],
            "recommendations": recommendations or ["\u5efa\u7acb\u6309\u5468\u590d\u76d8\u673a\u5236\uff0c\u6301\u7eed\u8ddf\u8e2a\u6838\u5fc3\u6307\u6807\u3002"],
            "report": "\n".join(
                [
                    f"\u6570\u636e\u6982\u89c8\uff1a{overview}",
                    f"\u5f02\u5e38\u5206\u6790\uff1a{'\uff1b'.join(anomalies)}",
                    f"\u4e1a\u52a1\u95ee\u9898\uff1a{'\uff1b'.join(problems)}",
                    f"\u4f18\u5316\u5efa\u8bae\uff1a{'\uff1b'.join(recommendations)}",
                ]
            ),
        }

    @staticmethod
    def _generate_with_deepseek(metrics: dict, fallback: dict) -> dict:
        from openai import OpenAI

        settings = get_settings()
        prompt = (
            "\u4f60\u662f\u4e00\u540d\u4f01\u4e1a\u8fd0\u8425\u6570\u636e\u5206\u6790\u5e08\u3002\u57fa\u4e8e\u4ee5\u4e0b\u771f\u5b9e\u6307\u6807\u751f\u6210\u4e2d\u6587\u62a5\u544a\uff0c\u4e0d\u5f97\u7f16\u9020\u6570\u636e\u3002"
            "\u8fd4\u56de JSON\uff1asummary, anomalies, business_problems, recommendations, report\u3002\n"
            f"\u6307\u6807\uff1a{metrics}"
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
