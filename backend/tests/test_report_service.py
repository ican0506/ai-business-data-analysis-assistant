from types import SimpleNamespace

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
