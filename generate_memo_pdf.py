"""
Generates executive-grade BUSINESS_MEMO.pdf using ReportLab.
Run: python generate_memo_pdf.py
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

def build_pdf(filename="BUSINESS_MEMO.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#065f46')
    )

    story = []

    # Title & Memo Header
    story.append(Paragraph("EXECUTIVE MEMORANDUM", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284c7'), spaceAfter=8))
    
    meta_text = """
    <b>TO:</b> Founder & CEO &nbsp;&nbsp;|&nbsp;&nbsp; <b>FROM:</b> Associate Software Engineer (AI & Automation)<br/>
    <b>DATE:</b> November 2, 2026 &nbsp;&nbsp;|&nbsp;&nbsp; <b>SUBJECT:</b> COD Decision Engine & Financial Optimization
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=10))

    # Executive Summary Callout Box
    summary_html = """
    <b>EXECUTIVE SUMMARY:</b><br/>
    Across last month's 2,018 COD orders, our automated 4-tier decision engine achieved:
    <b>+Rs 65,089 saved</b> from avoided returns and damaged inventory, constrained false cancellations to just <b>3.5%</b> of volume, and produced <b>+Rs 28,422 in net profit expansion</b> (+Rs 14.08 per order). Scaled to 3,000 monthly orders, this delivers <b>~Rs 42,000+ monthly net profit expansion</b> (~Rs 5 Lakhs annually) while protecting customer acquisition ROI.
    """
    summary_table = Table([[Paragraph(summary_html, callout_style)]], colWidths=[520])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ecfdf5')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#059669')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # Section 1
    story.append(Paragraph("1. Surprising Data Findings (With Numbers)", h2_style))
    story.append(Paragraph(
        "<b>1. The Pincode Fallacy (1,066 unique pincodes across 2,018 orders):</b> "
        "Over 96.6% of pincodes had fewer than 5 orders (840 had exactly 1). Banning pincodes based on historical returns creates an illusory 100% RTO penalty on sample sizes of n=1, destroying genuine growth. Risk is driven by macro-geography (Bihar at 53.4% RTO, UP at 44.7% vs. Maharashtra at 17.9%), not local pincodes.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>2. The 'Hinglish Address' Delivery Paradox:</b> "
        "388 orders (19.2% of total) contained colloquial Hinglish directions ('ph krke aana', 'Mandir ke paas', 'gali no 22 ke andar'). While rigid regex checks reject these, empirical data proves they delivered 68.0% of the time, contributing Rs 1.5 Lakhs in margin. In contrast, dummy entries ('.', 'xyz') failed 62% to 73% of the time. An LLM is required to distinguish local context from actual gibberish.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>3. The High-Value COD Paradox:</b> "
        "Orders over Rs 2,000 had an RTO rate of 40.4% (and Rs 1,500-Rs 2,000 had 37.9% RTO), compared to the Rs 1,000-Rs 1,500 bracket which had the lowest RTO at 20.2%. High COD ticket sizes trigger doorstep buyer remorse when handing over cash to couriers.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>4. The Prior RTO Cliff:</b> "
        "Repeat customers with 0 returns deliver 86.2% of the time (13.8% RTO). But customers with >= 2 prior returns suffered a 76.5% RTO rate. Serial returners exist, and stopping COD for repeat returners is our highest-conviction cancellation rule.",
        bullet_style
    ))
    story.append(Spacer(1, 8))

    # Section 2
    story.append(Paragraph("2. Recommended Strategy & Simulation on Last Month's Orders", h2_style))
    story.append(Paragraph("Simulation of our 4-tier decision engine on all 2,018 historical COD records:", body_style))

    # Table of 4 Buckets
    t_data = [
        ["Action Bucket", "Orders", "% Total", "Hist RTO %", "Avg Val", "Operational Logic", "Net Rs Impact"],
        ["1. Ship as-is", "654", "32.4%", "15.7%", "Rs 738", "Immediate dispatch; verified & repeat buyers", "Rs 0 (base)"],
        ["2. Ship after confirm", "872", "43.2%", "29.7%", "Rs 675", "WhatsApp interactive verification check", "+Rs 28,518"],
        ["3. Nudge to prepaid", "422", "20.9%", "37.2%", "Rs 1,704", "Rs 50 discount offered to secure payment", "+Rs 6,322"],
        ["4. Hold / cancel", "70", "3.5%", "77.1%", "Rs 912", "Repeat abusers (>=2 RTO) & bot dummy accounts", "-Rs 6,419"],
        ["TOTALS", "2,018", "100.0%", "28.4%", "Rs 897", "Avoided RTO: Rs 65,089 | Net Profit:", "+Rs 28,422"]
    ]
    t = Table(t_data, colWidths=[100, 42, 45, 52, 48, 160, 73])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ALIGN', (1,0), (4,-1), 'CENTER'),
        ('ALIGN', (6,0), (6,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f8fafc')]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Mathematical Justification for the Rs 50 Prepaid Discount:</b> "
        "Delivered gross profit is Rs 402.38 (62% on Rs 649 AOV). Each RTO costs Rs 169.40 (Rs 65 fwd + Rs 65 rtrn + Rs 25 pack + Rs 14.40 damage). "
        "Expected RTO cost on risky COD (35% RTO) is Rs 59.29; on Prepaid (4% RTO) it drops to Rs 6.78. "
        "The direct shipping savings delta is Rs 52.51, which completely funds the Rs 50 discount! "
        "Expected net profit on prepaid with discount is Rs 331.50 vs Rs 202.26 on risky COD, generating <b>+Rs 129.24 net margin expansion per conversion</b>.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 3
    story.append(Paragraph("3. Balancing Operations vs. Marketing with Rs Trade-off", h2_style))
    story.append(Paragraph(
        "Delivering an order generates <b>+Rs 402.38 profit</b>. An RTO costs <b>-Rs 169.40</b>. "
        "However, cancelling a genuine customer loses the Rs 402.38 margin PLUS the Rs 300 Meta CAC = <b>-Rs 702.38 total destruction</b>. "
        "Therefore, <b>cancelling a genuine order is 4.1 times more expensive than suffering an RTO</b>. "
        "Mathematically, outright cancellation is only viable when RTO risk exceeds <b>70.4%</b>. "
        "Ops' aggressive cancellation destroys value by false-cancelling customers. Marketing's zero-cancellation burns Rs 97,000 on returns. "
        "Our engine balances both: Ops saves Rs 65k in returns while Marketing keeps 96.5% of order acquisition.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 4
    story.append(Paragraph("4. What Could Go Wrong & How We'd Notice", h2_style))
    story.append(Paragraph(
        "<b>- WhatsApp Message Delivery Drops:</b> Monitored via real-time delivery rate. If delivery falls below 90%, fallback to automated SMS with 1-click token link.<br/>"
        "<b>- False Cancellation Drift:</b> Monitored via daily 'Hold/Cancel' share. If it exceeds 5.0% of volume, automated circuit-breaker holds orders for review.<br/>"
        "<b>- Courier Doorstep Fraud:</b> Couriers reporting fake 'Customer Refused'. Monitored by tracking discrepancy between WhatsApp-confirmed orders and courier RTO logs.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 5
    story.append(Paragraph("5. What We Would Build in the Next Two Weeks", h2_style))
    story.append(Paragraph(
        "<b>1. Automated Courier NDR Re-engagement:</b> Real-time WhatsApp webhook triggered when courier flags failed delivery, allowing customers to share live pin location.<br/>"
        "<b>2. Native 1-Click WhatsApp UPI:</b> Cashfree/Razorpay WhatsApp UPI intent for instant in-chat payment.<br/>"
        "<b>3. Dynamic COD Checkout Surcharge:</b> Pushing engine scores back to Shopify Functions to charge a nominal Rs 39 COD fee to high-risk profiles at checkout.<br/>"
        "<b>4. Pincode-Courier Dynamic Allocation:</b> Routing couriers by regional delivery rate (e.g. Delhivery in West India, avoiding Shadowfax in Bihar).",
        body_style
    ))

    doc.build(story)
    print(f"✅ Generated executive PDF: {filename}")

if __name__ == "__main__":
    build_pdf()
