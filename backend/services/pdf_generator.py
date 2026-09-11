"""PDF and JSON report generation for Auditly scan results.

Reports deliberately describe automated findings and the Auditly Accessibility
Health Score. They do not claim to certify WCAG conformance.
"""
import asyncio
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .storage import load_png_bytes

logger = logging.getLogger(__name__)

SCORE_NAME = 'Auditly Accessibility Health Score'
SCORE_DISCLAIMER = (
    'This automated score is an indicator derived from automated checks. '
    'It is not a WCAG compliance percentage, certification, or substitute for manual accessibility testing.'
)


class ReportExporter:
    @staticmethod
    def _safe(value: Any) -> str:
        return xml_escape('N/A' if value is None else str(value))

    @staticmethod
    def _date(value: Any) -> str:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc).strftime('%d %B %Y at %H:%M UTC')
        return ReportExporter._safe(value)

    @staticmethod
    async def generate_pdf_report(scan_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            rightMargin=0.65 * inch,
            title='Auditly Accessibility Report',
            author='Auditly',
            subject=f"Automated accessibility scan results for {scan_data.get('url', '')}",
            creator='Auditly',
            producer='ReportLab',
            keywords='accessibility, automated testing, axe-core, WCAG',
        )
        styles = getSampleStyleSheet()
        h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=24, leading=30, textColor=colors.HexColor('#047857'), spaceAfter=8)
        h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=15, leading=20, textColor=colors.HexColor('#0f766e'), spaceBefore=18, spaceAfter=8)
        h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=11, leading=15, textColor=colors.HexColor('#1e293b'), spaceBefore=12, spaceAfter=5)
        body = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=9.5, leading=14, textColor=colors.HexColor('#1f2937'))
        small = ParagraphStyle('Small', parent=body, fontSize=8.5, leading=12, textColor=colors.HexColor('#475569'))
        code = ParagraphStyle('Code', parent=small, fontName='Courier', fontSize=7.5, leading=10, backColor=colors.HexColor('#f8fafc'), borderPadding=6)
        warning = ParagraphStyle('Warning', parent=body, backColor=colors.HexColor('#fef3c7'), borderColor=colors.HexColor('#f59e0b'), borderWidth=0.5, borderPadding=8, spaceBefore=8, spaceAfter=12)
        story = []

        score = scan_data.get('score')
        issues = scan_data.get('issues') or {}
        failed = issues.get('failed') or []
        passed = issues.get('passed') or []
        incomplete = issues.get('incomplete') or []

        story.append(Paragraph('Auditly Accessibility Report', h1))
        story.append(Paragraph(ReportExporter._safe(scan_data.get('url')), body))
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph(f'<b>{SCORE_NAME}: {score if score is not None else "N/A"}/100</b>', body))
        story.append(Paragraph(SCORE_DISCLAIMER, warning))

        details = [
            ['Property', 'Value'],
            ['Website', ReportExporter._safe(scan_data.get('url'))],
            ['Scan date', ReportExporter._date(scan_data.get('createdAt'))],
            ['Engine', ReportExporter._safe(scan_data.get('tool', 'axe-core'))],
            ['Status', ReportExporter._safe(scan_data.get('status'))],
        ]
        table = Table(details, colWidths=[1.35 * inch, 5.35 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(table)

        story.append(Paragraph('Results summary', h2))
        summary = Table([
            ['Category', 'Rules'],
            ['Failed', str(len(failed))],
            ['Passed', str(len(passed))],
            ['Needs manual review', str(len(incomplete))],
        ], colWidths=[3.2 * inch, 1.1 * inch])
        summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(summary)

        if failed:
            story.append(Paragraph('Failed automated checks', h2))
            for index, issue in enumerate(failed[:25], start=1):
                title = issue.get('help') or issue.get('id') or f'Issue {index}'
                story.append(Paragraph(f'{index}. {ReportExporter._safe(title)}', h3))
                metadata = []
                if issue.get('impact'):
                    metadata.append(f"Impact: {ReportExporter._safe(issue.get('impact')).upper()}")
                if issue.get('count') is not None:
                    metadata.append(f"Affected elements: {issue.get('count')}")
                wcag = [str(tag).upper() for tag in issue.get('wcag', []) if str(tag).lower().startswith('wcag')]
                if wcag:
                    metadata.append('Tags: ' + ', '.join(wcag))
                if metadata:
                    story.append(Paragraph(' | '.join(metadata), small))
                if issue.get('description'):
                    story.append(Paragraph(ReportExporter._safe(issue.get('description')), body))
                for element in (issue.get('elements') or [])[:3]:
                    if element.get('target'):
                        story.append(Paragraph('<b>Selector:</b> ' + ReportExporter._safe(' → '.join(element.get('target') or [])), small))
                    if element.get('html'):
                        story.append(Paragraph(ReportExporter._safe(element.get('html')), code))
                    if element.get('failureSummary'):
                        story.append(Paragraph(ReportExporter._safe(element.get('failureSummary')), small))
                if issue.get('helpUrl'):
                    story.append(Paragraph('Technical documentation: ' + ReportExporter._safe(issue.get('helpUrl')), small))

        if incomplete:
            story.append(Paragraph('Checks requiring manual review', h2))
            story.append(Paragraph('Automated testing cannot determine conformance for these checks. They require human assessment.', body))
            for issue in incomplete[:20]:
                story.append(Paragraph(ReportExporter._safe(issue.get('help') or issue.get('id')), h3))
                if issue.get('description'):
                    story.append(Paragraph(ReportExporter._safe(issue.get('description')), body))

        screenshot_bytes = await asyncio.to_thread(
            load_png_bytes,
            base64_data=scan_data.get('full_page_screenshot'),
            key=scan_data.get('full_page_screenshot_key'),
        )
        if screenshot_bytes:
            try:
                story.append(Paragraph('Visual evidence', h2))
                story.append(Paragraph('Screenshot captured during the automated scan. Highlighted elements indicate locations the scanner could associate with automated failures.', body))
                image = Image(BytesIO(screenshot_bytes), width=6.4 * inch, height=4.3 * inch, kind='proportional')
                story.append(Spacer(1, 0.08 * inch))
                story.append(image)
            except Exception as exc:
                logger.warning('Could not add screenshot to PDF: %s', exc)

        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph('Testing limitations', h2))
        story.append(Paragraph(
            'Automated scanners identify only a subset of accessibility barriers. Keyboard operation, focus management, meaningful reading order, alternative text quality, captions, cognitive usability, assistive-technology behaviour and other requirements may need manual testing by qualified reviewers and disabled users.',
            body,
        ))
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(f"Generated by Auditly on {datetime.now(timezone.utc).strftime('%d %B %Y at %H:%M UTC')}", small))

        document.build(story)
        value = buffer.getvalue()
        buffer.close()
        return value

    @staticmethod
    async def generate_json_report(scan_data: Dict[str, Any]) -> Dict[str, Any]:
        issues = scan_data.get('issues') or {}
        failed = issues.get('failed') or []
        passed = issues.get('passed') or []
        incomplete = issues.get('incomplete') or []
        evidence_count = max(
            len(scan_data.get('evidence_screenshots') or {}),
            len(scan_data.get('evidence_screenshot_keys') or {}),
            len(scan_data.get('evidence_screenshot_urls') or {}),
        )
        return {
            'scan_info': {
                'id': scan_data.get('id'),
                'url': scan_data.get('url'),
                'scan_date': scan_data.get('createdAt'),
                'tool': scan_data.get('tool'),
                'status': scan_data.get('status'),
                'score': scan_data.get('score'),
                'score_name': SCORE_NAME,
                'score_disclaimer': SCORE_DISCLAIMER,
            },
            'results': {
                'summary': {
                    'total_failed': len(failed),
                    'total_passed': len(passed),
                    'total_incomplete': len(incomplete),
                    'critical_issues': sum(1 for issue in failed if issue.get('impact') == 'critical'),
                    'serious_issues': sum(1 for issue in failed if issue.get('impact') == 'serious'),
                },
                'failed_tests': failed,
                'passed_tests': passed,
                'incomplete_tests': incomplete,
            },
            'visual_evidence': {
                'full_page_screenshot_available': bool(
                    scan_data.get('full_page_screenshot') or scan_data.get('full_page_screenshot_key') or scan_data.get('full_page_screenshot_url')
                ),
                'issue_screenshots_count': evidence_count,
            },
            'metadata': scan_data.get('scan_metadata', {}),
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
        }
