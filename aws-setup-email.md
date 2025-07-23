# Setup Email Configuration for Emma Invitation

## 1. AWS SES Configuration

First, configure AWS SES (Simple Email Service) to send emails:

### Step 1: Verify your email address in SES
```bash
# Replace YOUR_EMAIL@domain.com with your actual email
aws ses verify-email-identity --email-address YOUR_EMAIL@domain.com --region eu-north-1
```

### Step 2: Check verification status
```bash
aws ses get-identity-verification-attributes --identities YOUR_EMAIL@domain.com --region eu-north-1
```

You'll receive a verification email - click the link to verify.

## 2. Store Email in Systems Manager Parameter Store

Create a secure parameter to store your email address:

```bash
# Replace YOUR_EMAIL@domain.com with your actual email
aws ssm put-parameter \
    --name "/emma-invitation/recipient-email" \
    --value "YOUR_EMAIL@domain.com" \
    --type "SecureString" \
    --description "Recipient email for Emma baptism invitation confirmations" \
    --region eu-north-1
```

## 3. Update Lambda Function Permissions

Your Lambda function needs permission to:
1. Read from Systems Manager Parameter Store
2. Send emails via SES

### Update the Lambda execution role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:eu-north-1:*:parameter/emma-invitation/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*"
        }
    ]
}
```

## 4. Test the Setup

1. Deploy the updated Lambda function
2. Test the form submission from the website
3. Check your email for confirmation messages

## 5. Security Notes

- The email address is stored encrypted in Systems Manager Parameter Store
- It's never exposed in the frontend code or logs
- Only the Lambda function can access it with proper IAM permissions
- SES ensures secure email delivery

## 6. Monitoring

Check CloudWatch logs for the Lambda function to monitor email sending:
- Function execution logs
- Email sending success/failure
- Form submission details

## 7. Cost Considerations

- AWS SES: Very low cost (usually free for small volumes)
- Systems Manager Parameter Store: Free for standard parameters
- Lambda: Pay per execution (very minimal for this use case)
