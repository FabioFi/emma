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
        'Access-Control-Allow-Origin': 'https://fabiofi.github.io',
        'Access-Control-Allow-Headers': 'Content-Type, Origin, Referer, User-Agent, Accept',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Credentials': 'false',
        'Content-Type': 'application/json'
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
        
        # Special case: if the event contains form data directly (API Gateway misconfiguration)
        if 'action' in event and 'data' in event:
            print("Direct form data detected - handling as form submission")
            return handle_direct_form_data(event, response_headers)
        
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

def handle_direct_form_data(event, response_headers):
    """Handle form data sent directly in the event (API Gateway misconfiguration workaround)"""
    
    print("=== HANDLING DIRECT FORM DATA ===")
    
    # Extract form data directly from event
    action = event.get('action')
    form_data = event.get('data', {})
    
    print(f"Direct Action: {action}")
    print(f"Direct Form data: {form_data}")
    
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
        print(f"Environment RECIPIENT_EMAIL: {recipient_email}")
        
        if not recipient_email:
            # Try Systems Manager Parameter Store
            print("Trying Systems Manager Parameter Store...")
            ssm = boto3.client('ssm')
            try:
                response = ssm.get_parameter(
                    Name='/emma-invitation/recipient-email',
                    WithDecryption=True
                )
                recipient_email = response['Parameter']['Value']
                print(f"Got email from SSM: {recipient_email}")
            except ClientError as e:
                print(f"Error getting recipient email from SSM: {e}")
                return False
        
        if not recipient_email:
            print("No recipient email configured - check environment variables or SSM parameter")
            return False
        
        print(f"Using recipient email: {recipient_email}")
        
        # Create SES client
        print("Creating SES client...")
        ses = boto3.client('ses', region_name='eu-north-1')
        
        # Check if email is verified in SES
        try:
            verification_response = ses.get_identity_verification_attributes(
                Identities=[recipient_email]
            )
            verification_status = verification_response.get('VerificationAttributes', {}).get(recipient_email, {}).get('VerificationStatus', 'Unknown')
            print(f"Email verification status: {verification_status}")
            
            if verification_status != 'Success':
                print(f"ERROR: Email {recipient_email} is not verified in SES. Status: {verification_status}")
                print("Please verify your email in AWS SES first!")
                return False
        except Exception as ve:
            print(f"Error checking email verification: {ve}")
            print("Continuing anyway...")
        
        # Format email content
        subject = f"Conferma Partecipazione Battesimo Emma - {form_data.get('fullName', 'Unknown')}"
        print(f"Email subject: {subject}")
        
        # Create email body
        email_body = f"""Ciao!

Hai ricevuto una nuova conferma di partecipazione per il battesimo di Emma! 🎉

👤 Nome e Cognome: {form_data.get('fullName', 'N/A')}
👥 Numero di partecipanti: {form_data.get('participants', 'N/A')}
🍽️ Intolleranze alimentari: {form_data.get('intolerances', 'Nessuna specificata')}
📝 Note aggiuntive: {form_data.get('notes', 'Nessuna nota')}

📅 Data conferma: {form_data.get('timestamp', 'N/A')}

Grazie per aver confermato la partecipazione! ❤️

---
Questo messaggio è stato generato automaticamente dal sito dell'invito.
        """.strip()
        
        # Send email
        print(f"Attempting to send email from {recipient_email} to {recipient_email}")
        response = ses.send_email(
            Source=f"Battesimo Emma <{recipient_email}>",  # Sender with friendly name
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
        
        print(f"Email sent successfully! MessageId: {response['MessageId']}")
        print(f"Response: {response}")
        return True
        
    except ClientError as ce:
        print(f"AWS ClientError sending email: {ce}")
        print(f"Error Code: {ce.response['Error']['Code']}")
        print(f"Error Message: {ce.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"General error sending email: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
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