import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    AWS Lambda function to securely return WhatsApp phone number
    Temporarily permissive for debugging header issues
    """
    
    # Debug: Log the entire event to see what we're getting
    print("=== FULL EVENT DEBUG ===")
    print("Event:", json.dumps(event, indent=2, default=str))
    print("======================")
    
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
    
    print(f"Extracted - Origin: {origin}, Referer: {referer}, User-Agent: {user_agent}")
    print(f"Source IP: {source_ip}")
    
    # TEMPORARY: Be more permissive while debugging
    # Allow requests that seem to come from legitimate sources
    is_allowed = False
    is_browser = False
    
    # Check if we have any valid headers
    if origin and 'fabiofi.github.io' in origin:
        is_allowed = True
        print("Allowed by origin")
    elif referer and 'fabiofi.github.io' in referer:
        is_allowed = True
        print("Allowed by referer")
    elif user_agent and any(browser in user_agent.lower() for browser in ['mozilla', 'chrome', 'safari', 'firefox', 'edge', 'webkit']):
        is_browser = True
        # For now, allow browser requests even without origin/referer
        # This handles the GitHub Pages header issue
        is_allowed = True
        print("Allowed by browser user-agent (GitHub Pages fallback)")
    else:
        # Last resort: if headers are completely missing, it might be API Gateway config issue
        # Check if this looks like a legitimate request
        if not origin and not referer and not user_agent:
            print("No headers detected - possible API Gateway issue")
            # Temporarily allow to test functionality
            is_allowed = True
            is_browser = True
            print("TEMPORARY: Allowing request with no headers for debugging")
    
    # More lenient browser check
    is_browser = is_browser or any(browser in user_agent.lower() for browser in ['mozilla', 'chrome', 'safari', 'firefox', 'edge', 'webkit']) if user_agent else True
    
    print(f"Final decision - Is allowed: {is_allowed}, Is browser: {is_browser}")
    
    # CORS headers - be permissive for now
    response_headers = {
        'Access-Control-Allow-Origin': origin if origin else 'https://fabiofi.github.io',
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
        query_params = event.get('queryStringParameters') or {}
        action = query_params.get('action', 'yes') if query_params else 'yes'
        
        # Debug: Log the action being processed
        print(f"=== ACTION DEBUG ===")
        print(f"Raw query parameters object: {event.get('queryStringParameters')}")
        print(f"Query parameters type: {type(event.get('queryStringParameters'))}")
        print(f"Query parameters dict: {query_params}")
        print(f"Action key exists: {'action' in query_params if query_params else False}")
        print(f"Raw action value: {query_params.get('action') if query_params else 'NO_PARAMS'}")
        print(f"Final extracted action: '{action}'")
        print("==================")
        
        # Prepare WhatsApp messages
        messages = {
            'yes': "Ciao! Sarò presente al battesimo di Emma il 21 Settembre 2025. Grazie per l'invito! 🎉",
            'no': "Ciao! Purtroppo non potrò essere presente al battesimo di Emma. Mi dispiace molto! 😔"
        }
        
        # URL encode the message properly
        import urllib.parse
        message = messages.get(action, messages['yes'])
        
        # Debug: Log the selected message
        print(f"Selected message for action '{action}': {message}")
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
                    'phone': phone_number,
                    'encoded_message': encoded_message
                }
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