from io import BytesIO

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill

from app.models.dataset import Dataset
from app.services.ai_analysis_service import AIAnalysisService


class ReportService:
    def __init__(self) -> None:
        self.analysis_service = AIAnalysisService()

    def build_excel(self, db, dataset: Dataset) -> bytes:
        analysis = self.analysis_service.generate_report(db, dataset)
        metrics = analysis["metrics"]
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "业务分析报告"
        sheet.append(["AI 智能数据分析助手 - 业务分析报告"])
        sheet.merge_cells("A1:B1")
        sheet["A1"].font = Font(bold=True, size=16, color="FFFFFF")
        sheet["A1"].fill = PatternFill("solid", fgColor="1D4ED8")
        sheet.append(["数据集", dataset.original_filename])
        sheet.append(["有效记录", metrics["total_rows"]])
        sheet.append(["销售额总计", metrics["sales_amount"]["total"]])
        sheet.append(["销售额均值", metrics["sales_amount"]["average"]])
        sheet.append(["目标完成率", metrics["completion_rate"]])
        sheet.append([])
        sheet.append(["AI 分析模式", analysis["mode"]])
        sheet.append(["数据摘要", analysis["summary"]])
        sheet.append(["异常发现", "；".join(analysis["anomalies"])])
        sheet.append(["业务问题", "；".join(analysis["business_problems"])])
        sheet.append(["优化建议", "；".join(analysis["recommendations"])])
        top_regions = metrics.get("top_regions", [])
        if top_regions:
            sheet["D1"] = "区域"
            sheet["E1"] = "销售额"
            for row, region in enumerate(top_regions, start=2):
                sheet.cell(row=row, column=4, value=region["name"])
                sheet.cell(row=row, column=5, value=region["value"])
            chart = BarChart()
            chart.title = "区域销售额 TOP"
            chart.y_axis.title = "销售额"
            chart.x_axis.title = "区域"
            chart.add_data(Reference(sheet, min_col=5, min_row=1, max_row=len(top_regions) + 1), titles_from_data=True)
            chart.set_categories(Reference(sheet, min_col=4, min_row=2, max_row=len(top_regions) + 1))
            chart.height = 8
            chart.width = 15
            sheet.add_chart(chart, "D4")
        sheet.column_dimensions["A"].width = 18
        sheet.column_dimensions["B"].width = 90
        for cell in sheet["A"]:
            cell.font = Font(bold=True)
        output = BytesIO()
        workbook.save(output)
        return output.getvalue()

    def _analysis(self, db, dataset: Dataset) -> dict:
        return self.analysis_service.generate_report(db, dataset)

    @staticmethod
    def _build_region_chart(metrics: dict) -> BytesIO | None:
        regions = metrics.get("top_regions", [])
        if not regions:
            return None

        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt

        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        chart, axis = plt.subplots(figsize=(8, 3.8))
        axis.bar([item["name"] for item in regions], [item["value"] for item in regions], color="#2563EB")
        axis.set_title("Top 区域销售额")
        axis.set_ylabel("销售额")
        axis.tick_params(axis="x", rotation=25)
        chart.tight_layout()
        output = BytesIO()
        chart.savefig(output, format="png", dpi=160)
        plt.close(chart)
        output.seek(0)
        return output

    def build_word(self, db, dataset: Dataset) -> bytes:
        from docx import Document
        from docx.shared import Pt
        analysis = self._analysis(db, dataset)
        doc = Document()
        doc.add_heading("AI 智能数据分析助手 - 业务分析报告", 0)
        doc.add_paragraph(f"数据集：{dataset.original_filename}")
        doc.add_heading("数据概览", 1)
        for label, value in [("有效记录", analysis["metrics"]["total_rows"]), ("销售额总计", analysis["metrics"]["sales_amount"]["total"]), ("目标完成率", analysis["metrics"]["completion_rate"])]:
            doc.add_paragraph(f"{label}：{value}")
        chart = self._build_region_chart(analysis["metrics"])
        if chart is not None:
            doc.add_heading("区域销售额图表", 1)
            doc.add_picture(chart)
        for title, content in [("数据摘要", analysis["summary"]), ("异常发现", "；".join(analysis["anomalies"])), ("业务问题", "；".join(analysis["business_problems"])), ("优化建议", "；".join(analysis["recommendations"]))]:
            doc.add_heading(title, 1); doc.add_paragraph(content)
        for style in doc.styles:
            if hasattr(style, "font"):
                style.font.name = "Microsoft YaHei"
                style.font.size = Pt(10)
        output = BytesIO(); doc.save(output); return output.getvalue()

    def build_pdf(self, db, dataset: Dataset) -> bytes:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfgen.canvas import Canvas
        analysis = self._analysis(db, dataset)
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        output = BytesIO(); canvas = Canvas(output, pagesize=A4); canvas.setFont("STSong-Light", 16)
        canvas.drawString(50, 800, "AI 智能数据分析助手 - 业务分析报告")
        canvas.setFont("STSong-Light", 10); y = 770
        lines = [f"数据集：{dataset.original_filename}", f"有效记录：{analysis['metrics']['total_rows']}", f"销售额总计：{analysis['metrics']['sales_amount']['total']}", f"数据摘要：{analysis['summary']}", f"异常发现：{'；'.join(analysis['anomalies'])}", f"优化建议：{'；'.join(analysis['recommendations'])}"]
        for line in lines:
            canvas.drawString(50, y, line[:70]); y -= 28
        chart = self._build_region_chart(analysis["metrics"])
        if chart is not None:
            canvas.drawImage(ImageReader(chart), 50, 390, width=490, height=232, preserveAspectRatio=True, mask="auto")
        canvas.save(); return output.getvalue()
