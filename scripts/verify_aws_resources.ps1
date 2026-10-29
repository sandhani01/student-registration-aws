<#
.SYNOPSIS
    Verifies AWS DynamoDB and SNS configurations for the Student Registration System.
#>

[CmdletBinding()]
param (
    [string]$RollNo = $env:ROLL_NO,
    [string]$Region = $env:AWS_REGION,
    [string]$TableName = $env:DYNAMODB_TABLE,
    [string]$TopicArn = $env:SNS_TOPIC_ARN
)

if (-not $RollNo) { $RollNo = "<MY_UNIVERSITY_ROLL_NUMBER>" }
if (-not $Region) { $Region = "us-east-1" }
if (-not $TableName) { $TableName = "Students-$RollNo" }

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "AWS Resource Verification Utility (PowerShell)" -ForegroundColor Cyan
Write-Host "Roll Number:    $RollNo"
Write-Host "AWS Region:     $Region"
Write-Host "DynamoDB Table: $TableName"
Write-Host "==========================================================" -ForegroundColor Cyan

$awsCmd = Get-Command aws -ErrorAction SilentlyContinue
if (-not $awsCmd) {
    Write-Warning "'aws' CLI was not found. Please verify using the AWS Console."
    exit 1
}

# 1. DynamoDB Table Check
Write-Host "`n[1/3] Checking DynamoDB Table '$TableName'..." -ForegroundColor Yellow
$table = aws dynamodb describe-table --table-name $TableName --region $Region 2>$null | ConvertFrom-Json
if ($table) {
    Write-Host "  Table Status:   $($table.Table.TableStatus)" -ForegroundColor Green
    Write-Host "  Partition Key:  $($table.Table.KeySchema[0].AttributeName)" -ForegroundColor Green
    Write-Host "  Billing Mode:   $($table.Table.BillingModeSummary.BillingMode)" -ForegroundColor Green
    Write-Host "  Total Items:    $($table.Table.ItemCount)" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Table '$TableName' not found in $Region." -ForegroundColor Red
}

# 2. DynamoDB Items
Write-Host "`n[2/3] Scanning DynamoDB for Stored Records..." -ForegroundColor Yellow
aws dynamodb scan --table-name $TableName --region $Region --max-items 5

# 3. SNS Check
Write-Host "`n[3/3] Checking SNS Topic..." -ForegroundColor Yellow
if ($TopicArn -and $TopicArn -notlike "*<*") {
    aws sns list-subscriptions-by-topic --topic-arn $TopicArn --region $Region
} else {
    Write-Host "  SNS_TOPIC_ARN not set. Listing all student topics:"
    aws sns list-topics --region $Region
}

Write-Host "`nVerification check complete." -ForegroundColor Cyan
