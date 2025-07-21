#!/bin/bash
# Create deployment packages

echo "Creating deployment packages..."

# Main function (with security logic fixed)
zip -r lambda-main-fixed.zip lambda-function.py
echo "✅ Created lambda-main-fixed.zip (with fixed security logic)"

# Simple function (no security, guaranteed to work)
zip -r lambda-simple.zip lambda-function-simple.py
echo "✅ Created lambda-simple.zip (no security restrictions)"

echo ""
echo "=== DEPLOYMENT OPTIONS ==="
echo ""
echo "Option 1: Deploy lambda-main-fixed.zip (recommended)"
echo "- Fixed the elif logic issue"
echo "- Should now properly allow GitHub Pages requests"
echo "- Maintains some basic security"
echo ""
echo "Option 2: Deploy lambda-simple.zip (fallback)"
echo "- Completely permissive, guaranteed to work"
echo "- Use this if the fixed version still doesn't work"
echo "- Handler should be: lambda-function-simple.lambda_handler"
echo ""
echo "Upload either zip file to AWS Lambda Console!"
