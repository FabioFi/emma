#!/bin/bash

# Script to update Lambda function with GitHub Pages fix
echo "🔧 Updating Lambda function for GitHub Pages compatibility..."

# Create deployment package
echo "📦 Creating deployment package..."
zip -r lambda-function.zip lambda-function.py

# Update Lambda function
echo "🚀 Updating Lambda function..."
aws lambda update-function-code \
  --function-name emma-whatsapp-handler \
  --zip-file fileb://lambda-function.zip

if [ $? -eq 0 ]; then
    echo "✅ Lambda function updated successfully!"
    echo ""
    echo "🧪 Testing from GitHub Pages:"
    echo "Visit: https://fabiofi.github.io/emma/"
    echo "Click the 'Sì' or 'No' buttons to test"
    echo ""
    echo "📊 To view logs:"
    echo "aws logs tail /aws/lambda/emma-whatsapp-handler --follow"
else
    echo "❌ Failed to update Lambda function"
    echo "Please check your AWS credentials and function name"
fi

# Clean up
rm lambda-function.zip

echo ""
echo "🔍 If you're still getting 403 errors, deploy the debug version:"
echo "1. zip lambda-function-debug.py"
echo "2. Update function with debug version"
echo "3. Check CloudWatch logs to see actual headers"
echo "4. Switch back to fixed version once working"
