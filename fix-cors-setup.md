# Fix CORS Configuration for Emma Invitation API Gateway

## Problem
The Lambda function is working but API Gateway is not returning proper CORS headers for the domain `https://fabiofi.github.io`.

## Solution: Configure CORS in API Gateway Console

### Option 1: AWS Console (Recommended)

1. Go to AWS API Gateway Console
2. Find your API (the one with endpoint `4sl8y10tm8.execute-api.eu-north-1.amazonaws.com`)
3. Select your resource (`/whatsapp`)
4. Click "Actions" → "Enable CORS"
5. Configure:
   - **Access-Control-Allow-Origin**: `https://fabiofi.github.io`
   - **Access-Control-Allow-Headers**: `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,Referer,User-Agent`
   - **Access-Control-Allow-Methods**: `GET,POST,OPTIONS`
6. Click "Enable CORS and replace existing CORS headers"
7. **Important**: Click "Actions" → "Deploy API" to stage `prod`

### Option 2: AWS CLI Commands

```bash
# Get your API ID
API_ID="4sl8y10tm8"  # From your endpoint URL
REGION="eu-north-1"

# Update the resource to enable CORS
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?pathPart==`whatsapp`].id' --output text) \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION

# Add CORS headers to the integration response
aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?pathPart==`whatsapp`].id' --output text) \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": "'\''https://fabiofi.github.io'\''",
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,Referer,User-Agent'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,OPTIONS'\''"
    }' \
    --region $REGION

# Deploy the API to make changes live
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $REGION
```

### Option 3: Quick Test with Wildcard (Temporary)

If you need a quick test, you can temporarily use wildcard CORS:

```bash
# Update Lambda function to use wildcard temporarily
# Change the lambda-function.py CORS headers to:
# 'Access-Control-Allow-Origin': '*'
```

## Verification

After making changes:

1. Deploy the Lambda function with updated CORS headers
2. Test from browser console:
   ```javascript
   fetch('https://4sl8y10tm8.execute-api.eu-north-1.amazonaws.com/prod/whatsapp', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
           action: 'confirmation',
           data: { fullName: 'Test', participants: '1', intolerances: '', notes: '', timestamp: new Date().toISOString() }
       })
   }).then(r => r.json()).then(console.log);
   ```

## Important Notes

- **Always deploy API Gateway changes** - CORS configuration won't work without deployment
- The Lambda CORS headers AND API Gateway CORS configuration both need to match
- Use specific domain (`https://fabiofi.github.io`) for security instead of wildcard
- If testing locally, you might need to add `http://localhost` or `file://` to allowed origins
