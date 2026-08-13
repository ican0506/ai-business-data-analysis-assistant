from app.services.ai_analysis_service import AIAnalysisService


def test_analyze_metrics_returns_business_insight_json() -> None:
    metrics = {
        "total_rows": 2,
        "sales_amount": {"total": 1200, "average": 600},
        "completion_rate": 60.0,
        "growth_rate": -50.0,
        "highest_sales_region": {"name": "east", "value": 800},
        "lowest_sales_region": {"name": "south", "value": 400},
        "region_performance": [
            {"name": "east", "sales_amount": 800, "target_amount": 1000, "completion_rate": 80.0},
            {"name": "south", "sales_amount": 400, "target_amount": 1000, "completion_rate": 40.0},
        ],
        "sales_volatility": {"standard_deviation": 200, "coefficient_of_variation": 33.33},
    }

    insight = AIAnalysisService().analyze_metrics(metrics)

    assert {"summary", "anomalies", "business_problems", "recommendations"} <= insight.keys()
    assert isinstance(insight["summary"], str)
    assert isinstance(insight["anomalies"], list)
    assert isinstance(insight["business_problems"], list)
    assert isinstance(insight["recommendations"], list)
    assert "metrics" not in insight
