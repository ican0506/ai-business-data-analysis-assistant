from io import BytesIO
from pathlib import Path

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
        overview_rows = self._overview_rows(metrics)
        for label, value in (overview_rows[2], overview_rows[3], overview_rows[5]):
            sheet.append([label, value])
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
    def _overview_rows(metrics: dict) -> list[tuple[str, str | float | int | None]]:
        """Build a shared business overview for Excel, Word, and PDF reports."""
        sales = metrics["sales_amount"]
        highest = metrics.get("highest_sales_region")
        lowest = metrics.get("lowest_sales_region")
        ranking = metrics.get("region_ranking", [])[:5]

        def format_region(region: dict | None) -> str:
            if not region:
                return "-"
            return f"{region['name']}\uff08{region['value']:g}\uff09"

        ranking_text = "\uff1b".join(
            f"{index}. {region['name']}\uff1a{region['value']:g}"
            for index, region in enumerate(ranking, start=1)
        ) or "-"
        completion_rate = metrics.get("completion_rate")
        return [
            ("\u9500\u552e\u989d\u603b\u8ba1", sales["total"]),
            ("\u5e73\u5747\u9500\u552e\u989d", sales.get("average")),
            ("\u6700\u5927\u9500\u552e\u533a\u57df", format_region(highest)),
            ("\u6700\u4f4e\u9500\u552e\u533a\u57df", format_region(lowest)),
            ("\u5b8c\u6210\u7387", f"{completion_rate}%" if completion_rate is not None else "-"),
            ("\u533a\u57df TOP \u6392\u540d", ranking_text),
        ]

    @staticmethod
    def _resolve_chart_font_path() -> Path:
        """返回当前运行环境中可供 Matplotlib 使用的中文字体文件。"""
        candidates = (
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"),
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\simhei.ttf"),
        )
        for font_path in candidates:
            if font_path.is_file():
                return font_path
        raise RuntimeError("未找到可用中文字体，请安装 Noto CJK 或配置运行环境字体")

    @staticmethod
    def _build_region_chart(metrics: dict) -> BytesIO | None:
        regions = metrics.get("top_regions", [])
        if not regions:
            return None

        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        from matplotlib.font_manager import FontProperties

        plt.rcParams["axes.unicode_minus"] = False
        chinese_font = FontProperties(fname=str(ReportService._resolve_chart_font_path()))
        chart, axis = plt.subplots(figsize=(8, 3.8))
        axis.bar(
            [item["name"] for item in regions],
            [item["value"] for item in regions],
            color="#2563EB",
            label="区域销售额",
        )
        axis.set_title("区域销售额 TOP", fontproperties=chinese_font)
        axis.set_xlabel("区域", fontproperties=chinese_font)
        axis.set_ylabel("销售额", fontproperties=chinese_font)
        axis.legend(prop=chinese_font)
        for label in axis.get_xticklabels():
            label.set_fontproperties(chinese_font)
        axis.tick_params(axis="x", rotation=25)
        chart.tight_layout()
        output = BytesIO()
        chart.savefig(output, format="png", dpi=160)
        plt.close(chart)
        output.seek(0)
        return output

    @staticmethod
    def _build_pdf_summary_image(dataset: Dataset, analysis: dict) -> BytesIO:
        """Render PDF text as a CJK-capable image for consistent PDF viewing."""
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        from matplotlib.font_manager import FontProperties

        chinese_font = FontProperties(fname=str(ReportService._resolve_chart_font_path()))
        from textwrap import wrap

        metrics = analysis["metrics"]
        overview_rows = ReportService._overview_rows(metrics)
        sections = [
            ("AI \u667a\u80fd\u6570\u636e\u5206\u6790\u52a9\u624b - \u4e1a\u52a1\u5206\u6790\u62a5\u544a", 16),
            (f"\u6570\u636e\u96c6\uff1a{dataset.original_filename}    \u6709\u6548\u8bb0\u5f55\uff1a{metrics['total_rows']}", 9),
            *[(f"{label}\uff1a{value}", 8.5) for label, value in overview_rows],
            (f"\u6570\u636e\u6458\u8981\uff1a{analysis['summary']}", 8.5),
            (f"\u5f02\u5e38\u5206\u6790\uff1a{'\uff1b'.join(analysis['anomalies'])}", 8.5),
            (f"\u4e1a\u52a1\u5efa\u8bae\uff1a{'\uff1b'.join(analysis['recommendations'])}", 8.5),
        ]
        figure, axis = plt.subplots(figsize=(8.2, 5.5))
        axis.axis("off")
        y_position = 0.96
        for content, font_size in sections:
            wrapped_content = "\n".join(wrap(content, width=56))
            axis.text(
                0.02,
                y_position,
                wrapped_content,
                fontproperties=chinese_font,
                fontsize=font_size,
                fontweight="bold" if font_size >= 16 else "normal",
                va="top",
            )
            line_height = 0.065 if font_size >= 16 else 0.042
            y_position -= line_height * (wrapped_content.count("\n") + 1) + 0.012
        figure.tight_layout(pad=0.3)
        output = BytesIO()
        figure.savefig(output, format="png", dpi=160, bbox_inches="tight")
        plt.close(figure)
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
        doc.add_heading("\u9500\u552e\u6982\u89c8\u4e0e\u533a\u57df\u6392\u540d", 1)
        for label, value in (
            self._overview_rows(analysis["metrics"])[1],
            self._overview_rows(analysis["metrics"])[2],
            self._overview_rows(analysis["metrics"])[3],
            self._overview_rows(analysis["metrics"])[5],
        ):
            doc.add_paragraph(f"{label}\uff1a{value}")
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
        output = BytesIO()
        canvas = Canvas(output, pagesize=A4)
        canvas.setTitle("AI Business Analysis Report")
        summary_image = self._build_pdf_summary_image(dataset, analysis)
        canvas.drawImage(
            ImageReader(summary_image),
            50,
            80,
            width=490,
            height=680,
            preserveAspectRatio=True,
            mask="auto",
        )
        canvas.showPage()
        chart = self._build_region_chart(analysis["metrics"])
        if chart is not None:
            canvas.drawImage(
                ImageReader(chart),
                50,
                260,
                width=490,
                height=300,
                preserveAspectRatio=True,
                mask="auto",
            )
        canvas.save()
        return output.getvalue()

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
