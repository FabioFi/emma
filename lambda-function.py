import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    AWS Lambda function to securely return WhatsApp phone number
    Restricted to https://fabiofi.github.io/emma/ only
    """
    
    # Define allowed domains for security
    ALLOWED_ORIGINS = [
        'https://fabiofi.github.io',
        'https://fabiofi.github.io/emma',
        'https://fabiofi.github.io/emma/'
    ]
    
    ALLOWED_REFERER_PATTERNS = [
        'https://fabiofi.github.io/emma',
        'https://fabiofi.github.io/emma/'
    ]
    
    # Get headers multiple ways (API Gateway can be inconsistent)
    headers = event.get('headers', {})
    multi_headers = event.get('multiValueHeaders', {})
    
    # Try different header access methods
    origin = (
        headers.get('origin') or 
        headers.get('Origin') or
        (multi_headers.get('origin', [None])[0] if multi_headers.get('origin') else None) or
        (multi_headers.get('Origin', [None])[0] if multi_headers.get('Origin') else None)
    )
    
    referer = (
        headers.get('referer') or 
        headers.get('Referer') or
        (multi_headers.get('referer', [None])[0] if multi_headers.get('referer') else None) or
        (multi_headers.get('Referer', [None])[0] if multi_headers.get('Referer') else None)
    )
    
    user_agent = (
        headers.get('user-agent') or 
        headers.get('User-Agent') or
        (multi_headers.get('user-agent', [None])[0] if multi_headers.get('user-agent') else None) or
        (multi_headers.get('User-Agent', [None])[0] if multi_headers.get('User-Agent') else None) or
        ''
    )
    
    # Also check request context for more info
    request_context = event.get('requestContext', {})
    source_ip = request_context.get('identity', {}).get('sourceIp', 'unknown')
    
    print(f"Security Check - Origin: {origin}, Referer: {referer}")
    print(f"User-Agent: {user_agent[:100]}..." if len(user_agent) > 100 else f"User-Agent: {user_agent}")
    print(f"Source IP: {source_ip}")
    
    # Strict security validation
    is_allowed = False
    allowed_reason = ""
    
    # Check origin first (most reliable)
    if origin and origin in ALLOWED_ORIGINS:
        is_allowed = True
        allowed_reason = f"Valid origin: {origin}"
    
    # Check referer as backup (for cases where origin might be missing)
    elif referer:
        for pattern in ALLOWED_REFERER_PATTERNS:
            if referer.startswith(pattern):
                is_allowed = True
                allowed_reason = f"Valid referer: {referer}"
                break
    
    # Additional validation: must be from a browser
    is_browser = user_agent and any(browser in user_agent.lower() for browser in [
        'mozilla', 'chrome', 'safari', 'firefox', 'edge', 'webkit'
    ])
    
    if is_allowed and not is_browser:
        is_allowed = False
        allowed_reason = "Not from a browser"
    
    print(f"Security decision: {allowed_reason if is_allowed else 'BLOCKED - Invalid origin/referer'}")
    
    # Set CORS headers - restrictive
    response_headers = {
        'Access-Control-Allow-Origin': 'https://fabiofi.github.io',
        'Access-Control-Allow-Headers': 'Content-Type, Origin, Referer, User-Agent',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Credentials': 'false',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps('OK')
        }
    
    # Block unauthorized requests
    if not is_allowed:
        print(f"BLOCKED REQUEST - Origin: {origin}, Referer: {referer}")
        return {
            'statusCode': 403,
            'headers': response_headers,
            'body': json.dumps({
                'error': 'Access denied. This API is restricted to authorized domains only.'
            })
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
                'allowed': True,
                'source': allowed_reason
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
