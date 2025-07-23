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
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
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
        
        # WORKAROUND: Since query parameters are not working with API Gateway,
        # use POST body for 'no' action and query params for 'yes' action
        print("=== WORKAROUND ACTION EXTRACTION ===")
        
        # Initialize action
        action = 'yes'  # default
        
        # Check HTTP method
        http_method = event.get('httpMethod', 'GET')
        print(f"HTTP Method: {http_method}")
        
        if http_method == 'POST':
            # For POST requests, check the body for action
            body = event.get('body', '{}')
            print(f"POST body: {body}")
            
            try:
                if body:
                    if isinstance(body, str):
                        body_data = json.loads(body)
                    else:
                        body_data = body
                    
                    if 'action' in body_data:
                        action = body_data['action']
                        print(f"Found action in POST body: '{action}'")
            except json.JSONDecodeError as e:
                print(f"Error parsing POST body: {e}")
        
        else:
            # For GET requests, try query parameters
            query_params = event.get('queryStringParameters')
            print(f"queryStringParameters: {query_params}")
            
            if query_params and 'action' in query_params:
                raw_action = query_params['action']
                print(f"Found action in queryStringParameters: '{raw_action}'")
                if raw_action in ['yes', 'no']:
                    action = raw_action
        
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
        
        # Create event string for debug
        event_str = json.dumps(event, default=str)
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({
                'whatsappUrl': whatsapp_url,
                'message': message,
                'debug': {
                    'action': action,
                    'httpMethod': http_method,
                    'queryParams': event.get('queryStringParameters'),
                    'hasBody': bool(event.get('body')),
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