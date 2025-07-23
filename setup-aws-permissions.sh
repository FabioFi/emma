#!/bin/bash

# Setup script for Emma Invitation Lambda function permissions
# Run this script to configure all AWS permissions needed

set -e  # Exit on any error

# Configuration - Update these values
LAMBDA_FUNCTION_NAME="emma-invitation-function"  # Replace with your Lambda function name
RECIPIENT_EMAIL="your-email@domain.com"          # Replace with your email
AWS_REGION="eu-north-1"                          # Your AWS region

echo "🚀 Setting up Emma Invitation AWS permissions..."

# Step 1: Get Lambda function role
echo "📋 Getting Lambda function role..."
ROLE_ARN=$(aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --query 'Configuration.Role' --output text)
ROLE_NAME=$(echo "$ROLE_ARN" | sed 's/.*\///')
echo "Found role: $ROLE_NAME"

# Step 2: Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Step 3: Create policy
echo "📝 Creating IAM policy..."
POLICY_NAME="EmmaInvitationLambdaPolicy"
POLICY_ARN="arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"

# Check if policy already exists
if aws iam get-policy --policy-arn "$POLICY_ARN" >/dev/null 2>&1; then
    echo "Policy already exists, creating new version..."
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file://lambda-policy.json \
        --set-as-default
else
    echo "Creating new policy..."
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://lambda-policy.json \
        --description "Policy for Emma invitation Lambda function"
fi

# Step 4: Attach policy to role
echo "🔗 Attaching policy to Lambda role..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" || echo "Policy might already be attached"

# Step 5: Verify email in SES
echo "📧 Setting up SES email verification..."
aws ses verify-email-identity --email-address "$RECIPIENT_EMAIL" --region "$AWS_REGION"
echo "Check your email ($RECIPIENT_EMAIL) and click the verification link!"

# Step 6: Store email in Parameter Store
echo "🔐 Storing email in Systems Manager Parameter Store..."
aws ssm put-parameter \
    --name "/emma-invitation/recipient-email" \
    --value "$RECIPIENT_EMAIL" \
    --type "SecureString" \
    --description "Recipient email for Emma baptism invitation confirmations" \
    --region "$AWS_REGION" \
    --overwrite

echo "✅ Setup completed successfully!"
echo ""
echo "📋 Summary:"
echo "- Lambda role: $ROLE_NAME"
echo "- Policy: $POLICY_NAME"
echo "- Email configured: $RECIPIENT_EMAIL"
echo "- Parameter stored: /emma-invitation/recipient-email"
echo ""
echo "🎯 Next steps:"
echo "1. Check your email and verify the SES verification link"
echo "2. Deploy your updated Lambda function code"
echo "3. Test the form submission from your website"
echo ""
echo "🔍 To check SES verification status:"
echo "aws ses get-identity-verification-attributes --identities $RECIPIENT_EMAIL --region $AWS_REGION"
