#!/bin/bash

echo "🔍 Diagnosing API Gateway and Lambda Configuration..."
echo ""

# Get API Gateway info
echo "📡 Checking API Gateway configuration..."
API_ID="4sl8y10tm8"  # From your URL
REGION="eu-north-1"   # From your URL

# Check if API exists and get basic info
aws apigateway get-rest-api --rest-api-id $API_ID --region $REGION 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Could not access API Gateway. Check your AWS credentials and region."
    exit 1
fi

echo ""
echo "🔧 Checking API Gateway method configuration..."

# Check the method configuration
aws apigateway get-method \
    --rest-api-id $API_ID \
    --resource-id $(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?pathPart==`whatsapp`].id' --output text) \
    --http-method GET \
    --region $REGION

echo ""
echo "🔧 Checking Integration configuration..."

# Check integration
aws apigateway get-integration \
    --rest-api-id $API_ID \
    --resource-id $(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?pathPart==`whatsapp`].id' --output text) \
    --http-method GET \
    --region $REGION

echo ""
echo "🔍 Testing API Gateway directly..."

# Test the API
curl -v -X GET \
    -H "Origin: https://fabiofi.github.io" \
    -H "Referer: https://fabiofi.github.io/emma/" \
    -H "User-Agent: Mozilla/5.0 (Debugging) AppleWebKit/537.36" \
    "https://$API_ID.execute-api.$REGION.amazonaws.com/prod/whatsapp?action=yes"

echo ""
echo ""
echo "🛠️  Common API Gateway Issues and Fixes:"
echo ""
echo "1. 🔧 CORS not properly configured:"
echo "   - Enable CORS on the /whatsapp resource"
echo "   - Allow headers: Content-Type, Origin, Referer, User-Agent"
echo "   - Allow methods: GET, OPTIONS"
echo ""
echo "2. 🔧 Lambda Proxy Integration not enabled:"
echo "   - Integration type should be 'AWS_PROXY'"
echo "   - This passes headers correctly to Lambda"
echo ""
echo "3. 🔧 Method Request not configured:"
echo "   - Method Request should not require API key"
echo "   - Authorization should be 'NONE'"
echo ""
echo "4. 🔧 Stage not deployed:"
echo "   - Deploy API to 'prod' stage after changes"
echo ""
echo "💡 Quick fixes:"
echo "aws apigateway put-integration \\"
echo "  --rest-api-id $API_ID \\"
echo "  --resource-id RESOURCE_ID \\"
echo "  --http-method GET \\"
echo "  --type AWS_PROXY \\"
echo "  --integration-http-method POST \\"
echo "  --uri 'arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/LAMBDA_ARN/invocations' \\"
echo "  --region $REGION"
