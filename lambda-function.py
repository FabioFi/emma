import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    AWS Lambda function to securely return WhatsApp phone number
    Restricted to GitHub Pages domain only
    """
    
    # Allowed origins - restrict to your GitHub Pages domain
    allowed_origins = [
        'https://fabiofi.github.io',
        'http://localhost:3000',  # For local development
        'http://127.0.0.1:5500'   # For VS Code Live Server
    ]
    
    # Get the origin from the request
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    referer = event.get('headers', {}).get('referer') or event.get('headers', {}).get('Referer')
    
    # Security check: Verify origin/referer
    is_allowed = False
    if origin:
        is_allowed = any(origin.startswith(allowed) for allowed in allowed_origins)
    elif referer:
        is_allowed = any(referer.startswith(allowed) for allowed in allowed_origins)
    
    # Additional security: Check User-Agent to prevent direct API calls
    user_agent = event.get('headers', {}).get('user-agent') or event.get('headers', {}).get('User-Agent', '')
    is_browser = any(browser in user_agent.lower() for browser in ['mozilla', 'chrome', 'safari', 'firefox', 'edge'])
    
    if not is_allowed or not is_browser:
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': origin if is_allowed else 'null',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'error': 'Access denied. This API is restricted to authorized domains only.'
            })
        }
    
    # CORS headers for allowed origins
    headers = {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Credentials': 'false'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps('OK')
        }
    
    try:
        # Method 1: Get phone number from environment variable
        phone_number = os.environ.get('WHATSAPP_PHONE')
        
        # Method 2: Alternative - Get from AWS Systems Manager Parameter Store
        # This is more secure for production
        if not phone_number:
            ssm = boto3.client('ssm')
            try:
                response = ssm.get_parameter(
                    Name='/emma-invitation/whatsapp-phone',
                    WithDecryption=True  # Use if parameter is encrypted
                )
                phone_number = response['Parameter']['Value']
            except ClientError as e:
                print(f"Error getting parameter: {e}")
        
        if not phone_number:
            return {
                'statusCode': 500,
                'headers': headers,
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
            'headers': headers,
            'body': json.dumps({
                'whatsappUrl': whatsapp_url,
                'message': messages.get(action, messages['yes'])
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }
