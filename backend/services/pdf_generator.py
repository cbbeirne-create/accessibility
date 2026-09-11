"""PDF and JSON report generation for Auditly scan results."""
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .evidence_storage import load_png

logger = logging.getLogger(__name__)


class ReportExporter:
    """Export automated accessibility scan results to stakeholder-friendly formats."""

    @staticmethod
    def _safe_text(value: Any) -> str:
        return xml_escape("N/A" if value is None else str(value))

    @staticmethod
    async def generate_pdf_report(scan_data: Dict[str, Any]) -> bytes:
        """Generate a readable PDF report.

        This report summarizes automated findings. It intentionally does not claim that
        the PDF itself is a formally tagged/validated accessible PDF or that the scanned
        website conforms to WCAG.
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                topMargin=0.7 * inch,
                bottomMargin=0.7 * inch,
                leftMargin=0.7 * inch,
                rightMargin=0.7 * inch,
                title="Auditly Accessibility Report",
                author="Auditly",
                subject=f"Automated accessibility findings for {scan_data.get('url', 'website')}",
                creator="Auditly",
                producer="ReportLab",
                keywords="accessibility, automated testing, WCAG, axe-core, remediation",
            )

            styles = getSampleStyleSheet()
            h1 = ParagraphStyle("AuditlyH1", parent=styles["Heading1"], fontSize=24, leading=29, textColor=colors.HexColor("#047857"), spaceAfter=10)
            h2 = ParagraphStyle("AuditlyH2", parent=styles["Heading2"], fontSize=15, leading=19, textColor=colors.HexColor("#0F766E"), spaceBefore=16, spaceAfter=8)
            h3 = ParagraphStyle("AuditlyH3", parent=styles["Heading3"], fontSize=11, leading=14, spaceBefore=10, spaceAfter=4)
            body = ParagraphStyle("AuditlyBody", parent=styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=6)
            small = ParagraphStyle("AuditlySmall", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#475569"), spaceAfter=5)
            code = ParagraphStyle("AuditlyCode", parent=styles["BodyText"], fontName="Courier", fontSize=7.5, leading=10, backColor=colors.HexColor("#F8FAFC"), borderPadding=5, spaceAfter=5)

            story = [
                Paragraph("Auditly Accessibility Report", h1),
                Paragraph(
                    "Automated findings and remediation evidence. This report is not a WCAG conformance certification; manual accessibility testing remains necessary.",
                    body,
                ),
            ]

            metadata = scan_data.get("scan_metadata") or {}
            score = scan_data.get("score")
            score_name = metadata.get("score_name", "Auditly Accessibility Health Score")
            score_disclaimer = metadata.get(
                "score_disclaimer",
                "Automated health score only; it is not a WCAG conformance percentage or certification.",
            )
            story.extend([
                Spacer(1, 0.12 * inch),
                Paragraph(f"{ReportExporter._safe_text(score_name)}: {score if score is not None else 'N/A'}/100", h2),
                Paragraph(ReportExporter._safe_text(score_disclaimer), small),
            ])

            created_at = scan_data.get("createdAt")
            if hasattr(created_at, "strftime"):
                created_text = created_at.strftime("%Y-%m-%d %H:%M UTC")
            else:
                created_text = str(created_at or "N/A")

            details = [
                ["Property", "Value"],
                ["Website", ReportExporter._safe_text(scan_data.get("url"))],
                ["Scan date", ReportExporter._safe_text(created_text)],
                ["Engine", ReportExporter._safe_text(scan_data.get("tool", "axe-core"))],
                ["Status", ReportExporter._safe_text(scan_data.get("status"))],
            ]
            table = Table(details, colWidths=[1.4 * inch, 5.0 * inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([Paragraph("Scan details", h2), table])

            issues = scan_data.get("issues") or {}
            failed = issues.get("failed", [])
            passed = issues.get("passed", [])
            incomplete = issues.get("incomplete", [])
            story.append(Paragraph("Results summary", h2))
            summary = Table(
                [
                    ["Category", "Rules"],
                    ["Failed", str(len(failed))],
                    ["Passed", str(len(passed))],
                    ["Needs manual review", str(len(incomplete))],
                ],
                colWidths=[3.4 * inch, 1.0 * inch],
            )
            summary.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(summary)

            if failed:
                story.append(Paragraph("Priority findings", h2))
                for index, issue in enumerate(failed[:20], 1):
                    title = issue.get("help") or issue.get("id") or "Accessibility issue"
                    story.append(Paragraph(f"{index}. {ReportExporter._safe_text(title)}", h3))
                    story.append(Paragraph(
                        f"Impact: {ReportExporter._safe_text(issue.get('impact', 'unknown'))} · Affected elements: {issue.get('count', 0)}",
                        small,
                    ))
                    if issue.get("description"):
                        story.append(Paragraph(ReportExporter._safe_text(issue["description"]), body))

                    wcag_tags = [str(tag).upper() for tag in issue.get("wcag", []) if str(tag).lower().startswith("wcag")]
                    if wcag_tags:
                        story.append(Paragraph(f"WCAG/axe tags: {ReportExporter._safe_text(', '.join(wcag_tags))}", small))
                    if issue.get("help"):
                        story.append(Paragraph(f"Recommended action: {ReportExporter._safe_text(issue['help'])}", body))

                    elements = issue.get("elements") or []
                    for element in elements[:3]:
                        targets = element.get("target") or []
                        if targets:
                            story.append(Paragraph(f"Selector: {ReportExporter._safe_text(' → '.join(targets))}", small))
                        if element.get("html"):
                            story.append(Paragraph(ReportExporter._safe_text(element["html"]), code))
                        if element.get("failureSummary"):
                            story.append(Paragraph(ReportExporter._safe_text(element["failureSummary"]), small))

                if len(failed) > 20:
                    story.append(Paragraph(f"{len(failed) - 20} additional failed rules are available in the JSON/online report.", small))

            screenshot_ref = scan_data.get("full_page_screenshot")
            if screenshot_ref:
                story.append(Paragraph("Visual evidence", h2))
                story.append(Paragraph(
                    "The screenshot is a visual aid showing the page state captured during automated testing; highlighted elements are a sample of detected violations.",
                    body,
                ))
                try:
                    image_bytes = await load_png(screenshot_ref)
                    image = Image(BytesIO(image_bytes), width=6.2 * inch, height=4.2 * inch, kind="proportional")
                    story.append(image)
                except Exception as exc:
                    logger.warning("Could not include screenshot in PDF: %s", exc)
                    story.append(Paragraph("Visual evidence is available in Auditly but could not be embedded in this export.", small))

            story.extend([
                Spacer(1, 0.25 * inch),
                Paragraph("Generated by Auditly using automated axe-core analysis.", small),
                Paragraph(
                    "Automated testing cannot identify every accessibility barrier. Use these findings with keyboard, screen-reader, zoom/reflow, cognitive/usability and other manual assistive-technology testing.",
                    small,
                ),
                Paragraph(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", small),
            ])

            doc.build(story)
            result = buffer.getvalue()
            buffer.close()
            return result
        except Exception as exc:
            logger.exception("PDF generation failed")
            raise RuntimeError(f"Failed to generate PDF report: {exc}") from exc

    @staticmethod
    async def generate_json_report(scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON without embedding potentially huge screenshot blobs."""
        try:
            issues = scan_data.get("issues") or {}
            metadata = dict(scan_data.get("scan_metadata") or {})
            metadata.setdefault("score_name", "Auditly Accessibility Health Score")
            metadata.setdefault(
                "score_disclaimer",
                "Automated health score only; it is not a WCAG conformance percentage or certification.",
            )
            return {
                "scan_info": {
                    "id": scan_data.get("id"),
                    "url": scan_data.get("url"),
                    "scan_date": scan_data.get("createdAt"),
                    "tool": scan_data.get("tool"),
                    "status": scan_data.get("status"),
                    "score": scan_data.get("score"),
                },
                "results": {
                    "summary": {
                        "total_failed": len(issues.get("failed", [])),
                        "total_passed": len(issues.get("passed", [])),
                        "total_incomplete": len(issues.get("incomplete", [])),
                        "critical_issues": sum(1 for issue in issues.get("failed", []) if issue.get("impact") == "critical"),
                        "serious_issues": sum(1 for issue in issues.get("failed", []) if issue.get("impact") == "serious"),
                    },
                    "failed_tests": issues.get("failed", []),
                    "passed_tests": issues.get("passed", []),
                    "incomplete_tests": issues.get("incomplete", []),
                },
                "visual_evidence": {
                    "full_page_screenshot_available": bool(scan_data.get("full_page_screenshot")),
                    "issue_screenshots_count": len(scan_data.get("evidence_screenshots") or {}),
                },
                "metadata": metadata,
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.exception("JSON generation failed")
            raise RuntimeError(f"Failed to generate JSON report: {exc}") from exc
