<#
.SYNOPSIS
    Creates the Amazon DynamoDB table for the Student Registration System.
.DESCRIPTION
    Provisions a DynamoDB table with partition key 'roll_no' (String) and PAY_PER_REQUEST billing mode.
#>

[CmdletBinding()]
param (
    [string]$RollNo = $env:ROLL_NO,
    [string]$Region = $env:AWS_REGION,
    [string]$TableName = $env:DYNAMODB_TABLE
)

if (-not $RollNo) { $RollNo = "<MY_UNIVERSITY_ROLL_NUMBER>" }
if (-not $Region) { $Region = "us-east-1" }
if (-not $TableName) { $TableName = "Students-$RollNo" }

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Amazon DynamoDB Provisioning Script (PowerShell)" -ForegroundColor Cyan
Write-Host "Table Name:    $TableName"
Write-Host "AWS Region:    $Region"
Write-Host "Partition Key: roll_no (String)"
Write-Host "Billing Mode:  PAY_PER_REQUEST"
Write-Host "==========================================================" -ForegroundColor Cyan

# Check for AWS CLI
$awsCmd = Get-Command aws -ErrorAction SilentlyContinue
if (-not $awsCmd) {
    Write-Warning "'aws' CLI was not found on your system. Run this in AWS CloudShell or configure AWS CLI."
    exit 1
}

# Check if table exists
Write-Host "Checking if table '$TableName' exists..."
$exists = aws dynamodb describe-table --table-name $TableName --region $Region 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Notice: Table '$TableName' already exists in region '$Region'." -ForegroundColor Yellow
    exit 0
}

# Create table
Write-Host "Creating DynamoDB table '$TableName'..." -ForegroundColor Green
aws dynamodb create-table `
    --table-name $TableName `
    --attribute-definitions AttributeName=roll_no,AttributeType=S `
    --key-schema AttributeName=roll_no,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST `
    --region $Region `
    --tags Key=Project,Value=StudentRegistration Key=StudentRollNo,Value=$RollNo

# Wait for table
Write-Host "Waiting for table '$TableName' to become ACTIVE..." -ForegroundColor Yellow
aws dynamodb wait table-exists --table-name $TableName --region $Region

Write-Host "SUCCESS: DynamoDB table '$TableName' is now ACTIVE and ready for registration records!" -ForegroundColor Green
