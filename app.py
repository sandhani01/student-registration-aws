#!/usr/bin/env python3
"""
Student Registration System on AWS
Flask Web Application with Amazon DynamoDB and Amazon SNS Integration
Designed for AWS Academy Learner Lab Deployment
"""

import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    Response,
)

from pathlib import Path

# ==============================================================================
# Environment Configuration & Project-Level .env Loading
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"

# Module-level configuration variables (accessible globally and mockable in tests)
AWS_REGION: str = "us-east-1"
STUDENT_ROLL_NO_PLACEHOLDER: str = "<MY_UNIVERSITY_ROLL_NUMBER>"
DYNAMODB_TABLE_NAME: str = f"Students-{STUDENT_ROLL_NO_PLACEHOLDER}"
SNS_TOPIC_ARN: Optional[str] = None


def reload_environment():
    """
    Explicitly load or reload environment variables from the project's .env file.
    Ensures that local edits in D:\\AWS\\.env take effect immediately without
    depending on working directory or requiring process restarts.
    """
    global AWS_REGION, STUDENT_ROLL_NO_PLACEHOLDER, DYNAMODB_TABLE_NAME, SNS_TOPIC_ARN

    if DOTENV_PATH.exists():
        load_dotenv(dotenv_path=DOTENV_PATH, override=True)
    else:
        load_dotenv(override=True)

    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    STUDENT_ROLL_NO_PLACEHOLDER = os.getenv("ROLL_NO", "<MY_UNIVERSITY_ROLL_NUMBER>")

    raw_table = os.getenv("DYNAMODB_TABLE")
    if raw_table:
        # If DYNAMODB_TABLE still contains the template placeholder but ROLL_NO is configured, resolve it
        if "<MY_UNIVERSITY_ROLL_NUMBER>" in raw_table and STUDENT_ROLL_NO_PLACEHOLDER != "<MY_UNIVERSITY_ROLL_NUMBER>":
            DYNAMODB_TABLE_NAME = raw_table.replace("<MY_UNIVERSITY_ROLL_NUMBER>", STUDENT_ROLL_NO_PLACEHOLDER)
        else:
            DYNAMODB_TABLE_NAME = raw_table
    else:
        DYNAMODB_TABLE_NAME = f"Students-{STUDENT_ROLL_NO_PLACEHOLDER}"

    SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")


# Initial configuration load on startup
reload_environment()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger("student_registration_app")

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod-12345")
app.config["JSON_SORT_KEYS"] = False

# Regular expression for email validation (RFC 5322 compliant basic structure)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Valid years of study accepted by the system
VALID_YEARS = {"Year 1", "Year 2", "Year 3", "Year 4"}

# ==============================================================================
# AWS Resource Clients (Uses Default Boto3 Credential Provider Chain)
# Automatically acquires credentials via IAM Instance Profile on EC2
# ==============================================================================
def get_dynamodb_resource():
    """Retrieve Boto3 DynamoDB service resource using environment region."""
    return boto3.resource("dynamodb", region_name=AWS_REGION)


def get_sns_client():
    """Retrieve Boto3 SNS client using environment region."""
    return boto3.client("sns", region_name=AWS_REGION)


# ==============================================================================
# Input Validation Helper
# ==============================================================================
def validate_student_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, str]]:
    """
    Validate all 6 required fields:
    1. University Roll Number
    2. Student Name
    3. Course Name
    4. Address
    5. Email
    6. Year of Study
    
    Returns (is_valid, error_message, cleaned_data)
    """
    cleaned: Dict[str, str] = {}
    
    # Required field names
    required_fields = ["roll_no", "name", "course", "address", "email", "year"]
    
    # Check existence and non-empty status
    for field in required_fields:
        val = data.get(field)
        if val is None or not str(val).strip():
            readable_name = field.replace("_", " ").title()
            return False, f"Field '{readable_name}' is required and cannot be empty.", {}
        cleaned[field] = str(val).strip()

    # 1. Validate Roll Number format
    # Roll number should be alphanumeric and between 3 and 30 characters
    roll_no = cleaned["roll_no"].upper()
    cleaned["roll_no"] = roll_no
    if len(roll_no) < 2 or len(roll_no) > 30:
        return False, "University Roll Number must be between 2 and 30 characters.", {}

    # 2. Validate Student Name
    if len(cleaned["name"]) < 2 or len(cleaned["name"]) > 100:
        return False, "Student Name must be between 2 and 100 characters.", {}

    # 3. Validate Course Name
    if len(cleaned["course"]) < 2 or len(cleaned["course"]) > 100:
        return False, "Course Name must be between 2 and 100 characters.", {}

    # 4. Validate Address
    if len(cleaned["address"]) < 5 or len(cleaned["address"]) > 500:
        return False, "Address must be between 5 and 500 characters.", {}

    # 5. Validate Email Format
    email = cleaned["email"].lower()
    cleaned["email"] = email
    if not EMAIL_REGEX.match(email):
        return False, f"The email address '{email}' is not valid. Please enter a valid email format.", {}

    # 6. Validate Year of Study
    year = cleaned["year"]
    # Allow values like "1" or "Year 1" by normalizing
    if year in {"1", "2", "3", "4"}:
        year = f"Year {year}"
        cleaned["year"] = year

    if year not in VALID_YEARS:
        return False, f"Year of Study must be one of: {', '.join(sorted(VALID_YEARS))}.", {}

    return True, None, cleaned


# ==============================================================================
# Routes
# ==============================================================================

@app.route("/", methods=["GET"])
def index():
    """Display the student registration form with current AWS configuration context."""
    # Refresh environment from project .env so that local configuration changes are immediately visible
    reload_environment()

    # Extract friendly topic name from ARN if configured (e.g. StudentRegistration-24BCA7871)
    sns_topic_display = None
    if SNS_TOPIC_ARN and not SNS_TOPIC_ARN.startswith("<"):
        sns_topic_display = SNS_TOPIC_ARN.split(":")[-1]

    return render_template(
        "index.html",
        roll_no_placeholder=STUDENT_ROLL_NO_PLACEHOLDER,
        table_name=DYNAMODB_TABLE_NAME,
        aws_region=AWS_REGION,
        sns_topic_arn=SNS_TOPIC_ARN,
        sns_topic_display=sns_topic_display,
        sns_configured=bool(SNS_TOPIC_ARN and not SNS_TOPIC_ARN.startswith("<")),
    )


@app.route("/register", methods=["POST"])
def register():
    """
    Process student registration:
    1. Validate input fields on the backend.
    2. Save student record in DynamoDB with conditional check (reject duplicates).
    3. Publish notification to Amazon SNS after successful DynamoDB insertion.
    4. Return success view with DynamoDB and SNS publication details.
    """
    # Accept both JSON (AJAX) and Form Data (traditional submission)
    if request.is_json:
        payload = request.get_json() or {}
    else:
        payload = request.form.to_dict()

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json

    # Step 1: Validate input
    is_valid, validation_error, cleaned_data = validate_student_data(payload)
    if not is_valid:
        logger.warning(f"Validation failed: {validation_error}")
        if is_ajax:
            return jsonify({
                "success": False,
                "error_type": "ValidationError",
                "message": validation_error
            }), 400
        return render_template(
            "error.html",
            error_title="Validation Error",
            error_message=validation_error,
            status_code=400,
            submitted_data=payload
        ), 400

    roll_no = cleaned_data["roll_no"]
    student_name = cleaned_data["name"]
    course_name = cleaned_data["course"]
    address = cleaned_data["address"]
    email = cleaned_data["email"]
    year = cleaned_data["year"]
    now_utc = datetime.now(timezone.utc).isoformat()

    # DynamoDB Item schema
    item = {
        "roll_no": roll_no,
        "name": student_name,
        "course": course_name,
        "address": address,
        "email": email,
        "year": year,
        "registered_at": now_utc,
    }

    # Step 2: Save to Amazon DynamoDB with conditional write
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)

        logger.info(f"Attempting DynamoDB conditional write for roll_no: {roll_no} into table: {DYNAMODB_TABLE_NAME}")

        # attribute_not_exists(roll_no) guarantees no duplicate university roll number can overwrite
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(roll_no)"
        )
        logger.info(f"DynamoDB insertion successful for roll_no: {roll_no}")

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "UnknownError")
        raw_message = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"DynamoDB ClientError [{error_code}]: {raw_message}")

        # Check for duplicate roll number condition failure
        if error_code == "ConditionalCheckFailedException":
            duplicate_message = (
                f"Registration rejected: A student with University Roll Number '{roll_no}' "
                "is already registered in DynamoDB. Duplicate roll numbers are not permitted."
            )
            if is_ajax:
                return jsonify({
                    "success": False,
                    "error_type": "DuplicateRollNumber",
                    "message": duplicate_message
                }), 409
            return render_template(
                "error.html",
                error_title="Duplicate Registration Detected",
                error_message=duplicate_message,
                status_code=409,
                submitted_data=cleaned_data
            ), 409

        # Handle ResourceNotFoundException (e.g. table does not exist)
        if error_code == "ResourceNotFoundException":
            db_error_message = (
                f"DynamoDB table '{DYNAMODB_TABLE_NAME}' was not found in AWS region '{AWS_REGION}'. "
                "Please ensure the table has been created according to assignment instructions."
            )
        else:
            db_error_message = f"AWS DynamoDB error occurred: {error_code}. Please check IAM permissions and table configuration."

        if is_ajax:
            return jsonify({
                "success": False,
                "error_type": error_code,
                "message": db_error_message
            }), 500
        return render_template(
            "error.html",
            error_title="Database Operation Failed",
            error_message=db_error_message,
            status_code=500,
            submitted_data=cleaned_data
        ), 500

    except (BotoCoreError, Exception) as ex:
        logger.exception("Unexpected exception during DynamoDB insertion")
        general_error = "An unexpected error occurred while communicating with AWS DynamoDB. Please verify AWS credentials or IAM instance profile."
        if is_ajax:
            return jsonify({
                "success": False,
                "error_type": "InternalServerError",
                "message": general_error
            }), 500
        return render_template(
            "error.html",
            error_title="System Error",
            error_message=general_error,
            status_code=500,
            submitted_data=cleaned_data
        ), 500

    # Step 3: Publish notification through Amazon SNS ONLY AFTER DynamoDB insertion succeeds
    sns_message_id = None
    sns_published = False
    sns_error_notice = None

    if not SNS_TOPIC_ARN or SNS_TOPIC_ARN.startswith("<"):
        sns_error_notice = (
            "SNS topic ARN is not configured in environment variables (SNS_TOPIC_ARN). "
            "The student record was safely saved in DynamoDB, but no SNS notification was dispatched."
        )
        logger.warning(sns_error_notice)
    else:
        try:
            sns_client = get_sns_client()

            sns_subject = f"Student Registration Successful - {roll_no}"
            # SNS subject maximum allowed length is 100 characters
            if len(sns_subject) > 100:
                sns_subject = sns_subject[:97] + "..."

            sns_body = (
                "Student Registration Notification\n\n"
                f"University Roll Number: {roll_no}\n"
                f"Student Name: {student_name}\n"
                f"Course Name: {course_name}\n"
                "Registration Status: SUCCESSFUL\n\n"
                f"Address: {address}\n"
                f"Email: {email}\n"
                f"Year of Study: {year}\n"
                f"Registered At: {now_utc}\n"
                f"DynamoDB Table: {DYNAMODB_TABLE_NAME}\n"
            )

            logger.info(f"Publishing registration notification to SNS Topic: {SNS_TOPIC_ARN}")
            sns_response = sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=sns_subject,
                Message=sns_body
            )

            sns_message_id = sns_response.get("MessageId")
            sns_published = True
            logger.info(f"SNS notification published successfully! MessageId: {sns_message_id}")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "UnknownError")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"SNS ClientError [{error_code}] while publishing: {error_msg}")
            # Note requirement: Record has been saved in DynamoDB! Do NOT claim database failed.
            sns_error_notice = (
                f"Student record was successfully saved in DynamoDB, but SNS publication failed [{error_code}]. "
                "Ensure your IAM role has 'sns:Publish' permissions and the topic ARN exists in your region."
            )
        except Exception as ex:
            logger.exception("Unexpected error publishing to Amazon SNS")
            sns_error_notice = (
                "Student record was successfully saved in DynamoDB, but an unexpected error prevented "
                "SNS notification dispatch. Please check EC2 outbound connectivity."
            )

    # Step 4: Render Success view or JSON response
    response_payload = {
        "success": True,
        "message": "Student registration completed successfully.",
        "student": item,
        "dynamodb": {
            "status": "SAVED",
            "table": DYNAMODB_TABLE_NAME,
            "partition_key": roll_no
        },
        "sns": {
            "published": sns_published,
            "message_id": sns_message_id,
            "topic_arn": SNS_TOPIC_ARN,
            "warning": sns_error_notice
        }
    }

    if is_ajax:
        # 200 OK (even with SNS warning, record was safely stored)
        return jsonify(response_payload), 200

    return render_template(
        "success.html",
        student=item,
        dynamodb_table=DYNAMODB_TABLE_NAME,
        sns_published=sns_published,
        sns_message_id=sns_message_id,
        sns_topic_arn=SNS_TOPIC_ARN,
        sns_warning=sns_error_notice,
    )


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint for EC2 deployment testing, target groups, and uptime monitoring.
    Returns HTTP 200 with runtime diagnostics.
    """
    reload_environment()
    return jsonify({
        "status": "healthy",
        "service": "student-registration-app",
        "server_time_utc": datetime.now(timezone.utc).isoformat(),
        "aws_region": AWS_REGION,
        "dynamodb_table": DYNAMODB_TABLE_NAME,
        "sns_configured": bool(SNS_TOPIC_ARN and not SNS_TOPIC_ARN.startswith("<")),
        "configured_roll_no": STUDENT_ROLL_NO_PLACEHOLDER
    }), 200


# ==============================================================================
# Error Handlers
# ==============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found without leaking sensitive context."""
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": False, "error": "Endpoint not found"}), 404
    return render_template(
        "error.html",
        error_title="Page Not Found (404)",
        error_message="The requested resource or endpoint could not be found on this server.",
        status_code=404
    ), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 Internal Server Error securely."""
    logger.error(f"Internal server error: {error}")
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": False, "error": "Internal server error"}), 500
    return render_template(
        "error.html",
        error_title="Internal Server Error (500)",
        error_message="An unexpected internal server error occurred. Please contact the administrator or check system logs.",
        status_code=500
    ), 500


# ==============================================================================
# Application Entry Point
# ==============================================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

    logger.info(f"Starting Student Registration Web Application on {host}:{port}")
    logger.info(f"Configured DynamoDB Table: {DYNAMODB_TABLE_NAME}")
    logger.info(f"Configured AWS Region: {AWS_REGION}")
    logger.info(f"Configured SNS Topic ARN: {SNS_TOPIC_ARN or 'Not configured'}")

    app.run(host=host, port=port, debug=debug_mode)
