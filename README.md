# Student Registration System on AWS

A production-ready, cloud-native student registration web application built for the **AWS Academy Learner Lab** practical assignment. The application runs on **Amazon EC2 (Amazon Linux 2023)**, utilizes **Amazon DynamoDB** for transactional persistence with conditional writes to prevent duplicate roll numbers, and integrates with **Amazon SNS** to publish email notifications upon successful registration.

---

## 1. Project Objective

The primary objective of this project is to build and deploy an end-to-end, multi-tier web application adhering to AWS Well-Architected principles within the constraints of the AWS Academy Learner Lab environment.

The application collects the following student details:
1. **University Roll Number** (Unique Partition Key)
2. **Student Name**
3. **Course Name**
4. **Address**
5. **Email Address**
6. **Year of Study** (Years 1, 2, 3, or 4)

### Core Workflow:
1. Student inputs are validated both client-side (HTML5/JavaScript) and server-side (Python Flask).
2. The student profile is saved in **Amazon DynamoDB** using a conditional write (`attribute_not_exists(roll_no)`). Duplicate roll numbers are rejected with an explicit HTTP 409 error.
3. Only after the DynamoDB insertion succeeds, a message is published to the configured **Amazon SNS** topic.
4. An email notification is sent to confirmed subscribers containing student details and registration status.
5. The application renders a comprehensive confirmation view containing the record details and the **SNS Message ID**.
6. If database or notification operations encounter an issue, informative, security-conscious error messages are presented without exposing AWS credentials or raw stack traces.

---

## 2. Architecture & Data Flow

```text
[ Student Browser ]
       |
       | HTTP Port 80 (GET / or POST /register)
       v
[ Nginx Reverse Proxy (Port 80) ]
       |
       | Proxy Pass (127.0.0.1:5000)
       v
[ Gunicorn WSGI Server + Flask Web App (EC2 AL2023) ]
       |
       | (IAM Instance Profile: LabRole - Temporary Boto3 Credentials)
       |
       +---> [ Amazon DynamoDB (Table: Students-<ROLL_NO>) ]
       |       - Partition Key: roll_no
       |       - Condition: attribute_not_exists(roll_no)
       |       - Rejects duplicates
       |
       | (Only after DynamoDB write succeeds)
       |
       +---> [ Amazon SNS Topic (StudentRegistration-<ROLL_NO>) ]
               |
               v
     [ Email Notification ] ---> [ Student / Faculty Inbox ]
```

---

## 3. Technologies Used

* **Programming Language**: Python 3 (Tested on 3.11+ and 3.13)
* **Web Framework**: Flask 3.x
* **WSGI Server**: Gunicorn
* **Reverse Proxy**: Nginx
* **AWS SDK**: Boto3 (Amazon Web Services SDK for Python)
* **AWS Cloud Services**:
  * **Amazon EC2**: Amazon Linux 2023 (`t2.micro` or `t3.micro`)
  * **Amazon DynamoDB**: NoSQL Database (Pay-Per-Request on-demand billing)
  * **Amazon SNS**: Simple Notification Service (Standard Topic & Email Protocol)
  * **AWS IAM**: IAM Instance Profile (`LabRole`) for zero-credential keyless authentication
* **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom Design System with Inter typography), Vanilla JavaScript

---

## 4. Project Structure

```text
student-registration-aws/
│
├── app.py                             # Core Flask application & AWS Boto3 logic
├── requirements.txt                   # Production Python dependencies
├── README.md                          # Complete project documentation & guide
├── .gitignore                         # Git exclusion rules (prevents credential leaks)
├── .env.example                       # Environment variables template
│
├── templates/                         # Jinja2 HTML5 UI Templates
│   ├── base.html                      # Layout shell with navigation & footer
│   ├── index.html                     # Registration form with 6 required inputs
│   ├── success.html                   # Confirmation page with SNS Message ID evidence
│   └── error.html                     # Error page handling duplicates and AWS errors
│
├── static/                            # Static Web Assets
│   ├── css/
│   │   └── style.css                  # Modern responsive stylesheet (light blue accent)
│   └── js/
│       └── app.js                     # Client validation & interactive states
│
├── deploy/                            # Production Deployment Artifacts
│   ├── student-registration.service   # Systemd unit file for Gunicorn
│   ├── nginx.conf                     # Nginx reverse proxy configuration (Port 80)
│   ├── userdata.sh                    # EC2 User Data bootstrap script (AL2023)
│   └── least_privilege_policy.json    # Reference least-privilege IAM policy
│
├── scripts/                           # Automation & Verification Utilities
│   ├── create_dynamodb_table.sh       # Bash script to create DynamoDB table via AWS CLI
│   ├── create_dynamodb_table.ps1      # PowerShell script for Windows users
│   ├── verify_aws_resources.sh        # Bash script to verify table, items, SNS & health
│   └── verify_aws_resources.ps1       # PowerShell script to verify AWS resources
│
└── tests/                             # Automated Test Suite
    └── test_app.py                    # Unit and integration tests (11 test cases)
```

---

## 5. Prerequisites

Before deploying the project, ensure you have:
1. Access to **AWS Academy Learner Lab** with active session credits.
2. Your assigned **University Roll Number** (e.g., `21BCE1042`).
3. An active email address to receive SNS notifications.
4. An SSH key pair created in AWS EC2 (e.g., `vockey` or your custom key).

---

## 6. Student-Specific Configuration Placeholders

In this project, configuration values use standard placeholders. **You will replace these placeholders with your actual details:**

| Configuration Variable | Placeholder Value | Example Replacement |
|---|---|---|
| Student Roll Number | `<MY_UNIVERSITY_ROLL_NUMBER>` | `21BCE1042` |
| AWS Region | `us-east-1` | `us-east-1` |
| DynamoDB Table | `Students-<MY_UNIVERSITY_ROLL_NUMBER>` | `Students-21BCE1042` |
| SNS Topic Name | `StudentRegistration-<MY_UNIVERSITY_ROLL_NUMBER>` | `StudentRegistration-21BCE1042` |
| EC2 Instance Name | `StudentApp-<MY_UNIVERSITY_ROLL_NUMBER>` | `StudentApp-21BCE1042` |
| Security Group Name | `StudentApp-<MY_UNIVERSITY_ROLL_NUMBER>-sg` | `StudentApp-21BCE1042-sg` |

> [!IMPORTANT]
> **No AWS Access Keys or Secret Keys should ever be hard-coded or placed in files committed to version control.** On EC2, Boto3 automatically retrieves credentials via the IAM Instance Profile (`LabRole`).

---

## 7. AWS Resource Setup (Exact Execution Order)

Follow this precise sequence to configure your AWS environment in the AWS Management Console:

### Step 1: Verify the Learner Lab IAM Role
1. In the AWS Management Console, search for **IAM** in the top search bar.
2. Click **Roles** in the left navigation menu.
3. Locate **`LabRole`**. Click on it.
4. Verify that `LabRole` has policies granting `AmazonDynamoDBFullAccess` and `AmazonSNSFullAccess` (standard in AWS Academy Learner Lab).
5. Note your 12-digit **AWS Account ID** shown in the top right user menu.

### Step 2: Create the Amazon DynamoDB Table
1. Open the **Amazon DynamoDB** console in `us-east-1` (N. Virginia).
2. Click **Create table**.
3. Configure the following parameters:
   * **Table name**: `Students-<MY_UNIVERSITY_ROLL_NUMBER>` (e.g., `Students-21BCE1042`)
   * **Partition key**: `roll_no` (Type: **String**)
   * **Sort key**: *Leave blank*
   * **Table settings**: Select **Customize settings**
   * **Capacity mode**: Select **On-demand** (`PAY_PER_REQUEST`)
4. Click **Create table**.
5. Wait until the table status changes from *Creating* to **Active**.

*Alternative (AWS CloudShell / CLI):*
```bash
aws dynamodb create-table \
    --table-name "Students-<MY_UNIVERSITY_ROLL_NUMBER>" \
    --attribute-definitions AttributeName=roll_no,AttributeType=S \
    --key-schema AttributeName=roll_no,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

### Step 3: Create the Amazon SNS Topic & Email Subscription
1. Open the **Amazon SNS** console in `us-east-1`.
2. In the left navigation, click **Topics**, then click **Create topic**.
3. Choose **Standard** type.
4. Set **Name** to: `StudentRegistration-<MY_UNIVERSITY_ROLL_NUMBER>` (e.g., `StudentRegistration-21BCE1042`).
5. Set **Display name** to: `StudentReg` (or keep it under 100 characters).
6. Click **Create topic**.
7. Copy the generated **Topic ARN** (e.g., `arn:aws:sns:us-east-1:123456789012:StudentRegistration-21BCE1042`).
8. On the topic details page, click **Create subscription**:
   * **Protocol**: Select **Email**
   * **Endpoint**: Enter your personal or academic email address.
9. Click **Create subscription**.
10. The status will initially display as **`PendingConfirmation`**.

### Step 4: Confirm SNS Email Subscription
1. Open your email inbox (and check Spam/Promotions if not visible within 60 seconds).
2. Look for an email from **AWS Notifications** with the subject:
   `AWS Notification - Subscription Confirmation`.
3. Click the **"Confirm subscription"** link in the email body.
4. A web browser tab will open showing: *"Subscription confirmed!"*.
5. Refresh the Amazon SNS console. The subscription status will now display as **`Confirmed`** with a valid Subscription ARN.

### Step 5: Create the EC2 Security Group
1. Open the **Amazon EC2** console in `us-east-1`.
2. Under **Network & Security**, click **Security Groups** -> **Create security group**.
3. **Security group name**: `StudentApp-<MY_UNIVERSITY_ROLL_NUMBER>-sg`.
4. **Description**: `Security group for Student Registration Web App on Port 80 and SSH`.
5. **VPC**: Default VPC.
6. **Inbound rules**:
   * **Rule 1 (HTTP)**:
     * Type: **HTTP**
     * Port range: `80`
     * Source: `Anywhere-IPv4` (`0.0.0.0/0`)
   * **Rule 2 (SSH)**:
     * Type: **SSH**
     * Port range: `22`
     * Source: **My IP** (Restricts administration access to your current IP address for security)
7. Click **Create security group**.

### Step 6: Launch the Amazon EC2 Instance
1. In the EC2 Console, click **Launch instances**.
2. **Name**: `StudentApp-<MY_UNIVERSITY_ROLL_NUMBER>`.
3. **Application and OS Images (AMI)**: **Amazon Linux 2023 AMI** (64-bit x86).
4. **Instance type**: `t2.micro` or `t3.micro` (Free tier eligible / Learner Lab supported).
5. **Key pair**: Select your existing key pair (e.g. `vockey`) or create one.
6. **Network settings**:
   * Click **Edit**.
   * Auto-assign public IP: **Enable**.
   * Select existing security group: `StudentApp-<MY_UNIVERSITY_ROLL_NUMBER>-sg`.
7. **Advanced details (CRITICAL)**:
   * **IAM instance profile**: Select **`LabRole`**. *(If omitted, the app will not have permissions to access DynamoDB or SNS!)*
8. Click **Launch instance**.
9. Note down the **Public IPv4 Address** of your instance once running.

---

## 8. EC2 Deployment Instructions

### Method A: Manual Step-by-Step Deployment (Recommended for Understanding)

1. **Connect to your EC2 instance via SSH**:
   ```bash
   ssh -i /path/to/your-key.pem ec2-user@<EC2_PUBLIC_IP>
   ```

2. **Update the system and install required packages**:
   ```bash
   sudo dnf update -y
   sudo dnf install -y python3 python3-pip git nginx
   ```

3. **Create the application directory**:
   ```bash
   sudo mkdir -p /opt/student-registration /var/log/student-registration
   sudo chown -R ec2-user:ec2-user /opt/student-registration /var/log/student-registration
   ```

4. **Copy the application code to `/opt/student-registration`**:
   *You can clone your GitHub repository or copy files via SCP:*
   ```bash
   # Option 1: Git clone
   git clone https://github.com/<your-username>/student-registration-aws.git /opt/student-registration

   # Option 2: SCP from local machine
   # scp -i key.pem -r ./* ec2-user@<EC2_PUBLIC_IP>:/opt/student-registration/
   ```

5. **Set up Python Virtual Environment & Install Dependencies**:
   ```bash
   cd /opt/student-registration
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. **Create the Environment File at `/etc/student-registration.env`**:
   ```bash
   sudo bash -c 'cat <<EOF > /etc/student-registration.env
   ROLL_NO=<MY_UNIVERSITY_ROLL_NUMBER>
   AWS_REGION=us-east-1
   DYNAMODB_TABLE=Students-<MY_UNIVERSITY_ROLL_NUMBER>
   SNS_TOPIC_ARN=arn:aws:sns:us-east-1:<AWS_ACCOUNT_ID>:StudentRegistration-<MY_UNIVERSITY_ROLL_NUMBER>
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=production-secret-key-student-portal-2024
   PORT=5000
   HOST=127.0.0.1
   EOF'

   sudo chmod 600 /etc/student-registration.env
   sudo chown ec2-user:ec2-user /etc/student-registration.env
   ```

7. **Configure and Enable the Systemd Service**:
   ```bash
   sudo cp /opt/student-registration/deploy/student-registration.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable student-registration.service
   sudo systemctl start student-registration.service
   ```

8. **Configure Nginx as Reverse Proxy on Port 80**:
   ```bash
   sudo cp /opt/student-registration/deploy/nginx.conf /etc/nginx/conf.d/student-registration.conf
   
   # Prevent conflict with default server block
   sudo sed -i 's/listen       80 default_server;/listen       8080 default_server;/g' /etc/nginx/nginx.conf 2>/dev/null || true

   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

9. **Verify Service Status**:
   ```bash
   sudo systemctl status student-registration.service
   sudo systemctl status nginx
   curl -i http://127.0.0.1/health
   ```

---

### Method B: Automated Bootstrap via EC2 User Data

When launching the EC2 instance, paste the contents of [`deploy/userdata.sh`](file:///d:/AWS/deploy/userdata.sh) into the **Advanced details -> User data** box (after updating the configuration placeholders with your roll number and account ID). The instance will configure, install, and start the application automatically upon first boot.

---

## 9. Local Development & Testing Instructions

To run the application locally on your workstation:

1. **Clone the repository and navigate into it**:
   ```bash
   cd student-registration-aws
   ```

2. **Create a local environment file**:
   ```bash
   # Copy template
   cp .env.example .env
   ```
   Edit `.env` and fill in your details:
   ```ini
   ROLL_NO=21BCE1042
   AWS_REGION=us-east-1
   DYNAMODB_TABLE=Students-21BCE1042
   SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:StudentRegistration-21BCE1042
   PORT=5000
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the automated unit & integration test suite**:
   ```bash
   python -m pytest tests/test_app.py -v
   ```
   *Expected output: All 11 tests pass.*

5. **Start the local Flask development server**:
   ```bash
   python app.py
   ```
   Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 10. Testing Procedure

Follow this verification matrix to ensure all requirements are met:

| Test Case | Procedure | Expected Result |
|---|---|---|
| **1. Website Access** | Navigate to `http://<EC2_PUBLIC_IP>/` in web browser. | Registration portal loads with clean white layout, blue accents, and all 6 input fields. |
| **2. Field Presence** | Inspect form inputs. | All 6 fields (Roll No, Name, Course, Address, Email, Year) are present and marked required (`*`). |
| **3. Client Validation** | Submit form with an invalid email (e.g. `bademail`) or empty field. | Form stops submission, outlines the invalid field in red, and presents clear inline error text. |
| **4. Valid Registration** | Fill in valid details and click "Register Student". | Loading spinner appears. Page redirects to `/register` rendering the confirmation page with green checkmark, student summary, DynamoDB item status, and SNS Message ID. |
| **5. Duplicate Roll Number Rejection** | Submit the registration form again with the exact same University Roll Number. | DynamoDB conditional check rejects the write. Application displays the duplicate error page (HTTP 409) explaining that the roll number already exists. |
| **6. DynamoDB Item Verification** | Run `scripts/verify_aws_resources.sh` or inspect DynamoDB console. | Student record is visible with `roll_no`, `name`, `course`, `address`, `email`, `year`, and ISO 8601 UTC `registered_at`. |
| **7. SNS Email Delivery** | Check the subscriber email inbox. | Email received with Subject: `Student Registration Successful - <ROLL_NO>` containing roll number, student name, course name, and `SUCCESSFUL` status. |
| **8. Persistence Across Reboots** | In AWS Console, reboot the EC2 instance (`Actions -> Instance state -> Reboot`). | Wait 45 seconds and reload `http://<EC2_PUBLIC_IP>/health`. Service resumes automatically via systemd. |

---

## 11. Application Logs & Troubleshooting

Inspect service and system logs on your EC2 instance with the following commands:

* **Inspect live Gunicorn application logs**:
  ```bash
  sudo journalctl -u student-registration.service -f
  ```

* **Inspect Gunicorn error log file**:
  ```bash
  tail -n 50 /var/log/student-registration/error.log
  ```

* **Inspect Nginx access & error logs**:
  ```bash
  tail -n 50 /var/log/nginx/error.log
  tail -n 50 /var/log/nginx/access.log
  ```

### Common Issues & Solutions:
1. **Error: `AccessDeniedException` or `UnrecognizedClientException`**:
   * *Cause*: EC2 instance does not have the IAM instance profile attached.
   * *Fix*: In EC2 Console -> Select instance -> **Actions** -> **Security** -> **Modify IAM role** -> Attach **`LabRole`**.
2. **Error: `ResourceNotFoundException: Cannot do operations on a non-existent table`**:
   * *Cause*: DynamoDB table name mismatch or created in a different AWS region.
   * *Fix*: Verify `DYNAMODB_TABLE` in `/etc/student-registration.env` exactly matches the table name in the AWS DynamoDB Console under `us-east-1`.
3. **SNS Message Not Received**:
   * *Cause*: Email subscription was not confirmed, or email went to Spam folder.
   * *Fix*: Verify Amazon SNS -> Subscriptions -> Ensure status is `Confirmed` (not `PendingConfirmation`). Check Spam folder.
4. **Website Unreachable on Port 80**:
   * *Cause*: EC2 Security Group inbound rule for port 80 is missing, or Nginx is stopped.
   * *Fix*: Add Inbound rule for HTTP (Port 80) from `0.0.0.0/0` in the security group. Run `sudo systemctl status nginx`.

---

## 12. Submission Evidence & Screenshot Checklist

Your assignment requires capturing 9 specific screenshots. Use this guide to locate each screen in the AWS Console:

| # | Required Screenshot | AWS Console Navigation Path | Key Evidence to Show in Screenshot |
|---|---|---|---|
| **1** | **Student Registration Form** | Web Browser: `http://<EC2_PUBLIC_IP>/` | The active web form displaying all 6 fields, clear labels, and subtle blue accent styling. |
| **2** | **Successful Registration Page** | Web Browser: `http://<EC2_PUBLIC_IP>/register` | The confirmation summary card showing student details, DynamoDB confirmed item, and the **SNS Message ID**. |
| **3** | **Confirmed SNS Email Subscription** | Email Client (Gmail/Outlook) | The browser window displaying *"Subscription confirmed!"* after clicking the verification link in the AWS confirmation email. |
| **4** | **SNS Topic and Subscription** | AWS Console: **Amazon SNS** -> **Topics** -> `StudentRegistration-<ROLL_NO>` | Topic ARN, Topic Name, and the Subscriptions tab showing Protocol: `email`, Endpoint: your email, and Status: **`Confirmed`**. |
| **5** | **DynamoDB Table Configuration** | AWS Console: **Amazon DynamoDB** -> **Tables** -> `Students-<ROLL_NO>` | Table name, Partition key (`roll_no`), Table status (`Active`), and Capacity mode (`On-demand`). |
| **6** | **DynamoDB Item Showing Saved Record** | AWS Console: **Amazon DynamoDB** -> **Explore items** -> `Students-<ROLL_NO>` | The items table showing the saved record with attributes: `roll_no`, `name`, `course`, `address`, `email`, `year`, `registered_at`. |
| **7** | **EC2 Instance Running** | AWS Console: **Amazon EC2** -> **Instances** | Instance Name (`StudentApp-<ROLL_NO>`), Instance state (`Running`), Public IPv4 address, and IAM role (`LabRole`). |
| **8** | **Security Group Inbound Rules** | AWS Console: **Amazon EC2** -> **Security Groups** -> `StudentApp-<ROLL_NO>-sg` | Inbound rules table showing Port 80 open to `0.0.0.0/0` and Port 22 restricted to your IP address. |
| **9** | **Actual Email Notification Received** | Email Client (Inbox) | The email message received from AWS Notifications displaying Subject `Student Registration Successful - <ROLL_NO>`, Roll Number, Student Name, Course, and `Registration Status: SUCCESSFUL`. |

---

## 13. Resource Cleanup Instructions

To avoid draining your **AWS Academy Learner Lab** credits after capturing all assignment screenshots, clean up the resources in this order:

1. **Terminate the Amazon EC2 Instance**:
   * Navigate to **EC2** -> **Instances**.
   * Select `StudentApp-<MY_UNIVERSITY_ROLL_NUMBER>`.
   * Click **Instance state** -> **Terminate instance**.
2. **Delete the Amazon DynamoDB Table**:
   * Navigate to **DynamoDB** -> **Tables**.
   * Select `Students-<MY_UNIVERSITY_ROLL_NUMBER>`.
   * Click **Delete** and confirm.
3. **Delete the Amazon SNS Topic**:
   * Navigate to **Amazon SNS** -> **Topics**.
   * Select `StudentRegistration-<MY_UNIVERSITY_ROLL_NUMBER>`.
   * Click **Delete**.
4. **Delete the Security Group**:
   * Once the EC2 instance is fully terminated, navigate to **EC2** -> **Security Groups**.
   * Select `StudentApp-<MY_UNIVERSITY_ROLL_NUMBER>-sg`.
   * Click **Actions** -> **Delete security groups**.

---

## 14. License & Academic Integrity

This project is created strictly for academic demonstration in the AWS Academy Learner Lab. All code is original and complies with AWS Academy practical assignment guidelines.
# student-registration-aws
