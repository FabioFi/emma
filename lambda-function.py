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
    
    # Additional debug: Check all possible places where action might be
    print("=== ADDITIONAL DEBUG ===")
    print("pathParameters:", event.get('pathParameters'))
    print("queryStringParameters:", event.get('queryStringParameters'))
    print("multiValueQueryStringParameters:", event.get('multiValueQueryStringParameters'))
    print("httpMethod:", event.get('httpMethod'))
    print("path:", event.get('path'))
    print("resource:", event.get('resource'))
    print("========================")
    
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
        
        # Extract action from query parameters - with manual parsing fallback
        query_params = event.get('queryStringParameters')
        print(f"Raw queryStringParameters: {query_params}")
        print(f"queryStringParameters type: {type(query_params)}")
        
        # Initialize action to default
        action = 'yes'
        
        # Method 1: Standard query parameters
        if query_params and isinstance(query_params, dict):
            action = query_params.get('action', 'yes')
            print(f"Method 1 - Extracted action from queryStringParameters: '{action}'")
        
        # Method 2: Try to extract from raw query string 
        raw_query_string = event.get('rawQueryString', '')
        print(f"Method 2 - Raw query string: '{raw_query_string}'")
        if raw_query_string:
            if 'action=no' in raw_query_string:
                print("Method 2 - Detected action=no in rawQueryString, overriding action")
                action = 'no'
            elif 'action=yes' in raw_query_string:
                print("Method 2 - Detected action=yes in rawQueryString")
                action = 'yes'
        
        # Method 3: Parse from request context resource path if available
        request_context = event.get('requestContext', {})
        resource_path = request_context.get('resourcePath', '')
        request_path = request_context.get('path', '')
        print(f"Method 3 - Resource path: '{resource_path}', Request path: '{request_path}'")
        
        # Method 4: Manual parsing of query string from various sources
        # Check if there's a query string in the event somewhere
        full_event_str = json.dumps(event, default=str)
        if 'action=no' in full_event_str and action != 'no':
            print("Method 4 - Found action=no in full event JSON, overriding")
            action = 'no'
        
        # Method 5: Try multiValueQueryStringParameters
        multi_query_params = event.get('multiValueQueryStringParameters') or {}
        if multi_query_params.get('action'):
            extracted_action = multi_query_params.get('action')
            if isinstance(extracted_action, list) and len(extracted_action) > 0:
                extracted_action = extracted_action[0]
            print(f"Method 5 - Found action in multiValueQueryStringParameters: {extracted_action}")
            action = extracted_action
        
        # Method 6: Parse query string manually if we can find it
        # Look for patterns like ?action=no or &action=no in the event
        import re
        action_pattern = r'[?&]action=([^&\s"]+)'
        match = re.search(action_pattern, full_event_str)
        if match:
            manual_action = match.group(1)
            print(f"Method 6 - Manual regex extraction found action: '{manual_action}'")
            if manual_action in ['yes', 'no']:
                action = manual_action
        
        # Debug: Log the action being processed
        print(f"=== ACTION DEBUG ===")
        print(f"Raw query parameters object: {event.get('queryStringParameters')}")
        print(f"Query parameters type: {type(event.get('queryStringParameters'))}")
        print(f"MultiValue query parameters: {multi_query_params}")
        print(f"Raw query string: {event.get('rawQueryString', 'NOT_FOUND')}")
        print(f"Action key exists in query_params: {'action' in (query_params or {})}")
        print(f"Raw action value from query_params: {(query_params or {}).get('action', 'NO_ACTION_KEY')}")
        print(f"Final extracted action: '{action}'")
        print("==================")
        
        # Ensure action is valid
        if action not in ['yes', 'no']:
            print(f"Invalid action '{action}', defaulting to 'yes'")
            action = 'yes'
        
        # Prepare WhatsApp messages
        messages = {
            'yes': "Ciao! Sarò presente al battesimo di Emma il 21 Settembre 2025. Grazie per l'invito!",
            'no': "Ciao! Purtroppo non potrò essere presente al battesimo di Emma. Mi dispiace molto!"
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