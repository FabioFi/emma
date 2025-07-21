import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    AWS Lambda function - DEBUG VERSION
    This version logs all headers and allows requests for debugging
    """
    
    # Debug: Log everything we receive
    print("=== DEBUG INFO ===")
    print("Event:", json.dumps(event, indent=2, default=str))
    print("Headers received:", json.dumps(event.get('headers', {}), indent=2))
    print("Request context:", json.dumps(event.get('requestContext', {}), indent=2))
    
    # Get headers (case-insensitive)
    headers_dict = {k.lower(): v for k, v in event.get('headers', {}).items()}
    
    origin = headers_dict.get('origin')
    referer = headers_dict.get('referer')
    user_agent = headers_dict.get('user-agent', '')
    host = headers_dict.get('host')
    
    print(f"Origin: {origin}")
    print(f"Referer: {referer}")
    print(f"User-Agent: {user_agent}")
    print(f"Host: {host}")
    print("=================")
    
    # For debugging, allow all requests but log the info
    response_headers = {
        'Access-Control-Allow-Origin': '*',  # Temporarily allow all for debugging
        'Access-Control-Allow-Headers': 'Content-Type',
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
        
        # Alternative - Get from AWS Systems Manager Parameter Store
        if not phone_number:
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
        
        # Extract action from query parameters
        action = event.get('queryStringParameters', {}).get('action', 'yes') if event.get('queryStringParameters') else 'yes'
        
        # Prepare WhatsApp messages
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
                    'origin': origin,
                    'referer': referer,
                    'user_agent': user_agent[:100] if user_agent else None,
                    'host': host,
                    'all_headers': dict(headers_dict)
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
                'details': str(e)
            })
        }
