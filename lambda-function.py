import json
import os
import boto3
from botocore.exceptions import ClientError
import urllib.parse
from datetime import datetime

def lambda_handler(event, context):
    """
    AWS Lambda function to handle Emma baptism invitation confirmations
    """
    
    # Debug: Log the entire event to see what we're getting
    print("=== FULL EVENT DEBUG ===")
    print("Event:", json.dumps(event, indent=2, default=str))
    print("======================")
    
    # CORS headers - support for POST requests
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
        # Check HTTP method
        http_method = event.get('httpMethod', 'GET')
        print(f"HTTP Method: {http_method}")
        
        if http_method == 'POST':
            # Handle form submission
            return handle_confirmation_form(event, response_headers)
        else:
            # Handle legacy WhatsApp functionality (if needed)
            return handle_legacy_whatsapp(event, response_headers)
            
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

def handle_confirmation_form(event, response_headers):
    """Handle the confirmation form submission and send email"""
    
    # Parse the request body
    body = event.get('body', '{}')
    print(f"POST body: {body}")
    
    try:
        if isinstance(body, str):
            body_data = json.loads(body)
        else:
            body_data = body
    except json.JSONDecodeError as e:
        print(f"Error parsing POST body: {e}")
        return {
            'statusCode': 400,
            'headers': response_headers,
            'body': json.dumps({
                'error': 'Invalid JSON in request body'
            })
        }
    
    # Extract form data
    action = body_data.get('action')
    form_data = body_data.get('data', {})
    
    print(f"Action: {action}")
    print(f"Form data: {form_data}")
    
    if action != 'confirmation':
        return {
            'statusCode': 400,
            'headers': response_headers,
            'body': json.dumps({
                'error': 'Invalid action'
            })
        }
    
    # Validate required fields
    required_fields = ['fullName', 'participants']
    for field in required_fields:
        if not form_data.get(field):
            return {
                'statusCode': 400,
                'headers': response_headers,
                'body': json.dumps({
                    'error': f'Missing required field: {field}'
                })
            }
    
    # Send email confirmation
    email_sent = send_confirmation_email(form_data)
    
    if email_sent:
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({
                'success': True,
                'message': 'Confirmation received and email sent successfully'
            })
        }
    else:
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({
                'error': 'Failed to send confirmation email'
            })
        }

def send_confirmation_email(form_data):
    """Send confirmation email using AWS SES"""
    
    try:
        # Get email from environment variable or Systems Manager
        recipient_email = os.environ.get('RECIPIENT_EMAIL')
        
        if not recipient_email:
            # Try Systems Manager Parameter Store
            ssm = boto3.client('ssm')
            try:
                response = ssm.get_parameter(
                    Name='/emma-invitation/recipient-email',
                    WithDecryption=True
                )
                recipient_email = response['Parameter']['Value']
            except ClientError as e:
                print(f"Error getting recipient email: {e}")
                return False
        
        if not recipient_email:
            print("No recipient email configured")
            return False
        
        # Create SES client
        ses = boto3.client('ses', region_name='eu-north-1')  # or your preferred region
        
        # Format email content
        subject = f"Conferma Partecipazione Battesimo Emma - {form_data.get('fullName', 'Unknown')}"
        
        # Create email body
        email_body = f"""
Nuova conferma di partecipazione per il battesimo di Emma:

Nome e Cognome: {form_data.get('fullName', 'N/A')}
Numero di partecipanti: {form_data.get('participants', 'N/A')}
Intolleranze alimentari: {form_data.get('intolerances', 'Nessuna specificata')}
Note aggiuntive: {form_data.get('notes', 'Nessuna nota')}

Data conferma: {form_data.get('timestamp', 'N/A')}

---
Messaggio automatico dal sistema di conferma partecipazioni
        """.strip()
        
        # Send email
        response = ses.send_email(
            Source=recipient_email,  # Sender (must be verified in SES)
            Destination={
                'ToAddresses': [recipient_email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': email_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f"Email sent successfully. MessageId: {response['MessageId']}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def handle_legacy_whatsapp(event, response_headers):
    """Handle legacy WhatsApp functionality (placeholder)"""
    
    return {
        'statusCode': 200,
        'headers': response_headers,
        'body': json.dumps({
            'message': 'Legacy WhatsApp functionality - please use the new confirmation form'
        })
    }