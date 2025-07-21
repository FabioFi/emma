#!/bin/bash
# Create deployment package for the GitHub Pages compatible Lambda function

echo "Creating deployment package for GitHub Pages compatible Lambda function..."

# Create the zip file
zip -r lambda-github-pages.zip lambda-function.py

echo "✅ Created lambda-github-pages.zip"
echo ""
echo "To deploy:"
echo "1. Go to AWS Lambda Console"
echo "2. Find your function: emma-whatsapp-handler"
echo "3. Click 'Upload from' → '.zip file'"
echo "4. Upload lambda-github-pages.zip"
echo "5. Make sure handler is set to: lambda-function.lambda_handler"
echo "6. Click 'Save'"
echo ""
echo "The function is now optimized for GitHub Pages which sends no headers!"
