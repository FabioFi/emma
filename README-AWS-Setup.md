# Emma Invitation - AWS Lambda Setup Guide

This guide will help you set up an AWS Lambda function to securely handle the WhatsApp phone number, keeping it out of your GitHub repository.

## �️ Security Features

### Domain Restriction
Your API is now secured to only accept requests from `https://fabiofi.github.io`:

1. **Origin/Referer Validation**: Lambda function validates request headers
2. **User-Agent Checking**: Blocks non-browser requests (prevents curl/postman abuse)
3. **Rate Limiting**: 100 requests per 5 minutes per IP via AWS WAF
4. **Geographic Restrictions**: Only allows requests from IT, US, DE, GB
5. **API Gateway Resource Policy**: Additional referer-based filtering

### Deployment with Security

For maximum security, use the enhanced template:

```bash
aws cloudformation create-stack \
  --stack-name emma-whatsapp-secure \
  --template-body file://cloudformation-template-secure.yaml \
  --parameters ParameterKey=WhatsAppPhoneNumber,ParameterValue=myphonenumber \
               ParameterKey=GitHubPagesDomain,ParameterValue=fabiofi.github.io \
  --capabilities CAPABILITY_IAM
```

> 📖 **For detailed security configuration, see [SECURITY-GUIDE.md](./SECURITY-GUIDE.md)**

## �🚀 Quick Setup (Recommended)

### Option 1: Using CloudFormation (Automatic)

1. **Deploy the Stack:**
   ```bash
   aws cloudformation create-stack \
     --stack-name emma-whatsapp \
     --template-body file://cloudformation-template.yaml \
     --parameters ParameterKey=WhatsAppPhoneNumber,ParameterValue=myphonenumber \
     --capabilities CAPABILITY_IAM
   ```

2. **Get the API Endpoint:**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name emma-whatsapp \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
     --output text
   ```

3. **Update your website:**
   - Copy the API endpoint URL
   - Replace `LAMBDA_API_ENDPOINT` in `index.html` with your actual endpoint

### Option 2: Manual Setup via AWS Console

1. **Create Lambda Function:**
   - Go to AWS Lambda Console
   - Create new function: `emma-whatsapp-handler`
   - Runtime: Python 3.9
   - Copy code from `lambda-function.py`

2. **Set Environment Variable:**
   - In Lambda configuration → Environment variables
   - Add: `WHATSAPP_PHONE` = `myphonenumber`

3. **Create API Gateway:**
   - Go to API Gateway Console
   - Create REST API: `emma-whatsapp-api`
   - Create resource: `/whatsapp`
   - Create GET method
   - Integration type: Lambda Function
   - Enable CORS

4. **Deploy API:**
   - Deploy to stage: `prod`
   - Copy the invoke URL

## 🔧 Configuration

### Update Your Website

Replace this line in `index.html`:
```javascript
const LAMBDA_API_ENDPOINT = 'https://4sl8y10tm8.execute-api.eu-north-1.amazonaws.com/prod/whatsapp';
```

With your actual API endpoint.

## 🛡️ Security Features

1. **Phone Number Protection:**
   - Stored in AWS Systems Manager Parameter Store (encrypted)
   - Environment variable as fallback
   - Never exposed in client-side code

2. **Domain Restriction:**
   - Only accepts requests from `https://fabiofi.github.io`
   - Origin/Referer header validation
   - User-Agent checking (blocks automated tools)

3. **Rate Limiting:**
   - AWS WAF: 100 requests per 5 minutes per IP
   - API Gateway: 10 req/sec, 20 burst, 1000/day

4. **Geographic Filtering:**
   - Only allows traffic from Italy, US, Germany, UK
   - Blocks requests from other countries

5. **CORS Protection:**
   - Secure cross-origin requests
   - Specific domain allowlisting

## 📱 How It Works

1. User clicks "Sì" or "No" button
2. JavaScript calls your Lambda API
3. Lambda returns WhatsApp URL with pre-filled message
4. User is redirected to WhatsApp

## 🌍 Messages

- **Yes:** "Ciao! Sarò presente al battesimo di Emma il 21 Settembre 2025. Grazie per l'invito! 🎉"
- **No:** "Ciao! Purtroppo non potrò essere presente al battesimo di Emma. Mi dispiace molto! 😔"

## 💰 AWS Costs

- Lambda: Free tier covers up to 1M requests/month
- API Gateway: Free tier covers up to 1M API calls/month
- Parameter Store: Free for standard parameters

**Estimated monthly cost: $0** (within free tier limits)

## 🔍 Testing

Test your API endpoint:
```bash
curl "https://your-api-endpoint.amazonaws.com/prod/whatsapp?action=yes"
```

Expected response:
```json
{
  "whatsappUrl": "https://wa.me/myphonenumber?text=Ciao! Sarò presente...",
  "message": "Ciao! Sarò presente al battesimo di Emma il 21 Settembre 2025. Grazie per l'invito! 🎉"
}
```

## 🗑️ Cleanup

To remove all resources:
```bash
aws cloudformation delete-stack --stack-name emma-whatsapp
```

## 📞 Support

If you need help:
1. Check AWS CloudWatch logs for Lambda errors
2. Verify API Gateway settings
3. Test the endpoint directly first
4. Ensure CORS is properly configured
