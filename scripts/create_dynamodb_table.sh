#!/usr/bin/env bash
# ==============================================================================
# Script: create_dynamodb_table.sh
# Purpose: Create Amazon DynamoDB Table for Student Registration System
# Requirements:
#   - Partition Key: roll_no (String)
#   - Billing Mode: PAY_PER_REQUEST (On-Demand)
# ==============================================================================

set -euo pipefail

# Configuration placeholders - replace with your actual roll number if not set in environment
ROLL_NO="${ROLL_NO:-<MY_UNIVERSITY_ROLL_NUMBER>}"
AWS_REGION="${AWS_REGION:-us-east-1}"
TABLE_NAME="${DYNAMODB_TABLE:-Students-${ROLL_NO}}"

echo "=========================================================="
echo "Amazon DynamoDB Provisioning Script"
echo "Target Table Name: ${TABLE_NAME}"
echo "AWS Region:        ${AWS_REGION}"
echo "Partition Key:     roll_no (String)"
echo "Billing Mode:      PAY_PER_REQUEST"
echo "=========================================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: 'aws' CLI executable was not found. Please install the AWS CLI or run via AWS CloudShell." >&2
    exit 1
fi

# Step 1: Check if table already exists
echo "Checking if table '${TABLE_NAME}' already exists..."
if aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" > /dev/null 2>&1; then
    echo "Notice: Table '${TABLE_NAME}' already exists in region '${AWS_REGION}'."
    TABLE_STATUS=$(aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" --query "Table.TableStatus" --output text)
    echo "Current Table Status: ${TABLE_STATUS}"
    exit 0
fi

# Step 2: Create DynamoDB table
echo "Creating table '${TABLE_NAME}'..."
aws dynamodb create-table \
    --table-name "${TABLE_NAME}" \
    --attribute-definitions AttributeName=roll_no,AttributeType=S \
    --key-schema AttributeName=roll_no,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "${AWS_REGION}" \
    --tags Key=Project,Value=StudentRegistration Key=StudentRollNo,Value="${ROLL_NO}"

# Step 3: Wait for table to become ACTIVE
echo "Waiting for table '${TABLE_NAME}' to become ACTIVE..."
aws dynamodb wait table-exists \
    --table-name "${TABLE_NAME}" \
    --region "${AWS_REGION}"

TABLE_STATUS=$(aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" --query "Table.TableStatus" --output text)
TABLE_ARN=$(aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${AWS_REGION}" --query "Table.TableArn" --output text)

echo "=========================================================="
echo "SUCCESS: DynamoDB Table is ACTIVE!"
echo "Table Name:   ${TABLE_NAME}"
echo "Status:       ${TABLE_STATUS}"
echo "Table ARN:    ${TABLE_ARN}"
echo "=========================================================="
echo "You can now capture your assignment screenshot from the AWS Console:"
echo "Navigate to: DynamoDB -> Tables -> ${TABLE_NAME}"
