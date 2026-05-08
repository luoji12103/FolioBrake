# pyright: reportOptionalCall=false, reportOperatorIssue=false, reportOptionalMemberAccess=false
"""PDF report generation.

Dependencies (optional):
    pip install reportlab

If reportlab is not installed, falls back to plain-text generation.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore[import-untyped]
    from reportlab.lib.units import inch  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )

    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    colors = None  # type: ignore[misc,assignment]
    A4 = None  # type: ignore[misc,assignment]
    getSampleStyleSheet = None  # type: ignore[misc,assignment]
    ParagraphStyle = None  # type: ignore[misc,assignment]
    inch = None  # type: ignore[misc,assignment]
    SimpleDocTemplate = None  # type: ignore[misc,assignment]
    Paragraph = None  # type: ignore[misc,assignment]
    Spacer = None  # type: ignore[misc,assignment]
    Table = None  # type: ignore[misc,assignment]
    TableStyle = None  # type: ignore[misc,assignment]
    HRFlowable = None  # type: ignore[misc,assignment]


class ReportGenerator:

    @staticmethod
    def _assert_reportlab():
        assert SimpleDocTemplate is not None
        assert A4 is not None
        assert getSampleStyleSheet is not None
        assert ParagraphStyle is not None
        assert Paragraph is not None
        assert Spacer is not None
        assert HRFlowable is not None
        assert Table is not None
        assert TableStyle is not None
        assert colors is not None
        assert inch is not None

    def generate_backtest_report(self, data: dict[str, Any]) -> bytes:
        if HAS_REPORTLAB:
            return self._generate_pdf_backtest(data)
        return self._generate_text_backtest(data).encode("utf-8")

    def generate_portfolio_report(self, data: dict[str, Any]) -> bytes:
        if HAS_REPORTLAB:
            return self._generate_pdf_portfolio(data)
        return self._generate_text_portfolio(data).encode("utf-8")

    def generate_risk_report(self, data: dict[str, Any]) -> bytes:
        if HAS_REPORTLAB:
            return self._generate_pdf_risk(data)
        return self._generate_text_risk(data).encode("utf-8")

    def _generate_pdf_backtest(self, data: dict[str, Any]) -> bytes:
        self._assert_reportlab()
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            "ReportTitle", parent=styles["Title"], fontSize=18, spaceAfter=20,
        )
        elements.append(Paragraph("Backtest Report", title_style))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(HRFlowable(width="100%", thickness=1))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph("Configuration", styles["Heading2"]))
        config = data.get("config", {})
        config_data = [["Parameter", "Value"]]
        for k, v in config.items():
            config_data.append([str(k), str(v)])
        elements.append(self._make_table(config_data))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("Performance Metrics", styles["Heading2"]))
        metrics = data.get("metrics", {})
        metrics_data = [["Metric", "Value"]]
        for k, v in metrics.items():
            if isinstance(v, float):
                metrics_data.append([k, f"{v:.4f}"])
            else:
                metrics_data.append([k, str(v)])
        elements.append(self._make_table(metrics_data))
        elements.append(Spacer(1, 0.3 * inch))

        trades = data.get("trades", [])
        if trades:
            elements.append(Paragraph("Trade Summary", styles["Heading2"]))
            elements.append(Paragraph(f"Total trades: {len(trades)}", styles["Normal"]))

        doc.build(elements)
        return buf.getvalue()

    def _generate_pdf_portfolio(self, data: dict[str, Any]) -> bytes:
        self._assert_reportlab()
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Portfolio Report", styles["Title"]))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("Portfolio Overview", styles["Heading2"]))
        overview_data = [["Property", "Value"]]
        for k, v in data.get("overview", {}).items():
            overview_data.append([str(k), str(v)])
        elements.append(self._make_table(overview_data))
        elements.append(Spacer(1, 0.3 * inch))

        positions = data.get("positions", [])
        if positions:
            elements.append(Paragraph("Positions", styles["Heading2"]))
            pos_data = [["Instrument", "Quantity", "Avg Cost", "Current Price", "P&L"]]
            for p in positions:
                pos_data.append([
                    str(p.get("symbol", "")),
                    str(p.get("quantity", "")),
                    f"{p.get('avg_cost', 0):.2f}",
                    f"{p.get('current_price', 0):.2f}",
                    f"{p.get('pnl', 0):.2f}",
                ])
            elements.append(self._make_table(pos_data))

        doc.build(elements)
        return buf.getvalue()

    def _generate_pdf_risk(self, data: dict[str, Any]) -> bytes:
        self._assert_reportlab()
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Risk Report", styles["Title"]))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("Risk Metrics", styles["Heading2"]))
        risk_data = [["Metric", "Value"]]
        for k, v in data.get("metrics", {}).items():
            if isinstance(v, float):
                risk_data.append([k, f"{v:.4f}"])
            else:
                risk_data.append([k, str(v)])
        elements.append(self._make_table(risk_data))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("Risk State", styles["Heading2"]))
        elements.append(Paragraph(
            f"Current state: {data.get('state', 'UNKNOWN')}",
            styles["Normal"],
        ))
        if data.get("triggered_rules"):
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Triggered Rules:", styles["Heading3"]))
            for rule in data["triggered_rules"]:
                elements.append(Paragraph(f"- {rule}", styles["Normal"]))

        doc.build(elements)
        return buf.getvalue()

    def _make_table(self, data: list[list[str]]) -> Any:
        self._assert_reportlab()
        table = Table(data, colWidths=[2.5 * inch, 3.5 * inch])  # type: ignore[operator]
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def _generate_text_backtest(self, data: dict[str, Any]) -> str:
        lines = [
            "BACKTEST REPORT",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "CONFIGURATION:",
        ]
        for k, v in data.get("config", {}).items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("PERFORMANCE METRICS:")
        for k, v in data.get("metrics", {}).items():
            if isinstance(v, float):
                lines.append(f"  {k}: {v:.4f}")
            else:
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def _generate_text_portfolio(self, data: dict[str, Any]) -> str:
        lines = [
            "PORTFOLIO REPORT",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "OVERVIEW:",
        ]
        for k, v in data.get("overview", {}).items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("POSITIONS:")
        for p in data.get("positions", []):
            lines.append(f"  {p.get('symbol', '?')}: qty={p.get('quantity', 0)} pnl={p.get('pnl', 0):.2f}")
        return "\n".join(lines)

    def _generate_text_risk(self, data: dict[str, Any]) -> str:
        lines = [
            "RISK REPORT",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"State: {data.get('state', 'UNKNOWN')}",
            "",
            "RISK METRICS:",
        ]
        for k, v in data.get("metrics", {}).items():
            if isinstance(v, float):
                lines.append(f"  {k}: {v:.4f}")
            else:
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)
