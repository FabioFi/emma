import json
import os
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    DEBUG VERSION: Log all headers to understand what GitHub Pages sends
    """
    
    # Debug: Log the entire event to see what we're getting
    print("=== FULL HEADERS DEBUG ===")
    headers = event.get('headers', {})
    multi_headers = event.get('multiValueHeaders', {})
    request_context = event.get('requestContext', {})
    
    print("Headers:", json.dumps(headers, indent=2))
    print("Multi Headers:", json.dumps(multi_headers, indent=2))
    print("Request Context Identity:", json.dumps(request_context.get('identity', {}), indent=2))
    print("Query Parameters:", json.dumps(event.get('queryStringParameters'), indent=2))
    print("===========================")
    
    # Get headers multiple ways
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
    
    print(f"EXTRACTED VALUES:")
    print(f"Origin: '{origin}'")
    print(f"Referer: '{referer}'")
    print(f"User-Agent: '{user_agent}'")
    
    # For debugging, allow all requests but log what we got
    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Origin, Referer, User-Agent',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Credentials': 'false'
    }
    
    # Handle OPTIONS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps('OK')
        }
    
    # For debugging, return the headers we received
    return {
        'statusCode': 200,
        'headers': response_headers,
        'body': json.dumps({
            'debug': True,
            'received_origin': origin,
            'received_referer': referer,
            'received_user_agent': user_agent[:200] if user_agent else None,
            'all_headers': headers,
            'message': 'This is debug mode - check CloudWatch logs for full details'
        })
    }
    
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
