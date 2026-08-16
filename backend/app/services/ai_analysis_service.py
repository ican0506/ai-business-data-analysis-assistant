import json
import logging

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.services.metrics_service import MetricsService


logger = logging.getLogger(__name__)


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
        selected_module = metrics.get("selected_module") or {"id": "order", "name": "订单分析"}
        module_id = selected_module.get("id", "order")
        if module_id == "student_score":
            calculated_metrics = (metrics.get("student_score_analysis") or {}).copy()
        elif module_id == "inventory":
            calculated_metrics = (metrics.get("inventory_analysis") or {}).copy()
        elif module_id == "generic":
            calculated_metrics = {"generic_analysis": metrics.get("generic_analysis")}
        else:
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
            "selected_module": selected_module,
            "available_fields": metrics.get("available_fields", []),
            "analysis_plan": metrics.get("analysis_plan", []),
            "supported_analyses": supported,
            "skipped_analyses": skipped,
        }

    def _build_rule_report(self, metrics: dict, analysis_context: dict) -> dict:
        module_id = analysis_context["selected_module"].get("id")
        if module_id == "student_score":
            return self._build_student_score_rule_report(metrics, analysis_context)
        if module_id == "inventory":
            return self._build_inventory_rule_report(metrics, analysis_context)
        if module_id == "generic":
            return self._build_generic_rule_report(metrics, analysis_context)
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
    def _build_student_score_rule_report(metrics: dict, analysis_context: dict) -> dict:
        supported = analysis_context["supported_analyses"]
        summary_parts = [f"本次成绩分析覆盖 {metrics.get('total_rows', 0)} 条有效记录"]
        anomalies: list[str] = []
        problems: list[str] = []
        recommendations: list[str] = []

        student_count = supported.get("student_count")
        score_summary = supported.get("score_summary")
        subject_score = supported.get("subject_score", [])
        class_score = supported.get("class_score", [])
        student_score = supported.get("student_score", [])
        exam_trend = supported.get("exam_trend", [])

        if student_count is not None:
            summary_parts.append(f"学生数量 {student_count}")
        if isinstance(score_summary, dict):
            summary_parts.append(
                "有效成绩数量 {count}，平均分 {average}，中位数 {median}，最高分 {maximum}，最低分 {minimum}".format(
                    **score_summary
                )
            )
        if subject_score:
            best_subject, lowest_subject = subject_score[0], subject_score[-1]
            summary_parts.append(
                f"学科平均分最高为 {best_subject['name']}（{best_subject['average']}）"
            )
            if best_subject["name"] != lowest_subject["name"]:
                anomalies.append(
                    f"学科平均分存在差异：{best_subject['name']} 为 {best_subject['average']}，"
                    f"{lowest_subject['name']} 为 {lowest_subject['average']}。"
                )
                recommendations.append(
                    f"结合 {lowest_subject['name']} 的现有成绩数据安排针对性复盘，并跟踪后续考试变化。"
                )
        if class_score:
            best_class, lowest_class = class_score[0], class_score[-1]
            summary_parts.append(
                f"班级平均分较高的是 {best_class['name']}（{best_class['average']}）"
            )
            if best_class["name"] != lowest_class["name"]:
                anomalies.append(
                    f"班级平均分存在差异：{best_class['name']} 为 {best_class['average']}，"
                    f"{lowest_class['name']} 为 {lowest_class['average']}。"
                )
                recommendations.append("对比已有班级的教学安排与考试数据，识别可复用的改进做法。")
        if student_score:
            leading_student = student_score[0]
            student_label = leading_student.get("student_name") or leading_student["student_id"]
            summary_parts.append(
                f"当前已计算成绩中平均分较高的学生为 {student_label}（{leading_student['average']}）"
            )
        if len(exam_trend) >= 2:
            first, last = exam_trend[0], exam_trend[-1]
            change = round(float(last["average"]) - float(first["average"]), 2)
            if change > 0:
                trend_text = f"从 {first['name']} 到 {last['name']}，平均成绩上升 {change} 分。"
            elif change < 0:
                trend_text = f"从 {first['name']} 到 {last['name']}，平均成绩下降 {abs(change)} 分。"
            else:
                trend_text = f"从 {first['name']} 到 {last['name']}，平均成绩保持不变。"
            anomalies.append(trend_text)
            recommendations.append("基于已存在的考试趋势持续复盘，并补充后续考试数据验证变化。")

        if not anomalies:
            anomalies.append("当前已计算的成绩指标未触发额外差异或趋势结论。")
        if not problems:
            problems.append("仅基于当前已计算的成绩指标进行描述，未对缺失指标作业务评价。")
        if not recommendations:
            recommendations.append("持续补充真实考试、学科或班级数据，以支持后续对比分析。")

        overview = "；".join(summary_parts) + "。"
        return {
            "mode": "rule_based",
            "summary": overview,
            "anomalies": anomalies,
            "business_problems": problems,
            "recommendations": recommendations,
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
    def _build_generic_rule_report(metrics: dict, analysis_context: dict) -> dict:
        generic_analysis = analysis_context["supported_analyses"].get("generic_analysis") or {}
        row_count = generic_analysis.get("row_count", metrics.get("total_rows", 0))
        column_count = len(generic_analysis.get("column_profile", []))
        missing_columns = [
            item["column"]
            for item in generic_analysis.get("missing_value_analysis", [])
            if item.get("missing_count", 0) > 0
        ]
        overview = f"本次通用数据分析覆盖 {row_count} 行、{column_count} 列。"
        anomalies = (
            [f"存在缺失值的列：{'、'.join(missing_columns)}。"]
            if missing_columns
            else ["当前通用数据未发现已统计的缺失值。"]
        )
        return {
            "mode": "rule_based",
            "summary": overview,
            "anomalies": anomalies,
            "business_problems": ["通用数据仅输出行列与缺失情况，不推断业务领域指标。"],
            "recommendations": ["补充字段业务含义后，可接入对应领域模块进行进一步分析。"],
            "report": f"数据概览：{overview}\n异常分析：{'；'.join(anomalies)}",
            "analysis_context": analysis_context,
        }

    @staticmethod
    def _build_inventory_rule_report(metrics: dict, analysis_context: dict) -> dict:
        """Describe only inventory metrics calculated by InventoryAnalyzer."""
        supported = analysis_context["supported_analyses"]
        summary_parts = [f"本次库存分析覆盖 {metrics.get('total_rows', 0)} 条有效记录"]
        anomalies: list[str] = []
        problems: list[str] = []
        recommendations: list[str] = []

        inventory_count = supported.get("inventory_count")
        stock_summary = supported.get("stock_summary")
        low_stock = supported.get("low_stock_analysis", [])
        inventory_value = supported.get("inventory_value")
        warehouse_stock = supported.get("warehouse_stock", [])
        inventory_trend = supported.get("inventory_trend", [])

        if inventory_count is not None:
            summary_parts.append(f"商品数量 {inventory_count}")
        if isinstance(stock_summary, dict):
            summary_parts.append(
                f"库存总量 {stock_summary.get('total')}，平均库存 {stock_summary.get('average')}"
            )
        if isinstance(inventory_value, dict):
            summary_parts.append(f"库存价值总计 {inventory_value.get('total')}")
        if warehouse_stock:
            leading_warehouse = warehouse_stock[0]
            summary_parts.append(
                f"库存量较高的仓库为 {leading_warehouse['name']}（{leading_warehouse['value']}）"
            )

        if low_stock:
            names = "、".join(
                item.get("product_name") or item.get("product_id") or "未命名商品"
                for item in low_stock[:5]
            )
            anomalies.append(f"存在 {len(low_stock)} 个低库存商品：{names}。")
            problems.append("已计算的安全库存与当前库存之间存在缺口。")
            recommendations.append("核对低库存商品的当前库存与安全库存记录，并安排后续人工跟踪。")

        if len(inventory_trend) >= 2:
            first, last = inventory_trend[0], inventory_trend[-1]
            change = round(float(last["value"]) - float(first["value"]), 2)
            if change > 0:
                anomalies.append(f"库存总量从 {first['name']} 到 {last['name']} 上升 {change}。")
            elif change < 0:
                anomalies.append(f"库存总量从 {first['name']} 到 {last['name']} 下降 {abs(change)}。")
            else:
                anomalies.append(f"库存总量从 {first['name']} 到 {last['name']} 保持不变。")
            recommendations.append("持续记录库存日期数据，以便基于真实库存变化进行复盘。")

        if not anomalies:
            anomalies.append("当前已计算的库存指标未触发低库存或趋势异常结论。")
        if not problems:
            problems.append("仅基于当前已计算的库存指标进行描述，未对缺失库存指标作业务评价。")
        if not recommendations:
            recommendations.append("持续补充真实库存、安全库存或仓库字段，以支持更完整的库存复盘。")

        overview = "；".join(summary_parts) + "。"
        return {
            "mode": "rule_based",
            "summary": overview,
            "anomalies": anomalies,
            "business_problems": problems,
            "recommendations": recommendations,
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
    def _deepseek_metrics_payload(metrics: dict, analysis_context: dict) -> dict:
        selected_module = analysis_context.get("selected_module") or {"id": "order"}
        if selected_module.get("id") == "student_score":
            return {
                "selected_module": selected_module,
                "available_fields": analysis_context.get("available_fields", []),
                "analysis_plan": analysis_context.get("analysis_plan", []),
                "student_score_analysis": metrics.get("student_score_analysis"),
            }
        if selected_module.get("id") == "generic":
            return {
                "selected_module": selected_module,
                "available_fields": analysis_context.get("available_fields", []),
                "analysis_plan": analysis_context.get("analysis_plan", []),
                "generic_analysis": metrics.get("generic_analysis"),
            }
        if selected_module.get("id") == "inventory":
            return {
                "selected_module": selected_module,
                "available_fields": analysis_context.get("available_fields", []),
                "analysis_plan": analysis_context.get("analysis_plan", []),
                "inventory_analysis": metrics.get("inventory_analysis"),
            }
        return metrics

    @staticmethod
    def _generate_with_deepseek(metrics: dict, analysis_context: dict, fallback: dict) -> dict:
        from openai import OpenAI

        settings = get_settings()
        selected_module = (analysis_context.get("selected_module") or {"id": "order"}).get("id")
        student_constraints = (
            "当前是学生成绩数据：只能使用 student_score_analysis；不得重新计算原始成绩；"
            "不得假设 60 分为及格线；不得推断及格率、优秀率、GPA、排名规则或学生画像；"
            "不得编造学生、学科、班级或考试。\n"
            if selected_module == "student_score"
            else ""
        )
        inventory_constraints = (
            "当前是库存数据：只能使用 inventory_analysis；不得推断库存周转率、采购周期、补货天数、"
            "需求预测、缺货概率、EOQ 或 ABC 分类；不得编造商品、仓库、供应商或库存指标。\n"
            if selected_module == "inventory"
            else ""
        )
        prompt = (
            "你是一名企业运营数据分析师。只可基于 Python 已计算的真实分析结果生成中文报告。"
            "只能分析 supported_analyses 和提供的 metrics；不得推断 skipped_analyses。"
            "缺失字段不代表数值为 0；不得编造销售额、完成率、区域、客户或退款数据。"
            "所有数字必须来自输入 metrics；真实为 0 的指标可以正常说明。"
            "可以说明某项因缺少字段未分析，但不得评价该项业务表现，也不得根据字段名称自行补充指标。"
            f"{student_constraints}{inventory_constraints}"
            "返回 JSON：summary, anomalies, business_problems, recommendations, report。\n"
            f"分析上下文：{analysis_context}\n"
            f"真实指标：{AIAnalysisService._deepseek_metrics_payload(metrics, analysis_context)}"
        )
        try:
            client = OpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                timeout=settings.llm_timeout_seconds,
                max_retries=0,
            )
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            generated = json.loads(response.choices[0].message.content or "{}")
            return {**fallback, **generated, "mode": "deepseek"}
        except Exception as error:
            logger.warning(
                "LLM analysis failed; using rule-based fallback provider=%s model=%s error_type=%s",
                settings.llm_provider,
                settings.llm_model,
                type(error).__name__,
            )
            return fallback
