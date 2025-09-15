"""
Unit tests for Amazon Connect Q Connect Session Data Updater Lambda function.

Author: Ankit Jain
Version: 1.0.0
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, Mock
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError
import pytest

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import index
    from index import (
        ContextKeys,
        debug_log,
        get_qic_session_arn,
        get_parameter_from_event_or_env,
        get_session_data,
        update_qic_session,
        lambda_handler
    )
except ImportError as e:
    pytest.skip(f"Could not import index module: {e}", allow_module_level=True)


class TestContextKeys(unittest.TestCase):
    """Test ContextKeys class constants."""

    def test_context_keys_constants(self):
        """Test that ContextKeys contains expected constants."""
        self.assertEqual(ContextKeys.AI_ASSISTANT_ID, "AI_ASSISTANT_ID")
        self.assertEqual(ContextKeys.CONNECT_INSTANCE_ID, "CONNECT_INSTANCE_ID")


class TestDebugLog(unittest.TestCase):
    """Test debug_log function."""

    @patch.dict(os.environ, {'DEBUG_LOG': 'true'})
    @patch('index.logger')
    def test_debug_log_enabled(self, mock_logger):
        """Test debug_log when DEBUG_LOG is enabled."""
        debug_log("Test message", {"key": "value"})
        
        # Verify logger.info was called
        mock_logger.info.assert_called_once()
        
        # Check the logged message structure
        logged_message = mock_logger.info.call_args[0][0]
        parsed_log = json.loads(logged_message)
        
        self.assertEqual(parsed_log["level"], "DEBUG")
        self.assertEqual(parsed_log["message"], "Test message")
        self.assertEqual(parsed_log["params"], {"key": "value"})

    @patch.dict(os.environ, {'DEBUG_LOG': 'false'})
    @patch('index.logger')
    def test_debug_log_disabled(self, mock_logger):
        """Test debug_log when DEBUG_LOG is disabled."""
        debug_log("Test message", {"key": "value"})
        
        # Verify logger.info was not called
        mock_logger.info.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch('index.logger')
    def test_debug_log_no_env_var(self, mock_logger):
        """Test debug_log when DEBUG_LOG environment variable is not set."""
        debug_log("Test message")
        
        # Verify logger.info was not called
        mock_logger.info.assert_not_called()


class TestGetQicSessionArn(unittest.TestCase):
    """Test get_qic_session_arn function."""

    @patch('index.connect_client')
    @patch('index.debug_log')
    def test_get_qic_session_arn_success(self, mock_debug_log, mock_connect_client):
        """Test successful retrieval of Q Connect session ARN."""
        # Mock the API response
        mock_response = {
            'Contact': {
                'WisdomInfo': {
                    'SessionArn': 'arn:aws:qconnect:us-east-1:123456789012:session/test-session-arn'
                }
            }
        }
        mock_connect_client.describe_contact.return_value = mock_response

        result = get_qic_session_arn("test-contact-id", "test-instance-id")

        # Verify the result
        self.assertEqual(result, 'arn:aws:qconnect:us-east-1:123456789012:session/test-session-arn')
        
        # Verify API was called correctly
        mock_connect_client.describe_contact.assert_called_once_with(
            ContactId="test-contact-id",
            InstanceId="test-instance-id"
        )
        
        # Verify debug logs were called
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('index.connect_client')
    @patch('index.debug_log')
    def test_get_qic_session_arn_no_session(self, mock_debug_log, mock_connect_client):
        """Test when no Q Connect session is found."""
        # Mock the API response without session
        mock_response = {'Contact': {}}
        mock_connect_client.describe_contact.return_value = mock_response

        with self.assertRaises(Exception) as context:
            get_qic_session_arn("test-contact-id", "test-instance-id")

        self.assertIn("No Q Connect session found for contact test-contact-id", str(context.exception))

    @patch('index.connect_client')
    @patch('index.logger')
    def test_get_qic_session_arn_client_error(self, mock_logger, mock_connect_client):
        """Test handling of ClientError from AWS API."""
        # Mock ClientError
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Contact not found'
            }
        }
        mock_connect_client.describe_contact.side_effect = ClientError(error_response, 'DescribeContact')

        with self.assertRaises(ClientError):
            get_qic_session_arn("test-contact-id", "test-instance-id")

        # Verify error was logged
        mock_logger.error.assert_called_once()


class TestGetParameterFromEventOrEnv(unittest.TestCase):
    """Test get_parameter_from_event_or_env function."""

    @patch('index.debug_log')
    def test_get_parameter_from_event(self, mock_debug_log):
        """Test getting parameter from event parameters."""
        event = {
            'Details': {
                'Parameters': {
                    'AI_ASSISTANT_ID': 'event-assistant-id'
                }
            }
        }

        result = get_parameter_from_event_or_env('AI_ASSISTANT_ID', event)

        self.assertEqual(result, 'event-assistant-id')
        mock_debug_log.assert_called_once()

    @patch.dict(os.environ, {'AI_ASSISTANT_ID': 'env-assistant-id'})
    @patch('index.debug_log')
    def test_get_parameter_from_env(self, mock_debug_log):
        """Test getting parameter from environment variables."""
        event = {'Details': {'Parameters': {}}}

        result = get_parameter_from_event_or_env('AI_ASSISTANT_ID', event)

        self.assertEqual(result, 'env-assistant-id')
        mock_debug_log.assert_called_once()

    def test_get_parameter_not_found(self):
        """Test when parameter is not found in either location."""
        event = {'Details': {'Parameters': {}}}

        with self.assertRaises(Exception) as context:
            get_parameter_from_event_or_env('MISSING_PARAM', event)

        self.assertIn("Required parameter 'MISSING_PARAM' not found", str(context.exception))


class TestGetSessionData(unittest.TestCase):
    """Test get_session_data function."""

    @patch('index.debug_log')
    def test_get_session_data_success(self, mock_debug_log):
        """Test successful conversion of parameters to session data."""
        event = {
            'Details': {
                'Parameters': {
                    'AI_ASSISTANT_ID': 'assistant-id',  # Should be filtered out
                    'CONNECT_INSTANCE_ID': 'instance-id',  # Should be filtered out
                    'customer_intent': 'purchase',
                    'customer_tier': 'gold',
                    'product_id': '12345'
                }
            }
        }

        result = get_session_data(event)

        # Should have 3 session data entries (excluding system parameters)
        self.assertEqual(len(result), 3)
        
        # Verify structure of session data entries
        expected_keys = {'customer_intent', 'customer_tier', 'product_id'}
        actual_keys = {entry['key'] for entry in result}
        self.assertEqual(actual_keys, expected_keys)

        # Verify data structure
        for entry in result:
            self.assertIn('key', entry)
            self.assertIn('value', entry)
            self.assertIn('stringValue', entry['value'])

    @patch('index.debug_log')
    def test_get_session_data_no_parameters(self, mock_debug_log):
        """Test when no parameters are found in event."""
        event = {'Details': {}}

        result = get_session_data(event)

        self.assertEqual(len(result), 0)
        mock_debug_log.assert_called_once_with("No parameters found in Connect event")

    @patch('index.debug_log')
    def test_get_session_data_only_system_params(self, mock_debug_log):
        """Test when only system parameters are present."""
        event = {
            'Details': {
                'Parameters': {
                    'AI_ASSISTANT_ID': 'assistant-id',
                    'CONNECT_INSTANCE_ID': 'instance-id'
                }
            }
        }

        result = get_session_data(event)

        self.assertEqual(len(result), 0)


class TestUpdateQicSession(unittest.TestCase):
    """Test update_qic_session function."""

    @patch('index.qconnect_client')
    @patch('index.debug_log')
    def test_update_qic_session_success(self, mock_debug_log, mock_qconnect_client):
        """Test successful Q Connect session update."""
        session_data = [
            {
                'key': 'customer_intent',
                'value': {'stringValue': 'purchase'}
            }
        ]
        
        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_qconnect_client.update_session_data.return_value = mock_response

        # Should not raise an exception
        update_qic_session("assistant-id", "session-arn", session_data)

        # Verify API was called correctly
        mock_qconnect_client.update_session_data.assert_called_once_with(
            assistantId="assistant-id",
            sessionId="session-arn",
            data=session_data
        )

        # Verify debug logs were called
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('index.qconnect_client')
    @patch('index.logger')
    def test_update_qic_session_client_error(self, mock_logger, mock_qconnect_client):
        """Test handling of ClientError from Q Connect API."""
        session_data = [{'key': 'test', 'value': {'stringValue': 'value'}}]
        
        error_response = {
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Invalid session data'
            }
        }
        mock_qconnect_client.update_session_data.side_effect = ClientError(error_response, 'UpdateSessionData')

        with self.assertRaises(ClientError):
            update_qic_session("assistant-id", "session-arn", session_data)

        # Verify error was logged
        mock_logger.error.assert_called_once()


class TestLambdaHandler(unittest.TestCase):
    """Test lambda_handler function."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_event = {
            'Details': {
                'ContactData': {
                    'ContactId': 'test-contact-id'
                },
                'Parameters': {
                    'AI_ASSISTANT_ID': 'test-assistant-id',
                    'customer_intent': 'purchase',
                    'product_id': '12345'
                }
            }
        }
        self.context = Mock()

    @patch.dict(os.environ, {'CONNECT_INSTANCE_ID': 'test-instance-id'})
    @patch('index.update_qic_session')
    @patch('index.get_qic_session_arn')
    @patch('index.debug_log')
    def test_lambda_handler_success(self, mock_debug_log, mock_get_session_arn, mock_update_session):
        """Test successful lambda execution."""
        mock_get_session_arn.return_value = 'test-session-arn'

        result = lambda_handler(self.valid_event, self.context)

        # Verify successful response
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('Successfully updated', body['message'])

        # Verify functions were called
        mock_get_session_arn.assert_called_once_with('test-contact-id', 'test-instance-id')
        mock_update_session.assert_called_once()

    def test_lambda_handler_missing_contact_id(self):
        """Test lambda handler with missing contact ID."""
        invalid_event = {'Details': {'ContactData': {}}}

        result = lambda_handler(invalid_event, self.context)

        # Verify error response
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertIn('ContactId not found in event', body['error'])

    @patch('index.debug_log')
    def test_lambda_handler_no_session_data(self, mock_debug_log):
        """Test lambda handler when no session data is available."""
        event_no_params = {
            'Details': {
                'ContactData': {'ContactId': 'test-contact-id'},
                'Parameters': {
                    'AI_ASSISTANT_ID': 'test-assistant-id'  # Only system parameters
                }
            }
        }

        with patch.dict(os.environ, {'CONNECT_INSTANCE_ID': 'test-instance-id'}):
            result = lambda_handler(event_no_params, self.context)

        # Verify successful response with no data to update
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['message'], 'No session data to update')

    @patch.dict(os.environ, {}, clear=True)
    def test_lambda_handler_missing_env_var(self):
        """Test lambda handler with missing environment variable."""
        result = lambda_handler(self.valid_event, self.context)

        # Verify error response
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertIn('CONNECT_INSTANCE_ID', body['error'])

    @patch.dict(os.environ, {'CONNECT_INSTANCE_ID': 'test-instance-id'})
    @patch('index.get_qic_session_arn')
    @patch('index.debug_log')
    def test_lambda_handler_exception_handling(self, mock_debug_log, mock_get_session_arn):
        """Test lambda handler exception handling."""
        mock_get_session_arn.side_effect = Exception("Test error")

        result = lambda_handler(self.valid_event, self.context)

        # Verify error response
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Test error')


class TestIntegration(unittest.TestCase):
    """Integration tests for the full workflow."""

    @patch.dict(os.environ, {'CONNECT_INSTANCE_ID': 'test-instance-id'})
    @patch('index.qconnect_client')
    @patch('index.connect_client')
    @patch('index.debug_log')
    def test_full_workflow_success(self, mock_debug_log, mock_connect_client, mock_qconnect_client):
        """Test the complete workflow from event to Q Connect update."""
        # Mock Connect API response
        mock_connect_response = {
            'Contact': {
                'WisdomInfo': {
                    'SessionArn': 'test-session-arn'
                }
            }
        }
        mock_connect_client.describe_contact.return_value = mock_connect_response

        # Mock Q Connect API response
        mock_qconnect_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_qconnect_client.update_session_data.return_value = mock_qconnect_response

        # Test event with multiple parameters
        event = {
            'Details': {
                'ContactData': {
                    'ContactId': 'integration-test-contact-id'
                },
                'Parameters': {
                    'AI_ASSISTANT_ID': 'integration-test-assistant-id',
                    'customer_intent': 'support',
                    'customer_tier': 'premium',
                    'issue_category': 'billing',
                    'priority': 'high'
                }
            }
        }

        result = lambda_handler(event, Mock())

        # Verify successful response
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('Successfully updated 4 session data entries', body['message'])

        # Verify Connect API was called
        mock_connect_client.describe_contact.assert_called_once_with(
            ContactId='integration-test-contact-id',
            InstanceId='test-instance-id'
        )

        # Verify Q Connect API was called with correct data
        mock_qconnect_client.update_session_data.assert_called_once()
        call_args = mock_qconnect_client.update_session_data.call_args
        
        self.assertEqual(call_args.kwargs['assistantId'], 'integration-test-assistant-id')
        self.assertEqual(call_args.kwargs['sessionId'], 'test-session-arn')
        self.assertEqual(len(call_args.kwargs['data']), 4)  # 4 non-system parameters


if __name__ == '__main__':
    unittest.main()