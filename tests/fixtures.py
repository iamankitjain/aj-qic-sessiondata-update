"""
Test fixtures and mock data for Amazon Connect Q Connect Session Data Updater tests.

Author: Ankit Jain
Version: 1.0.0
"""

from typing import Dict, Any


class TestFixtures:
    """Test fixtures for Lambda function testing."""

    @staticmethod
    def valid_connect_event() -> Dict[str, Any]:
        """Generate a valid Amazon Connect Lambda event."""
        return {
            'Details': {
                'ContactData': {
                    'ContactId': '12345678-1234-1234-1234-123456789012',
                    'CustomerEndpoint': {
                        'Address': '+15551234567',
                        'Type': 'TELEPHONE_NUMBER'
                    },
                    'SystemEndpoint': {
                        'Address': '+15559876543',
                        'Type': 'TELEPHONE_NUMBER'
                    },
                    'InitialContactId': '12345678-1234-1234-1234-123456789012',
                    'PreviousContactId': None,
                    'Channel': 'VOICE',
                    'InstanceARN': 'arn:aws:connect:us-east-1:123456789012:instance/test-instance-id'
                },
                'Parameters': {
                    'AI_ASSISTANT_ID': 'test-assistant-id-12345',
                    'CONNECT_INSTANCE_ID': 'test-instance-id',
                    'customer_intent': 'billing_inquiry',
                    'customer_tier': 'premium',
                    'product_category': 'mobile_service',
                    'issue_priority': 'high',
                    'customer_sentiment': 'frustrated',
                    'previous_interaction_count': '3',
                    'account_type': 'business',
                    'region': 'us-east-1'
                }
            }
        }

    @staticmethod
    def minimal_connect_event() -> Dict[str, Any]:
        """Generate a minimal valid Amazon Connect Lambda event."""
        return {
            'Details': {
                'ContactData': {
                    'ContactId': '12345678-1234-1234-1234-123456789012'
                },
                'Parameters': {
                    'AI_ASSISTANT_ID': 'test-assistant-id-12345'
                }
            }
        }

    @staticmethod
    def system_params_only_event() -> Dict[str, Any]:
        """Generate event with only system parameters."""
        return {
            'Details': {
                'ContactData': {
                    'ContactId': '12345678-1234-1234-1234-123456789012'
                },
                'Parameters': {
                    'AI_ASSISTANT_ID': 'test-assistant-id-12345',
                    'CONNECT_INSTANCE_ID': 'test-instance-id'
                }
            }
        }

    @staticmethod
    def invalid_event_no_contact_id() -> Dict[str, Any]:
        """Generate invalid event without ContactId."""
        return {
            'Details': {
                'ContactData': {},
                'Parameters': {
                    'AI_ASSISTANT_ID': 'test-assistant-id-12345',
                    'customer_intent': 'support'
                }
            }
        }

    @staticmethod
    def invalid_event_no_details() -> Dict[str, Any]:
        """Generate invalid event without Details."""
        return {
            'SomeOtherField': 'value'
        }

    @staticmethod
    def connect_describe_contact_response() -> Dict[str, Any]:
        """Generate a valid Connect DescribeContact API response."""
        return {
            'Contact': {
                'Id': '12345678-1234-1234-1234-123456789012',
                'InitialContactId': '12345678-1234-1234-1234-123456789012',
                'PreviousContactId': None,
                'InitiationMethod': 'INBOUND',
                'Channel': 'VOICE',
                'QueueInfo': {
                    'Id': 'queue-12345',
                    'Name': 'CustomerSupport'
                },
                'AgentInfo': {
                    'Id': 'agent-12345',
                    'ConnectedToAgentTimestamp': '2024-01-15T10:30:00.000Z'
                },
                'InitiationTimestamp': '2024-01-15T10:25:00.000Z',
                'DisconnectTimestamp': None,
                'LastUpdateTimestamp': '2024-01-15T10:30:00.000Z',
                'ScheduledTimestamp': None,
                'WisdomInfo': {
                    'SessionArn': 'arn:aws:qconnect:us-east-1:123456789012:session/test-session-arn-12345'
                }
            }
        }

    @staticmethod
    def connect_describe_contact_no_wisdom() -> Dict[str, Any]:
        """Generate Connect DescribeContact response without WisdomInfo."""
        response = TestFixtures.connect_describe_contact_response()
        del response['Contact']['WisdomInfo']
        return response

    @staticmethod
    def qconnect_update_session_response() -> Dict[str, Any]:
        """Generate a valid Q Connect UpdateSessionData API response."""
        return {
            'ResponseMetadata': {
                'RequestId': 'abcd1234-5678-90ef-ghij-klmnopqrstuv',
                'HTTPStatusCode': 200,
                'HTTPHeaders': {
                    'content-type': 'application/x-amz-json-1.1',
                    'date': 'Mon, 15 Jan 2024 10:30:00 GMT',
                    'x-amzn-requestid': 'abcd1234-5678-90ef-ghij-klmnopqrstuv'
                },
                'RetryAttempts': 0
            }
        }

    @staticmethod
    def expected_session_data() -> list:
        """Generate expected session data from valid_connect_event."""
        return [
            {'key': 'customer_intent', 'value': {'stringValue': 'billing_inquiry'}},
            {'key': 'customer_tier', 'value': {'stringValue': 'premium'}},
            {'key': 'product_category', 'value': {'stringValue': 'mobile_service'}},
            {'key': 'issue_priority', 'value': {'stringValue': 'high'}},
            {'key': 'customer_sentiment', 'value': {'stringValue': 'frustrated'}},
            {'key': 'previous_interaction_count', 'value': {'stringValue': '3'}},
            {'key': 'account_type', 'value': {'stringValue': 'business'}},
            {'key': 'region', 'value': {'stringValue': 'us-east-1'}}
        ]

    @staticmethod
    def client_error_response(error_code: str, message: str) -> Dict[str, Any]:
        """Generate a boto3 ClientError response."""
        return {
            'Error': {
                'Code': error_code,
                'Message': message,
                'Type': 'Sender'
            },
            'ResponseMetadata': {
                'RequestId': 'abcd1234-5678-90ef-ghij-klmnopqrstuv',
                'HTTPStatusCode': 400,
                'HTTPHeaders': {
                    'content-type': 'application/x-amz-json-1.1',
                    'date': 'Mon, 15 Jan 2024 10:30:00 GMT'
                }
            }
        }


class TestConstants:
    """Test constants and configuration values."""
    
    VALID_CONTACT_ID = '12345678-1234-1234-1234-123456789012'
    VALID_INSTANCE_ID = 'test-instance-id'
    VALID_ASSISTANT_ID = 'test-assistant-id-12345'
    VALID_SESSION_ARN = 'arn:aws:qconnect:us-east-1:123456789012:session/test-session-arn-12345'
    
    # Environment variable configurations
    ENV_DEBUG_ENABLED = {'DEBUG_LOG': 'true'}
    ENV_DEBUG_DISABLED = {'DEBUG_LOG': 'false'}
    ENV_WITH_INSTANCE_ID = {'CONNECT_INSTANCE_ID': VALID_INSTANCE_ID}
    ENV_COMPLETE = {
        'DEBUG_LOG': 'true',
        'CONNECT_INSTANCE_ID': VALID_INSTANCE_ID,
        'AWS_REGION': 'us-east-1'
    }


class MockResponses:
    """Mock response builders for AWS services."""

    @staticmethod
    def success_lambda_response(message: str) -> Dict[str, Any]:
        """Generate a successful Lambda response."""
        return {
            'statusCode': 200,
            'body': f'{{"message": "{message}"}}'
        }

    @staticmethod
    def error_lambda_response(error_message: str) -> Dict[str, Any]:
        """Generate an error Lambda response."""
        return {
            'statusCode': 500,
            'body': f'{{"error": "{error_message}"}}'
        }