"""
Tests for test fixtures and mock data.

Author: Ankit Jain
Version: 1.0.0
"""

import unittest
from typing import Dict, Any

from tests.fixtures import TestFixtures, TestConstants, MockResponses


class TestTestFixtures(unittest.TestCase):
    """Test the test fixtures themselves."""

    def test_valid_connect_event_structure(self):
        """Test that valid_connect_event returns proper structure."""
        event = TestFixtures.valid_connect_event()
        
        # Verify top-level structure
        self.assertIn('Details', event)
        self.assertIn('ContactData', event['Details'])
        self.assertIn('Parameters', event['Details'])
        
        # Verify ContactData
        contact_data = event['Details']['ContactData']
        self.assertIn('ContactId', contact_data)
        
        # Verify Parameters contains both system and user parameters
        parameters = event['Details']['Parameters']
        self.assertIn('AI_ASSISTANT_ID', parameters)
        self.assertIn('customer_intent', parameters)

    def test_minimal_connect_event_structure(self):
        """Test that minimal_connect_event has required fields only."""
        event = TestFixtures.minimal_connect_event()
        
        self.assertIn('Details', event)
        self.assertIn('ContactData', event['Details'])
        self.assertIn('ContactId', event['Details']['ContactData'])
        self.assertIn('Parameters', event['Details'])
        self.assertIn('AI_ASSISTANT_ID', event['Details']['Parameters'])

    def test_system_params_only_event(self):
        """Test event with only system parameters."""
        event = TestFixtures.system_params_only_event()
        
        parameters = event['Details']['Parameters']
        self.assertEqual(len(parameters), 2)
        self.assertIn('AI_ASSISTANT_ID', parameters)
        self.assertIn('CONNECT_INSTANCE_ID', parameters)

    def test_invalid_events(self):
        """Test invalid event fixtures."""
        # No contact ID
        event_no_contact = TestFixtures.invalid_event_no_contact_id()
        self.assertNotIn('ContactId', event_no_contact['Details']['ContactData'])
        
        # No details
        event_no_details = TestFixtures.invalid_event_no_details()
        self.assertNotIn('Details', event_no_details)

    def test_connect_api_responses(self):
        """Test Connect API response fixtures."""
        # Valid response
        response = TestFixtures.connect_describe_contact_response()
        self.assertIn('Contact', response)
        self.assertIn('WisdomInfo', response['Contact'])
        self.assertIn('SessionArn', response['Contact']['WisdomInfo'])
        
        # No wisdom response
        no_wisdom = TestFixtures.connect_describe_contact_no_wisdom()
        self.assertIn('Contact', no_wisdom)
        self.assertNotIn('WisdomInfo', no_wisdom['Contact'])

    def test_qconnect_api_response(self):
        """Test Q Connect API response fixture."""
        response = TestFixtures.qconnect_update_session_response()
        
        self.assertIn('ResponseMetadata', response)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

    def test_expected_session_data(self):
        """Test expected session data fixture."""
        session_data = TestFixtures.expected_session_data()
        
        # Should be a list
        self.assertIsInstance(session_data, list)
        self.assertGreater(len(session_data), 0)
        
        # Each entry should have proper structure
        for entry in session_data:
            self.assertIn('key', entry)
            self.assertIn('value', entry)
            self.assertIn('stringValue', entry['value'])

    def test_client_error_response(self):
        """Test ClientError response fixture."""
        error_response = TestFixtures.client_error_response('ValidationException', 'Test error')
        
        self.assertIn('Error', error_response)
        self.assertEqual(error_response['Error']['Code'], 'ValidationException')
        self.assertEqual(error_response['Error']['Message'], 'Test error')


class TestTestConstants(unittest.TestCase):
    """Test the test constants."""

    def test_constants_exist(self):
        """Test that all expected constants exist."""
        self.assertIsNotNone(TestConstants.VALID_CONTACT_ID)
        self.assertIsNotNone(TestConstants.VALID_INSTANCE_ID)
        self.assertIsNotNone(TestConstants.VALID_ASSISTANT_ID)
        self.assertIsNotNone(TestConstants.VALID_SESSION_ARN)

    def test_environment_configurations(self):
        """Test environment configuration dictionaries."""
        # Debug enabled
        self.assertIn('DEBUG_LOG', TestConstants.ENV_DEBUG_ENABLED)
        self.assertEqual(TestConstants.ENV_DEBUG_ENABLED['DEBUG_LOG'], 'true')
        
        # Debug disabled
        self.assertIn('DEBUG_LOG', TestConstants.ENV_DEBUG_DISABLED)
        self.assertEqual(TestConstants.ENV_DEBUG_DISABLED['DEBUG_LOG'], 'false')
        
        # With instance ID
        self.assertIn('CONNECT_INSTANCE_ID', TestConstants.ENV_WITH_INSTANCE_ID)
        
        # Complete environment
        self.assertIn('DEBUG_LOG', TestConstants.ENV_COMPLETE)
        self.assertIn('CONNECT_INSTANCE_ID', TestConstants.ENV_COMPLETE)
        self.assertIn('AWS_REGION', TestConstants.ENV_COMPLETE)


class TestMockResponses(unittest.TestCase):
    """Test the mock response builders."""

    def test_success_lambda_response(self):
        """Test successful Lambda response builder."""
        response = MockResponses.success_lambda_response("Test success")
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('message', response['body'])
        self.assertIn('Test success', response['body'])

    def test_error_lambda_response(self):
        """Test error Lambda response builder."""
        response = MockResponses.error_lambda_response("Test error")
        
        self.assertEqual(response['statusCode'], 500)
        self.assertIn('error', response['body'])
        self.assertIn('Test error', response['body'])


if __name__ == '__main__':
    unittest.main()