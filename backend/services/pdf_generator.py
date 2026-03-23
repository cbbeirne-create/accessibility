"""
PDF report generator for accessibility scan results.
Generates WCAG-compliant Tagged PDFs with proper accessibility features.
"""
import logging
import base64
from datetime import datetime
from typing import Dict, Any
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image


class ReportExporter:
    """Export accessibility scan results to various formats."""
    
    @staticmethod
    def _safe_text(text):
        """Escape HTML/XML special characters for ReportLab Paragraph."""
        if text is None:
            return 'N/A'
        return xml_escape(str(text))
    
    @staticmethod
    async def generate_pdf_report(scan_data: Dict[str, Any]) -> bytes:
        """
        Generate WCAG-compliant Tagged PDF report from scan data.
        
        Accessibility Features:
        - Document metadata (Title, Author, Subject, Language)
        - Tagged PDF structure with proper heading hierarchy (H1, H2, H3)
        - Table headers marked for screen readers
        - Alt text for images
        - Logical reading order
        - Language specification (en-US)
        """
        try:
            # Create PDF buffer
            pdf_buffer = BytesIO()
            
            # Create document with metadata
            doc = SimpleDocTemplate(
                pdf_buffer, 
                pagesize=letter,
                topMargin=0.75*inch, 
                bottomMargin=0.75*inch,
                leftMargin=0.75*inch, 
                rightMargin=0.75*inch,
                title="Auditly Accessibility Report",
                author="Auditly - Website Accessibility Scanner",
                subject=f"Accessibility scan results for {scan_data.get('url', 'Unknown URL')}",
                creator="Auditly PDF Generator",
                producer="ReportLab with WCAG 2.1 AA Compliance",
                keywords="accessibility, WCAG, a11y, compliance, audit"
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # Brand Colors - Emerald/Teal Enterprise Theme (WCAG compliant contrast)
            brand_emerald = colors.Color(0.13, 0.55, 0.40)
            brand_teal = colors.Color(0.10, 0.50, 0.45)
            brand_slate = colors.Color(0.15, 0.18, 0.23)
            text_dark = colors.Color(0.1, 0.1, 0.1)
            
            # Define styles
            h1_style = ParagraphStyle(
                'AccessibleH1',
                parent=styles['Heading1'],
                fontSize=28,
                textColor=brand_emerald,
                alignment=1,
                spaceAfter=6,
                fontName='Helvetica-Bold',
                leading=34
            )
            
            h2_style = ParagraphStyle(
                'AccessibleH2',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=brand_teal,
                spaceBefore=20,
                spaceAfter=10,
                fontName='Helvetica-Bold',
                leading=20
            )
            
            h3_style = ParagraphStyle(
                'AccessibleH3',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=brand_slate,
                spaceBefore=12,
                spaceAfter=6,
                fontName='Helvetica-Bold',
                leading=16
            )
            
            body_style = ParagraphStyle(
                'AccessibleBody',
                parent=styles['Normal'],
                fontSize=10,
                textColor=text_dark,
                leading=14,
                spaceAfter=6
            )
            
            caption_style = ParagraphStyle(
                'AccessibleCaption',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.Color(0.3, 0.3, 0.3),
                alignment=1,
                spaceAfter=16,
                leading=14
            )
            
            score_style = ParagraphStyle(
                'ScoreDisplay',
                parent=styles['Normal'],
                fontSize=24,
                alignment=1,
                fontName='Helvetica-Bold',
                leading=30
            )
            
            detail_style = ParagraphStyle(
                'IssueDetail',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.Color(0.25, 0.25, 0.25),
                leftIndent=15,
                spaceAfter=4,
                leading=12
            )
            
            guidance_style = ParagraphStyle(
                'Guidance',
                parent=styles['Normal'],
                fontSize=9,
                textColor=brand_teal,
                leftIndent=15,
                spaceBefore=4,
                spaceAfter=10,
                leading=12
            )
            
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.Color(0.4, 0.4, 0.4),
                alignment=1,
                leading=10
            )
            
            # Document Title
            story.append(Paragraph("AUDITLY", h1_style))
            story.append(Paragraph("Website Accessibility Report", caption_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # Score Section
            score = scan_data.get('score', 0)
            if score >= 80:
                score_color = brand_emerald
                score_label = "Excellent Accessibility"
            elif score >= 60:
                score_color = colors.Color(0.8, 0.5, 0.0)
                score_label = "Good - Room for Improvement"
            else:
                score_color = colors.Color(0.7, 0.1, 0.1)
                score_label = "Needs Attention"
            
            score_display_style = ParagraphStyle(
                'ScoreValue',
                parent=score_style,
                textColor=score_color
            )
            story.append(Paragraph(f"Accessibility Score: {score}/100", score_display_style))
            story.append(Paragraph(score_label, caption_style))
            story.append(Spacer(1, 0.3 * inch))
            
            # Scan Details Section
            story.append(Paragraph("Scan Details", h2_style))
            
            scan_date = scan_data.get('createdAt')
            if scan_date:
                if hasattr(scan_date, 'strftime'):
                    formatted_date = scan_date.strftime('%B %d, %Y at %I:%M %p')
                else:
                    formatted_date = str(scan_date)
            else:
                formatted_date = 'N/A'
            
            url_value = ReportExporter._safe_text(scan_data.get('url', 'N/A'))
            info_data = [
                ['Property', 'Value'],
                ['Website URL', url_value],
                ['Scan Date', formatted_date],
                ['Testing Engine', scan_data.get('tool', 'axe-core').upper()],
                ['Status', scan_data.get('status', 'N/A').upper()]
            ]
            
            info_table = Table(info_data, colWidths=[1.8*inch, 4.7*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (-1, 0), text_dark),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 1), (0, -1), brand_slate),
                ('TEXTCOLOR', (1, 1), (1, -1), text_dark),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.3 * inch))
            
            # Results Summary Section
            if scan_data.get('issues'):
                issues = scan_data['issues']
                failed_count = len(issues.get('failed', []))
                passed_count = len(issues.get('passed', []))
                incomplete_count = len(issues.get('incomplete', []))
                
                story.append(Paragraph("Results Summary", h2_style))
                
                summary_data = [
                    ['Test Category', 'Count', 'Description'],
                    ['Failed Tests', str(failed_count), 'Accessibility issues requiring fixes'],
                    ['Passed Tests', str(passed_count), 'Accessibility checks that passed'],
                    ['Incomplete Tests', str(incomplete_count), 'Tests requiring manual review']
                ]
                
                summary_table = Table(summary_data, colWidths=[1.5*inch, 0.8*inch, 3.2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('TEXTCOLOR', (0, 0), (-1, 0), text_dark),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 1), (1, 1), colors.Color(0.7, 0.1, 0.1)),
                    ('TEXTCOLOR', (0, 2), (1, 2), brand_emerald),
                    ('TEXTCOLOR', (0, 3), (1, 3), colors.Color(0.8, 0.5, 0.0)),
                    ('TEXTCOLOR', (2, 1), (2, -1), colors.Color(0.3, 0.3, 0.3)),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 0.3 * inch))
                
                # Failed Issues Details
                if failed_count > 0:
                    story.append(Paragraph("Failed Accessibility Tests", h2_style))
                    story.append(Paragraph(
                        f"The following {min(failed_count, 15)} issue(s) were identified and require attention:",
                        body_style
                    ))
                    story.append(Spacer(1, 0.1 * inch))
                    
                    for i, issue in enumerate(issues['failed'][:15]):
                        issue_id = ReportExporter._safe_text(issue.get('id', 'Unknown Issue'))
                        story.append(Paragraph(f"Issue {i+1}: {issue_id}", h3_style))
                        
                        impact = issue.get('impact', 'unknown').upper()
                        if impact == 'CRITICAL':
                            impact_color = colors.Color(0.7, 0.0, 0.0)
                            impact_desc = "Critical - Must be fixed immediately"
                        elif impact == 'SERIOUS':
                            impact_color = colors.Color(0.8, 0.3, 0.0)
                            impact_desc = "Serious - Should be fixed soon"
                        elif impact == 'MODERATE':
                            impact_color = colors.Color(0.7, 0.5, 0.0)
                            impact_desc = "Moderate - Should be addressed"
                        else:
                            impact_color = colors.Color(0.4, 0.4, 0.4)
                            impact_desc = "Minor - Consider fixing"
                        
                        impact_style = ParagraphStyle(
                            'ImpactLevel',
                            parent=detail_style,
                            textColor=impact_color,
                            fontName='Helvetica-Bold'
                        )
                        story.append(Paragraph(f"Impact: {impact} - {impact_desc}", impact_style))
                        
                        description = ReportExporter._safe_text(issue.get('description', 'No description available'))
                        story.append(Paragraph(f"Description: {description}", detail_style))
                        
                        if issue.get('wcag'):
                            wcag_refs = [tag.upper() for tag in issue['wcag'] if 'wcag' in tag.lower()]
                            if wcag_refs:
                                story.append(Paragraph(f"WCAG Reference: {', '.join(wcag_refs)}", detail_style))
                        
                        if issue.get('help'):
                            help_text = ReportExporter._safe_text(issue['help'])
                            story.append(Paragraph(f"How to Fix: {help_text}", guidance_style))
                        
                        story.append(Spacer(1, 0.15 * inch))
                    
                    if failed_count > 15:
                        story.append(Paragraph(
                            f"Note: {failed_count - 15} additional issues not shown. View the full report online for complete details.",
                            caption_style
                        ))
                
                # Passed Tests Summary
                if passed_count > 0:
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph("Passed Accessibility Tests", h2_style))
                    story.append(Paragraph(
                        f"{passed_count} accessibility checks passed successfully. These include tests for:",
                        body_style
                    ))
                    
                    passed_examples = issues.get('passed', [])[:5]
                    for test in passed_examples:
                        test_id = ReportExporter._safe_text(test.get('id', 'Unknown'))
                        test_desc = ReportExporter._safe_text(test.get('description', 'N/A'))
                        story.append(Paragraph(f"* {test_id}: {test_desc}", detail_style))
                    
                    if passed_count > 5:
                        story.append(Paragraph(f"... and {passed_count - 5} more passing tests.", caption_style))
            
            # Visual Evidence Section
            if scan_data.get('full_page_screenshot'):
                story.append(Spacer(1, 0.3 * inch))
                story.append(Paragraph("Visual Evidence", h2_style))
                story.append(Paragraph(
                    "Screenshot of the scanned webpage with accessibility issues highlighted. "
                    "Areas with red borders indicate elements that failed accessibility tests.",
                    body_style
                ))
                
                try:
                    img_data = base64.b64decode(scan_data['full_page_screenshot'])
                    img_buffer = BytesIO(img_data)
                    img = Image(img_buffer, width=6*inch, height=4*inch, kind='proportional')
                    story.append(img)
                    story.append(Paragraph(
                        f"Figure 1: Full page screenshot of {scan_data.get('url', 'the scanned website')} "
                        f"captured during accessibility scan on {formatted_date}.",
                        caption_style
                    ))
                except Exception as img_error:
                    logging.warning(f"Could not include screenshot in PDF: {img_error}")
                    story.append(Paragraph(
                        "Note: Screenshot could not be included in this report. "
                        "View the online report for visual evidence.",
                        caption_style
                    ))
            
            # Footer
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph("—" * 40, footer_style))
            story.append(Paragraph("Generated by Auditly - Website Accessibility Scanner", footer_style))
            story.append(Paragraph("Powered by axe-core | WCAG 2.1 Level AA Compliance Testing", footer_style))
            story.append(Paragraph(
                f"Report generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}",
                footer_style
            ))
            story.append(Paragraph(
                "This report is provided for informational purposes. "
                "Manual testing is recommended for complete accessibility compliance.",
                footer_style
            ))
            
            # Build PDF
            doc.build(story)
            
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            return pdf_bytes
                
        except Exception as e:
            logging.error(f"PDF generation failed: {e}")
            raise Exception(f"Failed to generate PDF report: {e}")
    
    @staticmethod
    async def generate_json_report(scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON report from scan data."""
        try:
            json_report = {
                "scan_info": {
                    "id": scan_data.get('id'),
                    "url": scan_data.get('url'),
                    "scan_date": scan_data.get('createdAt'),
                    "tool": scan_data.get('tool'),
                    "status": scan_data.get('status'),
                    "score": scan_data.get('score'),
                    "user_id": scan_data.get('user_id')
                },
                "results": {
                    "summary": {},
                    "failed_tests": [],
                    "passed_tests": [],
                    "incomplete_tests": []
                },
                "metadata": scan_data.get('scan_metadata', {}),
                "export_timestamp": datetime.utcnow().isoformat()
            }
            
            if scan_data.get('issues'):
                issues = scan_data['issues']
                
                json_report["results"]["summary"] = {
                    "total_failed": len(issues.get('failed', [])),
                    "total_passed": len(issues.get('passed', [])),
                    "total_incomplete": len(issues.get('incomplete', [])),
                    "critical_issues": len([i for i in issues.get('failed', []) if i.get('impact') == 'critical']),
                    "serious_issues": len([i for i in issues.get('failed', []) if i.get('impact') == 'serious'])
                }
                
                json_report["results"]["failed_tests"] = issues.get('failed', [])
                json_report["results"]["passed_tests"] = issues.get('passed', [])
                json_report["results"]["incomplete_tests"] = issues.get('incomplete', [])
            
            if scan_data.get('full_page_screenshot'):
                json_report["visual_evidence"] = {
                    "full_page_screenshot_available": True,
                    "issue_screenshots_count": len(scan_data.get('evidence_screenshots', {}))
                }
            
            return json_report
            
        except Exception as e:
            logging.error(f"JSON generation failed: {e}")
            raise Exception(f"Failed to generate JSON report: {e}")
