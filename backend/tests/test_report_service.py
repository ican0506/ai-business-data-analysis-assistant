from io import BytesIO
from types import SimpleNamespace

from openpyxl import load_workbook

from app.services.report_service import ReportService


def test_report_service_resolves_a_real_cjk_font_for_charts() -> None:
    font_path = ReportService._resolve_chart_font_path()

    assert font_path.is_file()
    assert font_path.suffix.lower() in {".ttc", ".ttf", ".otf"}


def test_report_service_renders_pdf_summary_with_cjk_font() -> None:
    analysis = {
        "metrics": {
            "total_rows": 3,
            "sales_amount": {"total": 3600},
        },
        "summary": "华东区域销售表现领先。",
        "anomalies": ["华北完成率偏低。"],
        "recommendations": ["优先优化华北区域客户覆盖。"],
    }

    image = ReportService._build_pdf_summary_image(SimpleNamespace(original_filename="销售数据.csv"), analysis)

    assert image.getvalue().startswith(b"\x89PNG")


def test_report_service_builds_enterprise_overview_rows() -> None:
    metrics = {
        "sales_amount": {"total": 3600, "average": 1200},
        "completion_rate": 84.44,
        "highest_sales_region": {"name": "\u534e\u4e1c", "value": 2200},
        "lowest_sales_region": {"name": "\u534e\u5317", "value": 600},
        "region_ranking": [
            {"name": "\u534e\u4e1c", "value": 2200},
            {"name": "\u534e\u5357", "value": 800},
            {"name": "\u534e\u5317", "value": 600},
        ],
    }

    rows = dict(ReportService._overview_rows(metrics))

    assert rows["\u9500\u552e\u989d\u603b\u8ba1"] == 3600
    assert rows["\u5e73\u5747\u9500\u552e\u989d"] == 1200
    assert rows["\u6700\u5927\u9500\u552e\u533a\u57df"] == "\u534e\u4e1c\uff082200\uff09"
    assert rows["\u6700\u4f4e\u9500\u552e\u533a\u57df"] == "\u534e\u5317\uff08600\uff09"
    assert rows["\u5b8c\u6210\u7387"] == "84.44%"
    assert "1. \u534e\u4e1c\uff1a2200" in rows["\u533a\u57df TOP \u6392\u540d"]


def test_report_service_omits_unavailable_sales_and_lists_skipped_analyses() -> None:
    metrics = {
        "total_rows": 2,
        "sales_amount": None,
        "completion_rate": None,
        "order_count": 2,
        "product_quantity": [{"name": "A", "value": 5}],
        "region_ranking": [],
        "top_regions": [],
        "analysis_plan": [
            {
                "id": "sales_total",
                "name": "销售额分析",
                "supported": False,
                "missing_fields": ["sales_amount"],
                "reason": "缺少所需字段",
            }
        ],
    }

    rows = dict(ReportService._overview_rows(metrics))

    assert "销售额总计" not in rows
    assert rows["订单数量"] == 2
    assert "商品销量排名" in rows
    assert ReportService._skipped_analysis_rows(metrics) == ["销售额分析：缺少 sales_amount 字段"]


def test_report_service_keeps_real_zero_sales_in_overview() -> None:
    metrics = {
        "sales_amount": {"total": 0, "average": 0},
        "completion_rate": None,
        "region_ranking": [],
        "top_regions": [],
        "order_count": None,
        "product_quantity": [],
        "analysis_plan": [],
    }

    rows = dict(ReportService._overview_rows(metrics))

    assert rows["销售额总计"] == 0
    assert rows["平均销售额"] == 0


def test_report_exports_skip_unavailable_sales_and_region_chart() -> None:
    metrics = {
        "total_rows": 2,
        "sales_amount": None,
        "completion_rate": None,
        "order_count": 2,
        "product_quantity": [{"name": "A", "value": 5}],
        "region_ranking": [],
        "top_regions": [],
        "analysis_plan": [
            {
                "id": "sales_total",
                "name": "销售额分析",
                "supported": False,
                "missing_fields": ["sales_amount"],
                "reason": "缺少所需字段",
            }
        ],
    }
    analysis = {
        "mode": "rule_based",
        "metrics": metrics,
        "summary": "可统计订单与商品销量。",
        "anomalies": ["未触发预设风险规则。"],
        "business_problems": ["需持续积累数据。"],
        "recommendations": ["按周复盘。"],
    }
    service = ReportService()
    service.analysis_service = SimpleNamespace(generate_report=lambda *_args: analysis)
    dataset = SimpleNamespace(original_filename="minimal.csv")

    excel = load_workbook(BytesIO(service.build_excel(None, dataset)))
    labels = [excel.active.cell(row=row, column=1).value for row in range(1, excel.active.max_row + 1)]

    assert "销售额总计" not in labels
    assert excel.active._charts == []
    assert service.build_word(None, dataset).startswith(b"PK")
    assert service.build_pdf(None, dataset).startswith(b"%PDF")
