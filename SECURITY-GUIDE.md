# Securing AWS API for GitHub Pages Only

This guide shows multiple ways to restrict your AWS API to only accept requests from your GitHub Pages site: `https://fabiofi.github.io/emma/`

## 🛡️ Security Layers

### 1. **Origin/Referer Validation (Primary)**
The Lambda function checks:
- `Origin` header matches `https://fabiofi.github.io`
- `Referer` header starts with `https://fabiofi.github.io/`
- `User-Agent` contains browser identifiers

### 2. **Rate Limiting**
- AWS WAF: 100 requests per 5 minutes per IP
- API Gateway: 10 requests/second, 20 burst, 1000/day

### 3. **Geographic Restrictions**
- Only allows requests from: Italy, US, Germany, UK
- Blocks other countries via AWS WAF

### 4. **API Gateway Resource Policy**
- Restricts access based on referer header
- Only allows requests from your GitHub Pages domain

## 🚀 Deployment Options

### Option A: Maximum Security (Recommended)

Deploy with all security features:

```bash
aws cloudformation create-stack \
  --stack-name emma-whatsapp-secure \
  --template-body file://cloudformation-template-secure.yaml \
  --parameters ParameterKey=WhatsAppPhoneNumber,ParameterValue=YOUR_PHONE \
               ParameterKey=GitHubPagesDomain,ParameterValue=fabiofi.github.io \
  --capabilities CAPABILITY_IAM
```

### Option B: Basic Security

Use the updated Lambda function with origin validation:

```bash
aws cloudformation create-stack \
  --stack-name emma-whatsapp \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=WhatsAppPhoneNumber,ParameterValue=YOUR_PHONE \
  --capabilities CAPABILITY_IAM
```

## 🔧 Quick Fix for GitHub Pages

If you're getting 403 errors from your GitHub Pages site, here's the immediate solution:

### Step 1: Update Lambda Function Code

Replace your Lambda function code with the fixed version that handles GitHub Pages properly. The updated code:

1. **Checks headers case-insensitively** (GitHub Pages may send different cases)
2. **Allows requests without Origin/Referer** if they have a valid browser User-Agent
3. **Provides debug information** in error responses

### Step 2: Deploy Updated Function

```bash
# Zip the updated function
zip lambda-function.zip lambda-function.py

# Update your Lambda function
aws lambda update-function-code \
  --function-name emma-whatsapp-handler \
  --zip-file fileb://lambda-function.zip
```

### Step 3: Test from GitHub Pages

Visit `https://fabiofi.github.io/emma/` and click the buttons. It should now work!

### Step 4: Check Logs (if still failing)

```bash
# View CloudWatch logs to see what headers are being sent
aws logs tail /aws/lambda/emma-whatsapp-handler --follow
```

## 🔧 Manual Security Setup

If you prefer manual setup:

### 1. Update Lambda Function
Replace your Lambda code with the secured version that includes:
- Origin/Referer validation
- User-Agent checking
- Specific CORS configuration

### 2. Add API Gateway Resource Policy
In API Gateway console:
1. Go to your API → Resource Policy
2. Add this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:Referer": "https://fabiofi.github.io/*"
        }
      }
    }
  ]
}
```

### 3. Configure Usage Plan (Rate Limiting)
1. Go to API Gateway → Usage Plans
2. Create new plan with:
   - Rate: 10 requests/second
   - Burst: 20 requests
   - Quota: 1000 requests/day

### 4. Set up AWS WAF (Optional)
1. Create Web ACL in AWS WAF
2. Add rate limiting rule (100 req/5min)
3. Add geographic restriction
4. Associate with API Gateway stage

## 🧪 Testing Security

### Valid Request (Should Work)
```bash
curl -H "Origin: https://fabiofi.github.io" \
     -H "User-Agent: Mozilla/5.0 (compatible browser)" \
     "https://your-api.amazonaws.com/prod/whatsapp?action=yes"
```

### Invalid Requests (Should Fail)
```bash
# No origin header
curl "https://your-api.amazonaws.com/prod/whatsapp?action=yes"

# Wrong origin
curl -H "Origin: https://malicious-site.com" \
     "https://your-api.amazonaws.com/prod/whatsapp?action=yes"

# Non-browser user agent
curl -H "Origin: https://fabiofi.github.io" \
     -H "User-Agent: curl/7.68.0" \
     "https://your-api.amazonaws.com/prod/whatsapp?action=yes"
```

## 📊 Monitoring & Alerts

### CloudWatch Metrics to Monitor:
- `4XXError` - Failed authentication attempts
- `Count` - Total API calls
- `Latency` - Response times

### Set up Alerts:
1. High number of 403 errors (potential attack)
2. Unusual traffic patterns
3. API calls from blocked countries

## 🔒 Additional Security Tips

1. **Use HTTPS Only**: GitHub Pages serves over HTTPS
2. **Monitor Logs**: Check CloudWatch logs regularly
3. **Rotate Secrets**: Change phone number storage occasionally
4. **Update Dependencies**: Keep Lambda runtime updated
5. **Backup Configuration**: Save your CloudFormation templates

## 🆘 Troubleshooting

### Common Issues:

**403 Forbidden Errors from GitHub Pages:**

The most common issue is that GitHub Pages doesn't always send the `Origin` header for AJAX requests. Here's how to fix it:

1. **Use the Debug Version**: Deploy `lambda-function-debug.py` temporarily to see what headers are being sent:
   ```bash
   # Upload the debug version to see actual headers
   aws lambda update-function-code \
     --function-name emma-whatsapp-handler \
     --zip-file fileb://lambda-debug.zip
   ```

2. **Check CloudWatch Logs**: Look at the Lambda logs to see what headers GitHub Pages is actually sending.

3. **Quick Fix**: Use the updated `lambda-function.py` which handles GitHub Pages properly by:
   - Allowing requests with no Origin/Referer if User-Agent looks like a browser
   - Case-insensitive header checking
   - Fallback for GitHub Pages AJAX behavior

**Expected Behavior from GitHub Pages:**
- ✅ May not send `Origin` header for same-domain AJAX requests
- ✅ May not send `Referer` header in some browsers
- ✅ Will send a valid browser `User-Agent`

**Other 403 Issues:**
- Check if request includes proper Origin/Referer headers
- Verify User-Agent looks like a browser
- Ensure request comes from GitHub Pages domain

**CORS Errors:**
- Verify Origin header matches allowed domains
- Check that OPTIONS requests are handled correctly
- Ensure API Gateway CORS is configured

**Rate Limiting:**
- Reduce request frequency
- Check Usage Plan limits
- Monitor CloudWatch metrics

## 💡 How It Works

1. **Browser Request**: User clicks button on GitHub Pages
2. **Headers Check**: Lambda validates Origin/Referer/User-Agent
3. **Rate Limiting**: AWS WAF and Usage Plan enforce limits
4. **Response**: If valid, returns WhatsApp URL
5. **Fallback**: If invalid, returns 403 error

This multi-layer approach makes it extremely difficult for unauthorized users to access your API while maintaining smooth operation for legitimate visitors to your GitHub Pages site.
