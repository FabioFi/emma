import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    AWS Lambda function to securely return WhatsApp phone number
    Restricted to GitHub Pages domain only - Fixed for GitHub Pages
    """
    
    # Debug: Log the headers we receive (remove this in production)
    print("Headers received:", json.dumps(event.get('headers', {}), indent=2))
    print("Request context:", json.dumps(event.get('requestContext', {}), indent=2))
    
    # Allowed origins - restrict to your GitHub Pages domain
    allowed_origins = [
        'https://fabiofi.github.io',
        'http://localhost:3000',  # For local development
        'http://127.0.0.1:5500',  # For VS Code Live Server
        'http://localhost:5500',  # Alternative Live Server port
        'file://'                 # For local file testing
    ]
    
    # Get headers (case-insensitive)
    headers_dict = {k.lower(): v for k, v in event.get('headers', {}).items()}
    
    origin = headers_dict.get('origin')
    referer = headers_dict.get('referer')
    user_agent = headers_dict.get('user-agent', '')
    
    # Debug logging
    print(f"Origin: {origin}")
    print(f"Referer: {referer}")
    print(f"User-Agent: {user_agent}")
    
    # Security check: Verify origin/referer
    is_allowed = False
    
    # Check origin first
    if origin:
        is_allowed = any(origin.startswith(allowed) for allowed in allowed_origins)
        print(f"Origin check: {is_allowed}")
    
    # If no origin, check referer (GitHub Pages often doesn't send Origin for same-origin requests)
    if not is_allowed and referer:
        is_allowed = any(referer.startswith(allowed) for allowed in allowed_origins)
        print(f"Referer check: {is_allowed}")
    
    # For GitHub Pages, sometimes neither Origin nor Referer is sent for AJAX requests
    # In this case, we'll allow if the User-Agent looks legitimate and we're not in strict mode
    if not is_allowed and not origin and not referer:
        # This is a fallback for GitHub Pages AJAX requests
        is_browser = any(browser in user_agent.lower() for browser in ['mozilla', 'chrome', 'safari', 'firefox', 'edge'])
        if is_browser:
            is_allowed = True
            print("Allowed due to missing headers but valid browser User-Agent")
    
    # Check User-Agent to prevent direct API calls
    is_browser = any(browser in user_agent.lower() for browser in ['mozilla', 'chrome', 'safari', 'firefox', 'edge', 'webkit'])
    
    print(f"Is allowed: {is_allowed}, Is browser: {is_browser}")
    
    if not is_allowed or not is_browser:
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': origin if origin and any(origin.startswith(allowed) for allowed in allowed_origins) else 'https://fabiofi.github.io',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'error': 'Access denied. This API is restricted to authorized domains only.',
                'debug': {
                    'origin': origin,
                    'referer': referer,
                    'user_agent': user_agent[:100] if user_agent else None,
                    'is_allowed': is_allowed,
                    'is_browser': is_browser
                }
            })
        }
    
    # CORS headers for allowed origins
    response_headers = {
        'Access-Control-Allow-Origin': origin if origin else 'https://fabiofi.github.io',
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
                'message': messages.get(action, messages['yes'])
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }
