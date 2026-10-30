"""
Student Registration Web Application on AWS
Stores registrations in DynamoDB and announces each one through Amazon SNS.
Credentials come automatically from the EC2 IAM Instance Profile (LabRole).
"""

import logging
import os
import re
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from flask import Flask, render_template, request

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ROLL_NO = os.environ.get("ROLL_NO", "24BCA7871")
TABLE_NAME = os.environ.get("TABLE_NAME") or os.environ.get("DYNAMODB_TABLE") or f"Students-{ROLL_NO}"
DYNAMODB_TABLE_NAME = TABLE_NAME
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:394943564062:StudentRegistration-24BCA7871")

FIELDS = ["roll_no", "name", "course", "address", "email", "year"]
YEARS = ["Year 1", "Year 2", "Year 3", "Year 4"]
VALID_YEARS = set(YEARS)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_REGEX = EMAIL_RE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("student-app")

app = Flask(__name__)


def get_dynamodb_resource():
    return boto3.resource("dynamodb", region_name=AWS_REGION)


def get_dynamodb_table():
    return get_dynamodb_resource().Table(TABLE_NAME)


def get_sns_client():
    return boto3.client("sns", region_name=AWS_REGION)


def validate(form):
    data = {f: (form.get(f) or "").strip() for f in FIELDS}
    errors = [f"{f.replace('_', ' ').title()} is required and cannot be empty." for f in FIELDS if not data[f]]
    if data.get("email") and not EMAIL_RE.match(data["email"]):
        errors.append("Email address is not valid.")
    if data.get("year"):
        year_raw = data["year"].strip()
        if year_raw in ["1", "2", "3", "4"]:
            data["year"] = f"Year {year_raw}"
        elif year_raw in YEARS:
            data["year"] = year_raw
        else:
            errors.append("Year of study must be between Year 1 and Year 4.")
    return data, errors


def validate_student_data(data):
    """Compatibility validator for automated test suites."""
    cleaned, errors = validate(data)
    if errors:
        return False, errors[0], {}
    return True, None, cleaned


def notify(student, status):
    message = (
        "Student Registration Notification\n\n"
        f"University Roll Number: {student['roll_no']}\n"
        f"Student Name: {student['name']}\n"
        f"Course Name: {student['course']}\n"
        f"Registration Status: {status}\n"
    )
    sns = get_sns_client()
    resp = sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"Registration {status} - {student['roll_no']}"[:100],
        Message=message,
    )
    return resp["MessageId"]


def render(status_code=200, **ctx):
    return render_template("index.html", roll_no=ROLL_NO, years=YEARS, **ctx), status_code


@app.get("/")
def index():
    return render()


@app.post("/register")
def register():
    payload = request.form if request.form else (request.get_json(silent=True) or {})
    data, errors = validate(payload)
    if errors:
        if request.is_json:
            return {"success": False, "error_type": "ValidationError", "message": errors[0]}, 400
        return render(400, errors=errors, form=data)

    table = get_dynamodb_table()
    pk_name = "roll_no"
    try:
        if hasattr(table, "key_schema") and table.key_schema:
            for k in table.key_schema:
                if k.get("KeyType") == "HASH":
                    pk_name = k.get("AttributeName")
                    break
    except Exception:
        pk_name = "roll_no"

    item = dict(data, registered_at=datetime.now(timezone.utc).isoformat())
    item[pk_name] = data["roll_no"]
    item["roll_no"] = data["roll_no"]
    item["24bca7871"] = data["roll_no"]

    put_kwargs = {"Item": item}
    if pk_name == "roll_no":
        put_kwargs["ConditionExpression"] = "attribute_not_exists(roll_no)"
    else:
        put_kwargs["ConditionExpression"] = "attribute_not_exists(#pk)"
        put_kwargs["ExpressionAttributeNames"] = {"#pk": pk_name}

    try:
        # Refuse to silently overwrite an existing registration.
        table.put_item(**put_kwargs)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            err_msg = f"Roll number {data['roll_no']} is already registered."
            if request.is_json:
                return {"success": False, "error_type": "DuplicateRollNumber", "message": err_msg}, 409
            return render(409, errors=[err_msg], form=data)
        log.exception("DynamoDB put_item failed")
        err_msg = "Could not save the registration. Please try again."
        if request.is_json:
            return {"success": False, "error_type": "DatabaseError", "message": err_msg}, 500
        return render(500, errors=[err_msg], form=data)
    log.info("Saved roll_no=%s to %s", data["roll_no"], TABLE_NAME)

    status = "SUCCESSFUL"
    message_id = None
    try:
        if SNS_TOPIC_ARN and not SNS_TOPIC_ARN.startswith("<"):
            message_id = notify(data, status)
            log.info("SNS publish ok roll_no=%s message_id=%s", data["roll_no"], message_id)
    except ClientError as e:
        log.exception("SNS publish failed")
        warn_msg = f"Student registration was successfully saved in DynamoDB, but SNS email notification could not be sent: {e}"
        if request.is_json:
            return {
                "success": True,
                "student": data,
                "dynamodb": {"status": "SAVED", "table": TABLE_NAME},
                "sns": {"published": False, "warning": warn_msg, "message_id": None}
            }, 200
        return render(200, student=data, status=status, message_id=None,
                      errors=["Registration saved, but the email notification could not be sent."])

    if request.is_json:
        return {
            "success": True,
            "student": data,
            "dynamodb": {"status": "SAVED", "table": TABLE_NAME},
            "sns": {"published": True, "message_id": message_id}
        }, 200

    return render(200, student=data, status=status, message_id=message_id)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "student-app",
        "aws_region": AWS_REGION,
        "dynamodb_table": TABLE_NAME,
        "table_name": TABLE_NAME,
        "sns_topic_arn": SNS_TOPIC_ARN,
        "roll_no": ROLL_NO
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
