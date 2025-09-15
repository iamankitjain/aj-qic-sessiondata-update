"""
Amazon Connect Q Connect Session Data Updater

This Lambda function extracts key-value pairs from Amazon Connect contact flow parameters
and updates the associated Q Connect session with this data as session attributes.

Use case: Pass context data (like intent, customer info) from Connect to Q Connect AI agent.

Author: Ankit Jain
Version: 1.0.0
Last Updated: 2024

Expected Lambda Event Structure:
{
    "Details": {
        "ContactData": {
            "ContactId": "contact-id-here"
        },
        "Parameters": {
            "AI_ASSISTANT_ID": "assistant-id",
            "CONNECT_INSTANCE_ID": "instance-id",
            "customParam1": "value1",
            "customParam2": "value2"
        }
    }
}
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
qconnect_client = boto3.client('qconnect')
connect_client = boto3.client('connect', region_name=os.environ.get('AWS_REGION', 'us-east-1'))


class ContextKeys:
    """System parameter keys that should not be passed to Q Connect session data."""
    AI_ASSISTANT_ID = "AI_ASSISTANT_ID"
    CONNECT_INSTANCE_ID = "CONNECT_INSTANCE_ID"


def debug_log(message: str, data: Any = None) -> None:
    """Debug logging function that only logs when DEBUG_LOG is true."""
    if os.environ.get('DEBUG_LOG') == 'true':
        log_entry = {"level": "DEBUG", "message": message}
        if data is not None:
            log_entry["params"] = data
        logger.info(json.dumps(log_entry, default=str))


def get_qic_session_arn(contact_id: str, connect_instance_id: str) -> str:
    """
    Get the Q Connect session ARN from Amazon Connect contact details.

    Args:
        contact_id: The Amazon Connect contact ID
        connect_instance_id: The Amazon Connect instance ID

    Returns:
        The Q Connect session ARN

    Raises:
        Exception: If no Q Connect session is found for the contact
    """
    try:
        debug_log("Get QiC session request", {
            "ContactId": contact_id,
            "InstanceId": connect_instance_id
        })

        response = connect_client.describe_contact(
            ContactId=contact_id,
            InstanceId=connect_instance_id
        )

        debug_log("Get QiC session response", response)

        # Navigate through the response structure to find the session ARN
        session_arn = response.get('Contact', {}).get('WisdomInfo', {}).get('SessionArn')

        if not session_arn:
            raise Exception(f"No Q Connect session found for contact {contact_id}.")

        return session_arn

    except ClientError as e:
        logger.error(f"AWS API error retrieving contact: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error retrieving QiC session ARN: {str(e)}")
        raise


def get_parameter_from_event_or_env(context_key: str, connect_request: Dict[str, Any]) -> str:
    """
    Get parameter from Connect event parameters or environment variables.

    Args:
        context_key: The parameter key to search for
        connect_request: The Connect event request payload

    Returns:
        The parameter value

    Raises:
        Exception: If the parameter is not found in either location
    """
    # First, try to get from Connect event parameters
    value = connect_request.get('Details', {}).get('Parameters', {}).get(context_key)
    
    # If not found in event, try environment variables
    if not value:
        value = os.environ.get(context_key)

    if not value:
        raise Exception(f"Required parameter '{context_key}' not found in Connect event parameters or Lambda environment variables.")

    debug_log(f"Retrieved parameter {context_key}", {
        "source": "event" if connect_request.get('Details', {}).get('Parameters', {}).get(context_key) else "environment"
    })

    return value


def get_session_data(connect_request: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert Amazon Connect contact flow parameters to Q Connect session data format.

    Args:
        connect_request: The Connect event request payload

    Returns:
        List of session data entries in Q Connect format
    """
    parameters = connect_request.get('Details', {}).get('Parameters', {})

    if not parameters:
        debug_log("No parameters found in Connect event")
        return []

    session_data = []

    # Skip system parameters used for Lambda configuration
    system_keys = {ContextKeys.AI_ASSISTANT_ID, ContextKeys.CONNECT_INSTANCE_ID}

    for key, value in parameters.items():
        if key not in system_keys:
            # Convert value to string as required by Q Connect API
            string_value = str(value) if value is not None else ''

            session_data.append({
                'key': key,
                'value': {
                    'stringValue': string_value
                }
            })

            debug_log(f"Added parameter to session data: {key}", {
                "key": key,
                "valueLength": len(string_value)
            })

    debug_log(f"Converted {len(session_data)} parameters to session data format", {
        "totalParameters": len(parameters),
        "systemParameters": len(parameters) - len(session_data),
        "sessionDataCount": len(session_data)
    })

    return session_data


def update_qic_session(ai_assistant_id: str, qic_session_arn: str, session_data: List[Dict[str, Any]]) -> None:
    """
    Update Q Connect session with the provided session data.

    Args:
        ai_assistant_id: The Q Connect AI Assistant ID
        qic_session_arn: The Q Connect session ARN
        session_data: List of session data entries to update

    Raises:
        Exception: If the Q Connect API call fails
    """
    try:
        debug_log("Update QiC session request", {
            "assistantId": ai_assistant_id,
            "sessionId": qic_session_arn,
            "dataCount": len(session_data)
        })

        response = qconnect_client.update_session_data(
            assistantId=ai_assistant_id,
            sessionId=qic_session_arn,
            data=session_data
        )

        debug_log("Update QiC session response", response)

    except ClientError as e:
        logger.error(f"Q Connect API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating QiC session: {str(e)}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function for processing Amazon Connect events.

    Args:
        event: The Lambda event payload from Amazon Connect
        context: Lambda context object

    Returns:
        Lambda response with status code and message
    """
    try:
        # Extract contact ID
        contact_id = event.get('Details', {}).get('ContactData', {}).get('ContactId')
        
        if not contact_id:
            raise Exception("ContactId not found in event")

        debug_log("Processing Connect event", {
            "contactId": contact_id,
            "hasParameters": bool(event.get('Details', {}).get('Parameters'))
        })

        # Extract required configuration parameters
        ai_assistant_id = get_parameter_from_event_or_env(ContextKeys.AI_ASSISTANT_ID, event)
        connect_instance_id = os.environ.get(ContextKeys.CONNECT_INSTANCE_ID)

        if not connect_instance_id:
            raise Exception(f"Required parameter '{ContextKeys.CONNECT_INSTANCE_ID}' not found in Lambda environment variables.")

        # Convert Connect parameters to Q Connect session data format
        session_data = get_session_data(event)

        # Check if we have any data to update
        if not session_data:
            debug_log("No session data to update - all parameters were system parameters")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No session data to update'})
            }

        # Get Q Connect session ARN from the Connect contact
        qic_session_arn = get_qic_session_arn(contact_id, connect_instance_id)

        # Update Q Connect session with the extracted data
        update_qic_session(ai_assistant_id, qic_session_arn, session_data)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully updated {len(session_data)} session data entries'
            })
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }