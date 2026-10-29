"""
Unit and Integration Test Suite for Student Registration System
Verifies Input Validation, DynamoDB Conditional Writes, Duplicate Rejections,
and SNS Publication Flow using Mocks.
"""

import unittest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

# Import Flask app and helper functions
from app import app, validate_student_data, EMAIL_REGEX, VALID_YEARS


class TestStudentRegistrationValidation(unittest.TestCase):
    """Test frontend/backend validation rules for the 6 required student fields."""

    def test_valid_student_data(self):
        """All 6 fields valid should pass validation."""
        data = {
            "roll_no": "21BCE1042",
            "name": "Jane Doe",
            "course": "B.Tech Computer Science",
            "address": "42 Campus Avenue, Building B, Room 102",
            "email": "jane.doe@university.edu",
            "year": "Year 2",
        }
        is_valid, error_msg, cleaned = validate_student_data(data)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        self.assertEqual(cleaned["roll_no"], "21BCE1042")
        self.assertEqual(cleaned["email"], "jane.doe@university.edu")

    def test_missing_field_rejection(self):
        """Omitting any required field must fail validation."""
        required_fields = ["roll_no", "name", "course", "address", "email", "year"]
        base_data = {
            "roll_no": "21BCE1042",
            "name": "Jane Doe",
            "course": "B.Tech Computer Science",
            "address": "42 Campus Avenue, Building B, Room 102",
            "email": "jane.doe@university.edu",
            "year": "Year 2",
        }

        for field in required_fields:
            test_data = base_data.copy()
            del test_data[field]
            is_valid, error_msg, _ = validate_student_data(test_data)
            self.assertFalse(is_valid, f"Validation should fail when '{field}' is missing.")
            self.assertIn("required", error_msg.lower())

    def test_empty_whitespace_rejection(self):
        """Whitespace-only fields must be rejected."""
        data = {
            "roll_no": "   ",
            "name": "Jane Doe",
            "course": "B.Tech CS",
            "address": "Campus Address",
            "email": "jane@university.edu",
            "year": "Year 1",
        }
        is_valid, error_msg, _ = validate_student_data(data)
        self.assertFalse(is_valid)
        self.assertIn("required and cannot be empty", error_msg)

    def test_invalid_email_format(self):
        """Malformed emails must fail validation."""
        invalid_emails = [
            "plainaddress",
            "@missingusername.com",
            "username@.com",
            "username@domain",
            "user name@domain.com",
        ]
        for bad_email in invalid_emails:
            data = {
                "roll_no": "21BCE1042",
                "name": "Jane Doe",
                "course": "B.Tech CS",
                "address": "Campus Address",
                "email": bad_email,
                "year": "Year 1",
            }
            is_valid, error_msg, _ = validate_student_data(data)
            self.assertFalse(is_valid, f"Email '{bad_email}' should be rejected.")
            self.assertIn("not valid", error_msg)

    def test_year_of_study_normalization(self):
        """Years 1, 2, 3, 4 should normalize or validate correctly."""
        for y in ["1", "2", "3", "4", "Year 1", "Year 2", "Year 3", "Year 4"]:
            data = {
                "roll_no": "21BCE1042",
                "name": "Jane Doe",
                "course": "B.Tech CS",
                "address": "Campus Address",
                "email": "jane@university.edu",
                "year": y,
            }
            is_valid, _, cleaned = validate_student_data(data)
            self.assertTrue(is_valid)
            self.assertTrue(cleaned["year"].startswith("Year "))

        # Invalid year
        data["year"] = "Year 5"
        is_valid, error_msg, _ = validate_student_data(data)
        self.assertFalse(is_valid)


class TestFlaskRoutesAndAWSIntegration(unittest.TestCase):
    """Test Flask routes, DynamoDB conditional operations, and SNS publishing."""

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_get_index_contains_all_six_fields(self):
        """GET / must render the registration form with all 6 required fields."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        
        # Verify 6 fields
        self.assertIn('name="roll_no"', html)
        self.assertIn('name="name"', html)
        self.assertIn('name="course"', html)
        self.assertIn('name="year"', html)
        self.assertIn('name="email"', html)
        self.assertIn('name="address"', html)
        
        # Verify Year 1-4 options
        self.assertIn('value="Year 1"', html)
        self.assertIn('value="Year 2"', html)
        self.assertIn('value="Year 3"', html)
        self.assertIn('value="Year 4"', html)

    def test_health_endpoint(self):
        """GET /health must return status healthy with runtime metadata."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("aws_region", data)
        self.assertIn("dynamodb_table", data)

    @patch("app.get_sns_client")
    @patch("app.get_dynamodb_resource")
    def test_successful_registration_flow(self, mock_get_dynamodb, mock_get_sns):
        """
        Verify complete happy path:
        1. DynamoDB put_item called with condition attribute_not_exists(roll_no).
        2. SNS publish called ONLY after DynamoDB succeeds.
        3. Returns HTTP 200 with SNS Message ID.
        """
        # Mock DynamoDB
        mock_dynamo = MagicMock()
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_get_dynamodb.return_value = mock_dynamo

        # Mock SNS
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {"MessageId": "mock-sns-msg-12345-abcde"}
        mock_get_sns.return_value = mock_sns

        payload = {
            "roll_no": "21BCE1042",
            "name": "Alice Smith",
            "course": "B.Sc Computer Science",
            "address": "123 Academic Way, North Campus",
            "email": "alice.smith@university.edu",
            "year": "Year 3",
        }

        with patch("app.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:StudentRegistration-21BCE1042"):
            response = self.client.post("/register", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["dynamodb"]["status"], "SAVED")
        self.assertEqual(data["sns"]["message_id"], "mock-sns-msg-12345-abcde")
        self.assertTrue(data["sns"]["published"])

        # Check DynamoDB was called with ConditionExpression
        mock_table.put_item.assert_called_once()
        _, kwargs = mock_table.put_item.call_args
        self.assertEqual(kwargs.get("ConditionExpression"), "attribute_not_exists(roll_no)")
        self.assertEqual(kwargs.get("Item")["roll_no"], "21BCE1042")
        self.assertIn("registered_at", kwargs.get("Item"))

        # Check SNS publish was called
        mock_sns.publish.assert_called_once()
        _, sns_kwargs = mock_sns.publish.call_args
        self.assertIn("21BCE1042", sns_kwargs.get("Subject"))
        self.assertIn("Alice Smith", sns_kwargs.get("Message"))
        self.assertIn("B.Sc Computer Science", sns_kwargs.get("Message"))
        self.assertIn("SUCCESSFUL", sns_kwargs.get("Message"))

    @patch("app.get_sns_client")
    @patch("app.get_dynamodb_resource")
    def test_duplicate_roll_number_rejection(self, mock_get_dynamodb, mock_get_sns):
        """
        Verify duplicate roll numbers are rejected by DynamoDB conditional check:
        1. DynamoDB raises ConditionalCheckFailedException.
        2. Application catches it and returns HTTP 409 Conflict.
        3. SNS publish is NOT called.
        """
        mock_dynamo = MagicMock()
        mock_table = MagicMock()
        # Simulate AWS DynamoDB ConditionalCheckFailedException
        error_response = {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "The conditional request failed"
            }
        }
        mock_table.put_item.side_effect = ClientError(error_response, "PutItem")
        mock_dynamo.Table.return_value = mock_table
        mock_get_dynamodb.return_value = mock_dynamo

        mock_sns = MagicMock()
        mock_get_sns.return_value = mock_sns

        payload = {
            "roll_no": "DUPLICATE123",
            "name": "Bob Jones",
            "course": "Mechanical Engineering",
            "address": "456 Tech Hall",
            "email": "bob@university.edu",
            "year": "Year 2",
        }

        response = self.client.post("/register", json=payload)
        self.assertEqual(response.status_code, 409)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error_type"], "DuplicateRollNumber")
        self.assertIn("already registered", data["message"])

        # Crucial check: SNS publish MUST NOT have been called!
        mock_sns.publish.assert_not_called()

    @patch("app.get_sns_client")
    @patch("app.get_dynamodb_resource")
    def test_sns_failure_does_not_mask_dynamodb_success(self, mock_get_dynamodb, mock_get_sns):
        """
        Verify requirement:
        If DynamoDB succeeds, but SNS publishing fails (e.g. topic permissions or not found),
        do NOT say database insertion failed. Report that the student record was saved
        and provide clear SNS warning details.
        """
        mock_dynamo = MagicMock()
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_get_dynamodb.return_value = mock_dynamo

        # Simulate SNS error
        mock_sns = MagicMock()
        sns_error = {
            "Error": {
                "Code": "AuthorizationErrorException",
                "Message": "User is not authorized to perform: SNS:Publish"
            }
        }
        mock_sns.publish.side_effect = ClientError(sns_error, "Publish")
        mock_get_sns.return_value = mock_sns

        payload = {
            "roll_no": "SAFE2024",
            "name": "Charlie Brown",
            "course": "Information Systems",
            "address": "789 Campus Drive",
            "email": "charlie@university.edu",
            "year": "Year 4",
        }

        with patch("app.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:StudentRegistration-SAFE2024"):
            response = self.client.post("/register", json=payload)

        # Still returns 200 because student profile is saved
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["dynamodb"]["status"], "SAVED")
        self.assertFalse(data["sns"]["published"])
        self.assertIsNotNone(data["sns"]["warning"])
        self.assertIn("AuthorizationErrorException", data["sns"]["warning"])
        self.assertIn("successfully saved in DynamoDB", data["sns"]["warning"])

    def test_html_form_rendering_on_success(self):
        """Verify HTML form post renders templates/success.html."""
        with patch("app.get_dynamodb_resource") as mock_dynamo, \
             patch("app.get_sns_client") as mock_sns:
            mock_table = MagicMock()
            mock_dynamo.return_value.Table.return_value = mock_table
            mock_sns.return_value.publish.return_value = {"MessageId": "html-msg-999"}

            form_data = {
                "roll_no": "HTML2024",
                "name": "Diana Prince",
                "course": "Cybersecurity",
                "address": "500 Shield Hall",
                "email": "diana@university.edu",
                "year": "Year 1",
            }

            with patch("app.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:StudentRegistration-HTML2024"):
                response = self.client.post("/register", data=form_data)

            self.assertEqual(response.status_code, 200)
            html = response.data.decode("utf-8")
            self.assertIn("Registration Successfully Processed", html)
            self.assertIn("HTML2024", html)
            self.assertIn("Diana Prince", html)
            self.assertIn("html-msg-999", html)


if __name__ == "__main__":
    unittest.main()
