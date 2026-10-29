#!/usr/bin/env bash
# ==============================================================================
# Script: verify_aws_resources.sh
# Purpose: Comprehensive Verification of AWS Academy Learner Lab Resources
# Checks DynamoDB Table, DynamoDB Items, SNS Topic, Subscriptions, and EC2 Health
# ==============================================================================

set -euo pipefail

ROLL_NO="${ROLL_NO:-<MY_UNIVERSITY_ROLL_NUMBER>}"
AWS_REGION="${AWS_REGION:-us-east-1}"
TABLE_NAME="${DYNAMODB_TABLE:-Students-${ROLL_NO}}"
SNS_TOPIC_ARN="${SNS_TOPIC_ARN:-}"

echo "=========================================================="
echo "AWS Resource Verification Utility"
echo "Roll Number:    ${ROLL_NO}"
echo "AWS Region:     ${AWS_REGION}"
echo "DynamoDB Table: ${TABLE_NAME}"
echo "=========================================================="

# 1. DynamoDB Table Verification
echo -e "\n[1/4] Verifying DynamoDB Table..."
if aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" > /dev/null 2>&1; then
    STATUS=$(aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" --query "Table.TableStatus" --output text)
    KEY_NAME=$(aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" --query "Table.KeySchema[0].AttributeName" --output text)
    ITEM_COUNT=$(aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" --query "Table.ItemCount" --output text)
    BILLING_MODE=$(aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" --query "Table.BillingModeSummary.BillingMode" --output text 2>/dev/null || echo "PAY_PER_REQUEST")
    
    echo "  Status:        ${STATUS}"
    echo "  Partition Key: ${KEY_NAME}"
    echo "  Billing Mode:  ${BILLING_MODE}"
    echo "  Item Count:    ${ITEM_COUNT}"
    echo "  PASS: DynamoDB table is properly configured."
else
    echo "  FAIL: DynamoDB table '${TABLE_NAME}' not found in region '${AWS_REGION}'."
fi

# 2. DynamoDB Items Inspection
echo -e "\n[2/4] Inspecting Stored Student Records in DynamoDB..."
if aws dynamodb scan --table-name "${TABLE_NAME}" --region "${AWS_REGION}" --max-items 5 > /tmp/dynamo_items.json 2>&1; then
    COUNT=$(cat /tmp/dynamo_items.json | grep -c '"roll_no"' || true)
    echo "  Found ${COUNT} student records in table."
    echo "  Latest Items Sample:"
    aws dynamodb scan --table-name "${TABLE_NAME}" --region "${AWS_REGION}" \
        --projection-expression "roll_no, #n, course, email, registered_at" \
        --expression-attribute-names '{"#n": "name"}' \
        --query "Items[*].[roll_no.S, name.S, course.S, email.S, registered_at.S]" \
        --output table
else
    echo "  Unable to scan table items (check IAM permissions or table existence)."
fi

# 3. Amazon SNS Topic & Subscriptions Verification
echo -e "\n[3/4] Verifying Amazon SNS Topic & Subscription..."
if [ -n "${SNS_TOPIC_ARN}" ] && [[ "${SNS_TOPIC_ARN}" != *"<"* ]]; then
    echo "  Checking Topic: ${SNS_TOPIC_ARN}"
    if aws sns get-topic-attributes --topic-arn "${SNS_TOPIC_ARN}" --region "${AWS_REGION}" > /dev/null 2>&1; then
        echo "  PASS: SNS Topic exists and is accessible."
        echo "  Listing Subscriptions:"
        aws sns list-subscriptions-by-topic --topic-arn "${SNS_TOPIC_ARN}" --region "${AWS_REGION}" \
            --query "Subscriptions[*].[Protocol, Endpoint, SubscriptionArn]" \
            --output table
        echo "  NOTE: If SubscriptionArn shows 'PendingConfirmation', confirm the email in your inbox!"
    else
        echo "  FAIL: Cannot access SNS Topic with ARN: ${SNS_TOPIC_ARN}"
    fi
else
    echo "  SNS_TOPIC_ARN is not set. Listing all topics matching StudentRegistration in region:"
    aws sns list-topics --region "${AWS_REGION}" --query "Topics[?contains(TopicArn, 'StudentRegistration')].TopicArn" --output text || true
fi

# 4. Local Health Check
echo -e "\n[4/4] Verifying Web Application Local Health Check (Port 80 / Port 5000)..."
if curl -s http://127.0.0.1/health > /dev/null 2>&1; then
    echo "  Port 80 (Nginx): Responsive!"
    curl -s http://127.0.0.1/health | python3 -m json.tool
elif curl -s http://127.0.0.1:5000/health > /dev/null 2>&1; then
    echo "  Port 5000 (Gunicorn): Responsive!"
    curl -s http://127.0.0.1:5000/health | python3 -m json.tool
else
    echo "  Web server is not currently responding on 127.0.0.1 (app may not be running locally)."
fi

echo -e "\n=========================================================="
echo "Verification Complete."
echo "=========================================================="
