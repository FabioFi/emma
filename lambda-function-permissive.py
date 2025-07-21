import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    TEMPORARY: Completely permissive Lambda for debugging
    This version allows all requests to test functionality
    """
    
    # Log everything for debugging
    print("=== COMPLETE EVENT DUMP ===")
    print(json.dumps(event, indent=2, default=str))
    print("==========================")
    
    # Always allow - for testing only
    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Methods': '*',
        'Access-Control-Allow-Credentials': 'false'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps('OK - CORS preflight')
        }
    
    try:
        # Get phone number
        phone_number = os.environ.get('WHATSAPP_PHONE', 'TEST_PHONE')
        
        if not phone_number or phone_number == 'TEST_PHONE':
            ssm = boto3.client('ssm')
            try:
                response = ssm.get_parameter(
                    Name='/emma-invitation/whatsapp-phone',
                    WithDecryption=True
                )
                phone_number = response['Parameter']['Value']
            except ClientError as e:
                print(f"Error getting parameter: {e}")
                # For testing, use a placeholder
                phone_number = "1234567890"
        
        # Extract action
        action = 'yes'
        if event.get('queryStringParameters'):
            action = event.get('queryStringParameters', {}).get('action', 'yes')
        
        # Messages
        messages = {
            'yes': "Ciao! Sarò presente al battesimo di Emma il 21 Settembre 2025. Grazie per l'invito! 🎉",
            'no': "Ciao! Purtroppo non potrò essere presente al battesimo di Emma. Mi dispiace molto! 😔"
        }
        
        whatsapp_url = f"https://wa.me/{phone_number}?text={messages.get(action, messages['yes'])}"
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({
                'whatsappUrl': whatsapp_url,
                'message': messages.get(action, messages['yes']),
                'debug': {
                    'status': 'SUCCESS - Lambda is working!',
                    'headers_received': event.get('headers', {}),
                    'phone_configured': phone_number != "1234567890",
                    'action': action
                }
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e),
                'debug': 'Lambda function is running but encountered an error'
            })
        }
