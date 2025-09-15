# Amazon Connect Q Connect Session Data Updater

A Lambda function that extracts key-value pairs from Amazon Connect contact flow parameters and updates the associated Q Connect session with this data as session attributes.

## Overview

This Lambda function bridges Amazon Connect contact flows with Q Connect AI assistants by automatically transferring contextual information from the contact flow to the Q Connect session. This enables AI assistants to have access to customer context, intent, and other relevant data during conversations.

## Use Case

- **Pass context data** (like intent, customer info, product details) from Connect to Q Connect AI agent
- **Enhance AI responses** with customer-specific context
- **Improve customer experience** by providing AI agents with relevant conversation history
- **Automate data transfer** between Amazon Connect and Q Connect services

## Architecture

```
Amazon Connect Contact Flow
           ↓
    Lambda Function (this)
           ↓
   Q Connect Session Update
           ↓
    AI Assistant with Context
```

## Features

- ✅ **Automatic parameter extraction** from Connect contact flow
- ✅ **Environment variable fallback** for configuration parameters
- ✅ **System parameter filtering** (excludes Lambda configuration from session data)
- ✅ **Comprehensive error handling** with structured logging
- ✅ **Debug logging** with conditional enablement
- ✅ **Type hints** and professional code standards
- ✅ **Comprehensive test suite** with 38 test cases

## Project Structure

```
connect-qic-session-data-update/
├── src/
│   └── index.py                 # Lambda function source code
├── infrastructure/
│   └── template.yaml           # CloudFormation deployment template
├── tests/
│   ├── test_index.py           # Comprehensive unit tests
│   ├── test_fixtures.py        # Test data validation
│   ├── test_simple.py          # Basic functionality tests
│   ├── fixtures.py             # Test data and mock responses
│   └── __init__.py             # Test package init
├── docs/                       # Documentation
├── requirements.txt            # Runtime dependencies
├── requirements-test.txt       # Test dependencies
├── pyproject.toml             # Python project configuration
├── pytest.ini                # Test configuration
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Prerequisites

- **AWS Account** with appropriate permissions
- **Amazon Connect Instance** with Q Connect enabled
- **Q Connect AI Assistant** configured
- **Python 3.9+** for development and testing

## Installation & Deployment

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd connect-qic-session-data-update

# Install dependencies
pip install -r requirements.txt

# Install test dependencies (optional)
pip install -r requirements-test.txt
```

### AWS Deployment

#### Option 1: CloudFormation Template

```bash
# Deploy using AWS CLI
aws cloudformation deploy \
  --template-file infrastructure/template.yaml \
  --stack-name connect-qic-session-updater \
  --parameter-overrides \
    ConnectInstanceId=your-connect-instance-id \
    AiAssistantId=your-qconnect-assistant-id \
  --capabilities CAPABILITY_IAM
```

#### Option 2: Manual Deployment

1. Create Lambda function with Python 3.11 runtime
2. Upload `src/index.py` as the function code
3. Set handler to `index.lambda_handler`
4. Configure environment variables (see Configuration section)
5. Attach IAM role with required permissions (see Permissions section)

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CONNECT_INSTANCE_ID` | Yes | Amazon Connect Instance ID | `12345678-1234-1234-1234-123456789012` |
| `AI_ASSISTANT_ID` | No* | Q Connect AI Assistant ID | `assistant-12345` |
| `AWS_REGION` | No | AWS Region | `us-east-1` |
| `DEBUG_LOG` | No | Enable debug logging | `true` |

*Can be provided via Connect event parameters instead

### Connect Event Parameters

The Lambda expects Amazon Connect to pass these parameters:

```json
{
  "Details": {
    "ContactData": {
      "ContactId": "contact-id-here"
    },
    "Parameters": {
      "AI_ASSISTANT_ID": "assistant-id",
      "customer_intent": "billing_inquiry",
      "customer_tier": "premium",
      "product_category": "mobile_service",
      "issue_priority": "high"
    }
  }
}
```

**System Parameters** (filtered out from session data):
- `AI_ASSISTANT_ID` - Used for Q Connect API calls
- `CONNECT_INSTANCE_ID` - Used for Connect API calls

**User Parameters** (passed to Q Connect session):
- All other parameters are converted to session attributes

## Permissions

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "qconnect:UpdateSessionData"
      ],
      "Resource": "arn:aws:qconnect:*:*:assistant/*/session/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "connect:DescribeContact"
      ],
      "Resource": "arn:aws:connect:*:*:instance/*/contact/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_index.py -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Test Coverage

The project includes **38 comprehensive tests** covering:
- ✅ Unit tests for all functions
- ✅ Integration tests for complete workflows
- ✅ Error handling scenarios
- ✅ Edge cases and validation
- ✅ Mock data and fixtures
- ✅ Environment variable handling

## Usage Examples

### Connect Contact Flow Integration

1. **Set up Lambda invoke block** in your Connect contact flow
2. **Pass parameters** you want to share with Q Connect:
   ```
   customer_intent: Get from previous flow logic
   customer_tier: Get from customer attributes
   product_category: Set based on call routing
   issue_priority: Derived from customer tier
   ```
3. **Configure environment variables** in Lambda
4. **Lambda automatically**:
   - Extracts all parameters from Connect
   - Filters out system parameters
   - Updates Q Connect session with customer context

### Sample Connect Parameters

```json
{
  "AI_ASSISTANT_ID": "assistant-12345",
  "customer_intent": "billing_inquiry",
  "customer_tier": "premium", 
  "account_type": "business",
  "previous_interaction_count": "3",
  "product_category": "mobile_service",
  "issue_priority": "high",
  "customer_sentiment": "frustrated"
}
```

These become Q Connect session attributes accessible to the AI assistant.

## Monitoring & Logging

### CloudWatch Logs

The function provides structured logging:

```json
{
  "level": "INFO",
  "message": "Successfully updated Q Connect session data",
  "params": {
    "contactId": "12345678-1234-1234-1234-123456789012",
    "assistantId": "assistant-12345",
    "updatedDataCount": 5
  }
}
```

### Debug Logging

Enable detailed debug logs by setting `DEBUG_LOG=true`:

```json
{
  "level": "DEBUG", 
  "message": "Get QiC session request",
  "params": {
    "ContactId": "12345678-1234-1234-1234-123456789012",
    "InstanceId": "test-instance-id"
  }
}
```

## Error Handling

The function handles various error scenarios:

- **Missing ContactId**: Returns 500 with descriptive error
- **Missing configuration**: Clear error messages for missing environment variables
- **Q Connect session not found**: Specific error when Connect contact has no Q Connect session
- **AWS API failures**: Proper ClientError handling with logging
- **No session data**: Returns 200 with message when only system parameters present

## API Reference

### Function Signature

```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]
```

### Input Event Structure

```python
{
    "Details": {
        "ContactData": {
            "ContactId": str  # Required
        },
        "Parameters": {
            str: str  # Key-value pairs for session data
        }
    }
}
```

### Response Structure

**Success Response:**
```python
{
    "statusCode": 200,
    "body": '{"message": "Successfully updated N session data entries"}'
}
```

**Error Response:**
```python
{
    "statusCode": 500,
    "body": '{"error": "Error description"}'
}
```

## Development

### Code Style

This project follows established Python conventions:
- **Google-style docstrings**
- **Type hints** on all functions
- **Comprehensive error handling**
- **Structured logging**
- **4-space indentation**
- **Snake_case naming**

### Adding New Features

1. **Update source code** in `src/index.py`
2. **Add corresponding tests** in `tests/`
3. **Update CloudFormation template** if needed
4. **Run test suite**: `pytest`
5. **Update documentation**

## Troubleshooting

### Common Issues

1. **ImportError in tests**
   - Ensure `pythonpath = src` in `pytest.ini`
   - Run tests from project root directory

2. **Q Connect session not found**
   - Verify Q Connect is enabled in Connect contact flow
   - Check that contact flow creates Q Connect session before calling Lambda

3. **Permission denied errors**
   - Review IAM permissions
   - Ensure Lambda execution role has required permissions

4. **Missing environment variables**
   - Set `CONNECT_INSTANCE_ID` in Lambda environment
   - Or pass `AI_ASSISTANT_ID` via Connect parameters

### Debug Steps

1. **Enable debug logging**: Set `DEBUG_LOG=true`
2. **Check CloudWatch logs** for structured error messages
3. **Run tests locally**: `pytest -v`
4. **Validate event structure** matches expected format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

**Ankit Jain**
- Version: 1.0.0
- Last Updated: 2024

## Related Documentation

- [Amazon Connect Developer Guide](https://docs.aws.amazon.com/connect/)
- [Amazon Q Connect API Reference](https://docs.aws.amazon.com/qconnect/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [CloudFormation Template Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/)