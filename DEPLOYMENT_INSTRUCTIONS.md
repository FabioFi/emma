# AWS Lambda Deployment Instructions (Manual)

Since AWS CLI is not available, follow these steps to deploy your updated Lambda function:

## Option 1: AWS Lambda Console (Recommended)

1. **Create deployment package**:
   ```bash
   zip lambda-deployment.zip lambda-function.py
   ```

2. **Upload via AWS Console**:
   - Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
   - Find your function: `emma-whatsapp-handler`
   - Click "Upload from" → ".zip file"
   - Upload `lambda-deployment.zip`
   - Click "Save"

## Option 2: Deploy Debug Version First (Recommended for troubleshooting)

If you want to see exactly what headers GitHub Pages is sending:

1. **Create debug deployment**:
   ```bash
   zip lambda-debug.zip lambda-function-debug.py
   ```

2. **Upload debug version**:
   - Go to AWS Lambda Console
   - Find your function: `emma-whatsapp-handler`
   - Click "Upload from" → ".zip file"
   - Upload `lambda-debug.zip`
   - **Important**: Rename the handler to `lambda-function-debug.lambda_handler`
   - Click "Save"

3. **Test from your website**:
   - Go to https://fabiofi.github.io/emma/
   - Click a WhatsApp button
   - Check the response in browser console
   - Check CloudWatch logs for detailed header info

4. **Deploy production version**:
   - After seeing what headers are sent, upload `lambda-deployment.zip`
   - Set handler back to `lambda-function.lambda_handler`

## Option 3: AWS CloudShell

If you have AWS CloudShell access:
1. Upload your files to CloudShell
2. Run the AWS CLI commands from there

## Testing After Deployment

1. Go to your website: https://fabiofi.github.io/emma/
2. Open browser console (F12)
3. Click "Sì" or "No" buttons
4. Check for any error messages

## Updated Security Features

The updated function now:
- ✅ Restricts access to your GitHub Pages domain
- ✅ Validates origin and referer headers
- ✅ Allows browser requests from GitHub Pages (handles missing headers)
- ✅ Blocks bots and crawlers
- ✅ Adds security headers
- ✅ Logs security decisions for monitoring

## If You Still Get 403 Errors

Deploy the debug version first to see exactly what headers GitHub Pages sends, then we can adjust the allowed patterns accordingly.
