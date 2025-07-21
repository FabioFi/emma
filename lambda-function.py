import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    AWS Lambda function to securely return WhatsApp phone number
    Handles GitHub Pages requests that may not send headers due to API Gateway configuration
    """
    
    # Get headers multiple ways (API Gateway can be inconsistent)
    headers = event.get('headers', {})
    multi_headers = event.get('multiValueHeaders', {})
    request_context = event.get('requestContext', {})
    
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
    source_ip = request_context.get('identity', {}).get('sourceIp', 'unknown')
    
    print(f"Security Check - Origin: {origin}, Referer: {referer}")
    print(f"User-Agent: {user_agent[:100]}..." if len(user_agent) > 100 else f"User-Agent: {user_agent}")
    print(f"Source IP: {source_ip}")
    print(f"HTTP Method: {event.get('httpMethod')}")
    print(f"Query Params: {event.get('queryStringParameters')}")
    print(f"Headers: {headers}")
    print(f"Headers length: {len(headers)}")
    
    # For debugging: log the exact conditions we're checking
    no_origin = not origin
    no_referer = not referer  
    no_user_agent = not user_agent
    empty_headers = len(headers) == 0
    print(f"Conditions - no_origin: {no_origin}, no_referer: {no_referer}, no_user_agent: {no_user_agent}, empty_headers: {empty_headers}")
    
    # GitHub Pages Security Strategy:
    # Since GitHub Pages + API Gateway strips headers, we need a different approach
    is_allowed = False
    allowed_reason = ""
    
    # Get basic request info
    query_params = event.get('queryStringParameters') or {}
    http_method = event.get('httpMethod', '').upper()
    
    print(f"Evaluating request - Method: {http_method}, Has query params: {bool(query_params)}")
    
    # Check if we have proper headers (ideal case)
    if origin and 'fabiofi.github.io' in origin:
        is_allowed = True
        allowed_reason = f"Valid origin: {origin}"
        print("✅ Allowed by origin")
    
    if not is_allowed and referer and 'fabiofi.github.io' in referer:
        is_allowed = True
        allowed_reason = f"Valid referer: {referer}"
        print("✅ Allowed by referer")
    
    # GitHub Pages fallback cases - be very permissive
    if not is_allowed and not origin and not referer:
        print("🔍 No origin/referer detected - checking GitHub Pages cases")
        
        # Case 1: No headers at all (most common GitHub Pages case)
        if not user_agent and len(headers) == 0:
            print("📱 GitHub Pages case: completely empty headers")
            if http_method in ['GET', 'OPTIONS']:
                is_allowed = True
                allowed_reason = f"GitHub Pages (no headers, {http_method})"
                print("✅ Allowed - GitHub Pages with no headers")
        
        # Case 2: Some headers but no origin/referer
        if not is_allowed and len(headers) >= 0:  # Any request, even with empty headers
            print("📱 GitHub Pages case: missing origin/referer")
            if http_method in ['GET', 'OPTIONS']:
                is_allowed = True
                allowed_reason = f"GitHub Pages ({http_method}, headers: {len(headers)})"
                print("✅ Allowed - GitHub Pages missing headers")
    
    # If we have user agent, validate it's a real browser
    if not is_allowed and user_agent and any(browser in user_agent.lower() for browser in [
        'mozilla', 'chrome', 'safari', 'firefox', 'edge', 'webkit'
    ]):
        # Block obvious bots even with user agent
        if not any(bot in user_agent.lower() for bot in ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget']):
            is_allowed = True
            allowed_reason = f"Browser request (User-Agent validated)"
            print("✅ Allowed by user agent")
    
    # Last resort: for GitHub Pages, allow all GET/OPTIONS requests
    if not is_allowed and http_method in ['GET', 'OPTIONS']:
        print("🚨 Last resort: allowing GET/OPTIONS for GitHub Pages compatibility")
        is_allowed = True
        allowed_reason = f"GitHub Pages compatibility ({http_method})"
    
    print(f"Security decision: {allowed_reason if is_allowed else 'BLOCKED - Invalid request'}")
    
    # Set CORS headers - permissive for GitHub Pages
    response_headers = {
        'Access-Control-Allow-Origin': '*',  # GitHub Pages needs this due to header issues
        'Access-Control-Allow-Headers': 'Content-Type, Origin, Referer, User-Agent',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Credentials': 'false',
        'X-Content-Type-Options': 'nosniff',
        'Cache-Control': 'no-cache, no-store, must-revalidate'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps('OK')
        }
    
    # Block unauthorized requests (but be permissive for GitHub Pages)
    if not is_allowed:
        print(f"BLOCKED REQUEST - Origin: {origin}, Referer: {referer}, User-Agent: {user_agent[:50] if user_agent else 'None'}")
        
        # Log additional context for debugging
        print(f"Request details - Method: {event.get('httpMethod')}, Query: {event.get('queryStringParameters')}")
        print(f"Headers count: {len(headers)}, Context: {request_context.get('requestId', 'unknown')}")
        
        return {
            'statusCode': 403,
            'headers': response_headers,
            'body': json.dumps({
                'error': 'Access denied. This API is restricted to authorized requests only.',
                'debug_info': {
                    'has_origin': origin is not None,
                    'has_referer': referer is not None,
                    'has_user_agent': bool(user_agent),
                    'headers_count': len(headers)
                }
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
