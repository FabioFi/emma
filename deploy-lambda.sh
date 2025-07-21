#!/bin/bash

# Script to create and deploy Lambda function
echo "Creating Lambda deployment package..."

# Create deployment directory
mkdir -p lambda-deployment
cd lambda-deployment

# Copy the Lambda function
cp ../lambda-function.py .

# Create ZIP package
zip -r lambda-function.zip lambda-function.py

echo "Lambda package created: lambda-function.zip"
echo ""
echo "Next steps:"
echo "1. Upload this ZIP to AWS Lambda"
echo "2. Set environment variable WHATSAPP_PHONE=myphonenumber"
echo "3. Set up API Gateway trigger"
echo "4. Update your website to use the API endpoint"
