"""
Script to generate the redesigned, customized AWS Practicum Project Report
for SK ABDUL SANDHANI (24BCA7871).
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'))

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/><w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/><w:left w:val="none"/><w:right w:val="none"/><w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/><w:insideV w:val="none"/></w:tblBorders>')
    tblPr.append(borders)

def set_box_borders(table, border_color="2563EB", bg_color="F8FAFC"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="none"/><w:bottom w:val="none"/><w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/></w:tblBorders>')
    tblPr.append(borders)

def build_report():
    doc = docx.Document()

    # Configure Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        # Header & Footer setup
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("VIT-AP UNIVERSITY  |  SCHOOL OF COMPUTER SCIENCE & ENGINEERING")
        hrun.font.name = "Segoe UI"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(100, 116, 139)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        frun1 = fp.add_run("AWS Cloud Practicum Report  ·  Student Registration System\t\tRoll No: 24BCA7871")
        frun1.font.name = "Segoe UI"
        frun1.font.size = Pt(8.5)
        frun1.font.color.rgb = RGBColor(100, 116, 139)

    # Styles setup
    NAVY = RGBColor(15, 44, 89)      # #0F2C59
    ROYAL = RGBColor(30, 58, 138)    # #1E3A8A
    ACCENT = RGBColor(37, 99, 235)   # #2563EB
    CHARCOAL = RGBColor(30, 41, 59)  # #1E293B
    MUTED = RGBColor(100, 116, 139)  # #64748B

    # ----------------------------------------------------
    # TITLE BANNER SECTION
    # ----------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_badge = title_p.add_run("AWS CLOUD COMPUTING PRACTICUM REPORT")
    run_badge.font.name = "Segoe UI"
    run_badge.font.size = Pt(10)
    run_badge.font.bold = True
    run_badge.font.color.rgb = ACCENT

    h1_p = doc.add_paragraph()
    h1_p.paragraph_format.space_before = Pt(2)
    h1_p.paragraph_format.space_after = Pt(4)
    run_title = h1_p.add_run("Serverless & Virtual Machine Integrated Student Registration Architecture")
    run_title.font.name = "Segoe UI"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = NAVY

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(0)
    sub_p.paragraph_format.space_after = Pt(16)
    run_sub = sub_p.add_run("Multi-Tier Deployment with Amazon EC2, DynamoDB NoSQL Persistence, and SNS Event Notifications")
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(11.5)
    run_sub.font.color.rgb = MUTED

    # ----------------------------------------------------
    # CANDIDATE & PROJECT CREDENTIALS TABLE
    # ----------------------------------------------------
    meta_table = doc.add_table(rows=8, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False

    # Widths: col 0 = 2.2 in, col 1 = 4.6 in
    for row in meta_table.rows:
        row.cells[0].width = Inches(2.2)
        row.cells[1].width = Inches(4.6)

    meta_data = [
        ("Student Name", "SK ABDUL SANDHANI"),
        ("Registration / Roll No.", "24BCA7871"),
        ("Institutional Email", "sandhani.24bca7871@vitapstudent.ac.in"),
        ("Degree & Department", "Bachelor of Computer Applications (BCA), SCSE"),
        ("AWS Deployment Region", "us-east-1 (US East - N. Virginia)"),
        ("Permanent Elastic IP (Static)", "100.48.182.11"),
        ("Live Web Application URL", "http://100.48.182.11/"),
        ("Source Code Repository", "https://github.com/sandhani01/student-registration-aws")
    ]

    set_table_borders(meta_table, color="CBD5E1", sz="6", val="single")

    for idx, (label, val) in enumerate(meta_data):
        c0 = meta_table.cell(idx, 0)
        c1 = meta_table.cell(idx, 1)

        set_cell_margins(c0, top=100, bottom=100, left=140, right=140)
        set_cell_margins(c1, top=100, bottom=100, left=140, right=140)

        # Alternating background
        bg = "F8FAFC" if idx % 2 == 0 else "FFFFFF"
        set_cell_background(c0, bg)
        set_cell_background(c1, bg)

        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(label)
        r0.font.name = "Segoe UI"
        r0.font.size = Pt(9.5)
        r0.font.bold = True
        r0.font.color.rgb = ROYAL

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.name = "Segoe UI"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = CHARCOAL
        if "http" in val:
            r1.font.color.rgb = ACCENT
            r1.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # Helper for adding styled sections
    def add_section_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(title)
        run.font.name = "Segoe UI"
        run.font.size = Pt(13.5)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return p

    def add_body_p(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            bp = p.add_run(bold_prefix)
            bp.font.name = "Segoe UI"
            bp.font.size = Pt(10)
            bp.font.bold = True
            bp.font.color.rgb = CHARCOAL
        r = p.add_run(text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(10)
        r.font.color.rgb = CHARCOAL
        return p

    def add_callout(title, text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        tbl.rows[0].cells[0].width = Inches(6.8)
        cell = tbl.cell(0, 0)
        set_box_borders(tbl, border_color="2563EB", bg_color="EFF6FF")
        set_cell_background(cell, "EFF6FF")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

        cp = cell.paragraphs[0]
        cp.paragraph_format.space_after = Pt(3)
        tr = cp.add_run(title)
        tr.font.name = "Segoe UI"
        tr.font.size = Pt(10)
        tr.font.bold = True
        tr.font.color.rgb = ROYAL

        bp = cell.add_paragraph()
        bp.paragraph_format.space_after = Pt(0)
        bp.paragraph_format.line_spacing = 1.15
        br = bp.add_run(text)
        br.font.name = "Segoe UI"
        br.font.size = Pt(9.5)
        br.font.color.rgb = CHARCOAL

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def add_code_block(code_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        tbl.rows[0].cells[0].width = Inches(6.8)
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        set_table_borders(tbl, color="E2E8F0", sz="4", val="single")

        cp = cell.paragraphs[0]
        cp.paragraph_format.space_after = Pt(0)
        r = cp.add_run(code_text)
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(15, 23, 42)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ----------------------------------------------------
    # SECTION 1: OBJECTIVES & EXECUTIVE SUMMARY
    # ----------------------------------------------------
    add_section_header("1. Executive Summary & Project Objectives")
    add_body_p(
        "This project implements a secure, scalable, and automated cloud-native Student Registration Portal deployed on Amazon Web Services (AWS). "
        "The architecture bridges virtualized compute (Amazon EC2) with fully managed serverless data storage (Amazon DynamoDB) and an asynchronous "
        "notification engine (Amazon Simple Notification Service - SNS)."
    )
    add_body_p(
        "Core design principles enforced in this implementation include: (1) Zero-credential application security by leveraging AWS IAM Instance Profiles (LabRole) "
        "rather than hardcoding IAM access keys in source control; (2) Idempotent database transactions using DynamoDB conditional write expressions to prohibit duplicate "
        "roll number registrations; and (3) Decoupled subscriber communication through event-driven SNS publication."
    )

    add_callout(
        "Architecture Highlight: Zero-Credential Principle",
        "The Flask web application queries the AWS Instance Metadata Service (IMDSv2) via the attached IAM Role (LabRole / LabInstanceProfile). "
        "Temporary AWS security credentials rotate automatically with zero administrative overhead and zero risk of key leakage in git repositories."
    )

    # ----------------------------------------------------
    # SECTION 2: AWS INFRASTRUCTURE & RESOURCE TOPOLOGY
    # ----------------------------------------------------
    add_section_header("2. Deployed AWS Infrastructure Inventory")
    add_body_p("The table below details the complete inventory of AWS cloud components provisioned, configured, and bound to this application:")

    res_table = doc.add_table(rows=6, cols=4)
    res_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    res_table.autofit = False

    widths = [Inches(1.4), Inches(1.8), Inches(2.2), Inches(1.4)]
    for row in res_table.rows:
        for c_idx, w in enumerate(widths):
            row.cells[c_idx].width = w

    headers = ["AWS Service", "Resource Name / Identifier", "Configuration Details", "Security / Network"]
    for c_idx, h in enumerate(headers):
        cell = res_table.cell(0, c_idx)
        set_cell_background(cell, "0F2C59")
        set_cell_margins(cell, top=120, bottom=120, left=100, right=100)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    resources = [
        ("Amazon EC2", "StudentApp-24BCA7871\n(i-09a305ec90d53a8ba)", "t2.micro, Amazon Linux 2023, Gunicorn WSGI + Nginx Proxy", "IAM LabInstanceProfile (LabRole)"),
        ("Elastic IP (EIP)", "100.48.182.11\n(eipassoc-0a271b8f5165c54a5)", "Allocated static IPv4 address associated with EC2 instance", "Public Subnet / IGW Route (0.0.0.0/0)"),
        ("Amazon DynamoDB", "Students-24BCA7871", "NoSQL Table, Partition Key: 24bca7871 (String), On-Demand billing", "AWS KMS Server-Side Encryption"),
        ("Amazon SNS", "StudentRegistration-24BCA7871", "Standard Pub/Sub Topic, Confirmed Email Protocol Subscription", "IAM ec2 publish authorization"),
        ("Security Group", "StudentApp-24BCA7871-sg\n(sg-0be3e88e0cd8a83a0)", "Stateful ingress firewall: Port 22 (SSH), Port 80 (HTTP)", "Stateless NACL Rule 1 (Ephemeral Ports)")
    ]

    set_table_borders(res_table, color="CBD5E1", sz="4", val="single")

    for r_idx, row_data in enumerate(resources, start=1):
        for c_idx, val in enumerate(row_data):
            cell = res_table.cell(r_idx, c_idx)
            bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Segoe UI"
            r.font.size = Pt(8.5)
            r.font.color.rgb = CHARCOAL

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ----------------------------------------------------
    # SECTION 3: SYSTEM ARCHITECTURE & DATA FLOW
    # ----------------------------------------------------
    add_section_header("3. Architecture & Transaction Workflow")
    add_body_p(
        "The application architecture operates on a modular, decoupled flow ensuring that compute resources remain stateless while state persistence "
        "and client communications are offloaded to specialized AWS managed services:"
    )

    flow_steps = [
        ("Step 1 (Client Ingress): ", "The end user connects via web browser to http://100.48.182.11/ on port 80. Nginx intercepts the HTTP request and reverse-proxies it to the internal Gunicorn WSGI master process listening on 127.0.0.1:8000."),
        ("Step 2 (Input Sanitization): ", "The Flask controller validates all payload parameters: Roll Number (24BCA7871), Full Name, Course Name, Year of Study, Institutional Email, and Physical Address."),
        ("Step 3 (Conditional Persistence): ", "The application initializes the Boto3 DynamoDB client and executes a PutItem command with a ConditionExpression ensuring that the roll number does not already exist. If a duplicate record is detected, a clean HTTP 409 conflict is returned without overwriting."),
        ("Step 4 (Asynchronous SNS Publish): ", "Following successful DynamoDB persistence, the backend publishes a structured JSON payload to the Amazon SNS topic StudentRegistration-24BCA7871 containing the student's credentials and submission timestamp."),
        ("Step 5 (Subscriber Notification): ", "Amazon SNS processes the notification and delivers a real-time email receipt to the subscriber endpoint (sandhani.24bca7871@vitapstudent.ac.in)."),
        ("Step 6 (Confirmation Feedback): ", "The web portal renders a modern, high-contrast confirmation card displaying the registered details along with the unique Amazon SNS Message ID as a proof of receipt.")
    ]

    for prefix, body in flow_steps:
        add_body_p(body, bold_prefix=prefix)

    # ----------------------------------------------------
    # SECTION 4: CLI IMPLEMENTATION COMMANDS
    # ----------------------------------------------------
    add_section_header("4. Infrastructure as Code & CLI Provisioning")
    add_body_p("The AWS infrastructure was systematically provisioned using the AWS Command Line Interface (CLI):")

    add_body_p("1. Amazon SNS Topic Creation & Email Subscription:", bold_prefix="Phase 1: ")
    add_code_block(
        "aws sns create-topic --name StudentRegistration-24BCA7871\n"
        "aws sns subscribe \\\n"
        "  --topic-arn arn:aws:sns:us-east-1:394943564062:StudentRegistration-24BCA7871 \\\n"
        "  --protocol email \\\n"
        "  --notification-endpoint sandhani.24bca7871@vitapstudent.ac.in"
    )

    add_body_p("2. Amazon DynamoDB Table Provisioning:", bold_prefix="Phase 2: ")
    add_code_block(
        "aws dynamodb create-table \\\n"
        "  --table-name Students-24BCA7871 \\\n"
        "  --attribute-definitions AttributeName=24bca7871,AttributeType=S \\\n"
        "  --key-schema AttributeName=24bca7871,KeyType=HASH \\\n"
        "  --billing-mode PAY_PER_REQUEST \\\n"
        "  --region us-east-1"
    )

    add_body_p("3. VPC Security Group & Firewall Rules:", bold_prefix="Phase 3: ")
    add_code_block(
        "aws ec2 create-security-group \\\n"
        "  --group-name StudentApp-24BCA7871-sg \\\n"
        "  --description 'Firewall rules for Student Registration Portal'\n\n"
        "aws ec2 authorize-security-group-ingress \\\n"
        "  --group-name StudentApp-24BCA7871-sg --protocol tcp --port 22 --cidr 0.0.0.0/0\n"
        "aws ec2 authorize-security-group-ingress \\\n"
        "  --group-name StudentApp-24BCA7871-sg --protocol tcp --port 80 --cidr 0.0.0.0/0"
    )

    add_body_p("4. Permanent Elastic IP Allocation & Association:", bold_prefix="Phase 4: ")
    add_code_block(
        "# Allocate permanent static public IPv4 address from AWS pool\n"
        "ALLOC_ID=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)\n\n"
        "# Associate permanently with the EC2 instance\n"
        "aws ec2 associate-address --instance-id i-09a305ec90d53a8ba --allocation-id $ALLOC_ID"
    )

    # ----------------------------------------------------
    # SECTION 5: SCREENSHOTS & EMPIRICAL EVIDENCE
    # ----------------------------------------------------
    add_section_header("5. Empirical Verification & Screenshots")
    add_body_p(
        "The following screenshots corroborate the successful configuration, live execution, and operational status of each AWS resource deployed for student 24BCA7871:"
    )

    screenshot_data = [
        ("Figure 1: Student Registration Web Interface (Live on Permanent Elastic IP 100.48.182.11)",
         "d:/AWS/extracted_images/image1_new.png" if os.path.exists("d:/AWS/extracted_images/image1_new.png") else "d:/AWS/extracted_images/image1.jpg",
         "The responsive web interface running on Amazon EC2 via Nginx reverse proxy, providing a clean form with real-time client-side validation."),

        ("Figure 2: Form Submission Confirmation with Transaction & SNS Receipt",
         "d:/AWS/extracted_images/image2.jpg",
         "Confirmation screen displaying successfully persisted student attributes along with the unique Amazon SNS message identifier."),

        ("Figure 3: Amazon SNS Email Subscription Confirmation Notice",
         "d:/AWS/extracted_images/image3.jpg",
         "Confirmation dialog verifying that the institutional endpoint sandhani.24bca7871@vitapstudent.ac.in accepted the SNS subscription topic."),

        ("Figure 4: Automated Event Notification Email Received by Student",
         "d:/AWS/extracted_images/image4.jpg",
         "Real-time email receipt dispatched by Amazon SNS upon DynamoDB write completion, including student name, roll number, and timestamp."),

        ("Figure 5: Amazon SNS Console displaying Active Topic & Confirmed Subscription",
         "d:/AWS/extracted_images/image5.jpg",
         "AWS Console view of StudentRegistration-24BCA7871 showing topic ARN, standard FIFO policy, and active confirmed subscriber status."),

        ("Figure 6: Amazon DynamoDB Table Schema & Configuration",
         "d:/AWS/extracted_images/image6.jpg",
         "Table details for Students-24BCA7871 showing Active status, on-demand capacity mode, primary partition key, and KMS encryption."),

        ("Figure 7: Amazon DynamoDB Items Explorer showing Persisted Records",
         "d:/AWS/extracted_images/image7.jpg",
         "DynamoDB item view verifying student records (Roll Number 24BCA7871) securely persisted across NoSQL attributes."),

        ("Figure 8: Amazon EC2 Console showing Running Instance & Elastic IP",
         "d:/AWS/extracted_images/image8.jpg",
         "EC2 Management Console displaying StudentApp-24BCA7871 (i-09a305ec90d53a8ba), t2.micro instance type, and static Elastic IP 100.48.182.11."),

        ("Figure 9: Security Group Inbound Firewall Rules",
         "d:/AWS/extracted_images/image9.jpg",
         "Security Group StudentApp-24BCA7871-sg demonstrating tightly controlled ingress permissions limited to SSH (22) and HTTP (80).")
    ]

    for title, img_path, caption in screenshot_data:
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(14)
        sp.paragraph_format.space_after = Pt(4)
        sr = sp.add_run(title)
        sr.font.name = "Segoe UI"
        sr.font.size = Pt(10.5)
        sr.font.bold = True
        sr.font.color.rgb = ROYAL

        if os.path.exists(img_path):
            img_p = doc.add_paragraph()
            img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            img_p.paragraph_format.space_before = Pt(2)
            img_p.paragraph_format.space_after = Pt(4)
            # Add image with max width 5.8 inches
            img_run = img_p.add_run()
            img_run.add_picture(img_path, width=Inches(5.8))

        cap_p = doc.add_paragraph()
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_p.paragraph_format.space_before = Pt(0)
        cap_p.paragraph_format.space_after = Pt(12)
        cr = cap_p.add_run(caption)
        cr.font.name = "Segoe UI"
        cr.font.size = Pt(8.5)
        cr.font.italic = True
        cr.font.color.rgb = MUTED

    # ----------------------------------------------------
    # SECTION 6: TECHNICAL CHALLENGES & RESOLUTIONS
    # ----------------------------------------------------
    add_section_header("6. Technical Hardening & Operational Resilience")
    add_body_p(
        "During live integration testing on the AWS infrastructure, two critical network and database challenges were diagnosed and resolved:"
    )

    add_body_p(
        "AWS Network ACLs (NACLs) are stateless, meaning return traffic is not automatically permitted. The default subnet ACL blocked "
        "inbound return traffic from AWS APIs on ephemeral ports (1024–65535), causing Boto3 calls to DynamoDB and SNS to hang for 60 seconds. "
        "This was resolved by creating Rule 1 on acl-06a84164cf14c8f4f allowing full return traffic, dropping API latency to under 50ms.",
        bold_prefix="1. Stateless NACL Ephemeral Port Resolution: "
    )

    add_body_p(
        "DynamoDB expressions parse tokens beginning with digits as numeric literals. Because the table partition key was created as 24bca7871, "
        "raw condition expressions caused syntax errors. The Python application was refactored to use ExpressionAttributeNames={'#pk': pk_name} "
        "and ConditionExpression='attribute_not_exists(#pk)', ensuring complete cross-platform compatibility.",
        bold_prefix="2. DynamoDB Partition Key Token Escaping: "
    )

    # ----------------------------------------------------
    # SECTION 7: CONCLUSION & DELIVERABLES
    # ----------------------------------------------------
    add_section_header("7. Conclusion & Deliverables Summary")
    add_body_p(
        "The automated Student Registration System for student SK ABDUL SANDHANI (24BCA7871) has been successfully designed, provisioned, deployed, "
        "and thoroughly validated on Amazon Web Services. The web application is publicly reachable at the permanent URL http://100.48.182.11/ and operates "
        "with zero credential vulnerability through AWS IAM Instance Profile automation."
    )

    # Save to both target file and v2
    doc.save("d:/AWS/24BCA7871_AWS_PROJECT.docx")
    doc.save("d:/AWS/24BCA7871_AWS_PROJECT_v2.docx")
    print("Report successfully built and saved to d:/AWS/24BCA7871_AWS_PROJECT.docx and v2!")

if __name__ == "__main__":
    build_report()
