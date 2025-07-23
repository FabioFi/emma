import json
import os
import boto3
from botocore.exceptions import ClientError
import urllib.parse

def lambda_handler(event, context):
    """
    AWS Lambda function to securely return WhatsApp phone number
    Simplified version focused on parameter extraction
    """
    
    # Debug: Log the entire event to see what we're getting
    print("=== FULL EVENT DEBUG ===")
    print("Event:", json.dumps(event, indent=2, default=str))
    print("======================")
    
    # CORS headers - be permissive for now
    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Origin, Referer, User-Agent',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Credentials': 'false'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps('OK')
        }
    
    try:
        # Get phone number from environment variable
        phone_number = os.environ.get('WHATSAPP_PHONE')
        
        if not phone_number:
            # Try Systems Manager Parameter Store
            ssm = boto3.client('ssm')
            try:
                response = ssm.get_parameter(
                    Name='/emma-invitation/whatsapp-phone',
                    WithDecryption=True
                )
                phone_number = response['Parameter']['Value']
            except ClientError as e:
                print(f"Error getting parameter: {e}")
        
        if not phone_number:
            return {
                'statusCode': 500,
                'headers': response_headers,
                'body': json.dumps({
                    'error': 'Phone number not configured'
                })
            }
        
        # SIMPLIFIED ACTION EXTRACTION
        print("=== SIMPLIFIED ACTION EXTRACTION ===")
        
        # Initialize action
        action = 'yes'  # default
        
        # Method 1: Direct queryStringParameters check
        query_params = event.get('queryStringParameters')
        print(f"queryStringParameters: {query_params}")
        
        if query_params:
            if 'action' in query_params:
                raw_action = query_params['action']
                print(f"Found action in queryStringParameters: '{raw_action}'")
                if raw_action == 'no':
                    action = 'no'
                elif raw_action == 'yes':
                    action = 'yes'
        
        # Method 2: Extract from the entire event as string (most reliable)
        event_str = str(event)
        print(f"Searching in event string for action parameter...")
        
        if "'action': 'no'" in event_str:
            print("Found 'action': 'no' in event string")
            action = 'no'
        elif '"action": "no"' in event_str:
            print('Found "action": "no" in event string')
            action = 'no'
        elif 'action=no' in event_str:
            print("Found action=no in event string")
            action = 'no'
        
        # Method 3: Try path parameters if it's configured that way
        path_params = event.get('pathParameters')
        if path_params and 'action' in path_params:
            path_action = path_params['action']
            print(f"Found action in pathParameters: '{path_action}'")
            if path_action in ['yes', 'no']:
                action = path_action
        
        print(f"Final action determined: '{action}'")
        print("=====================================")
        
        # Prepare WhatsApp messages
        messages = {
            'yes': "Ciao! Sarò presente al battesimo di Emma il 21 Settembre 2025. Grazie per l'invito!",
            'no': "Ciao! Purtroppo non potrò essere presente al battesimo di Emma. Mi dispiace molto!"
        }
        
        message = messages.get(action, messages['yes'])
        print(f"Selected message: {message}")
        
        encoded_message = urllib.parse.quote(message, safe='')
        whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
        
        print(f"Generated WhatsApp URL: {whatsapp_url}")
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({
                'whatsappUrl': whatsapp_url,
                'message': message,
                'debug': {
                    'action': action,
                    'queryParams': query_params,
                    'extractedFromEvent': f"action={action}",
                    'eventContainsActionNo': ('action=no' in event_str or "'action': 'no'" in event_str or '"action": "no"' in event_str)
                }
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }