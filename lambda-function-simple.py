import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    AWS Lambda function - SIMPLIFIED VERSION for GitHub Pages
    This version allows all GET requests to work around header issues
    """
    
    print("=== SIMPLE LAMBDA FUNCTION ===")
    print(f"HTTP Method: {event.get('httpMethod')}")
    print(f"Query Parameters: {event.get('queryStringParameters')}")
    print(f"Headers: {event.get('headers', {})}")
    print("==============================")
    
    # CORS headers - very permissive for GitHub Pages
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
            'body': json.dumps('OK')
        }
    
    # For GitHub Pages: Allow all GET requests (no security restrictions for now)
    http_method = event.get('httpMethod', '').upper()
    if http_method != 'GET':
        return {
            'statusCode': 405,
            'headers': response_headers,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    print("✅ Allowing request - GitHub Pages compatibility mode")
    
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
        
        # URL encode the message properly
        import urllib.parse
        message = messages.get(action, messages['yes'])
        encoded_message = urllib.parse.quote(message, safe='')
        
        whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
        
        print(f"Generated WhatsApp URL: {whatsapp_url}")
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({
                'whatsappUrl': whatsapp_url,
                'message': message,
                'action': action,
                'success': True
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
