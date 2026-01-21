# Zoho CRM to WhatsApp Automation

**Automated instant WhatsApp notifications for Zoho CRM leads via AiSensy**

## 🎯 Features

- ✅ **Instant notifications** - New leads get WhatsApp within seconds
- ✅ **Daily cohort analysis** - Email reports with lead segmentation
- ✅ **Click-to-approve campaigns** - Approve campaigns from email
- ✅ **Google Sheets tracking** - Complete message history
- ✅ **Zoho CRM updates** - Automatic notes on each lead
- ✅ **Smart segmentation** - Never contacted, 1st message, 2nd message, etc.
- ✅ **100% automated** - Runs 24/7 on Google Cloud Run

## 📋 Prerequisites

- [x] Zoho CRM account with API access
- [x] AiSensy account with approved template
- [x] Google Cloud account with billing enabled
- [x] Google Sheets created and shared
- [x] GitHub account

## 🚀 Quick Deployment (15 minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/kartavyasimpplifit/zoho-whatsapp-automation.git
cd zoho-whatsapp-automation
```

### Step 2: Set Environment Variables in Cloud Run

Go to Google Cloud Console and set these environment variables:

**Zoho Credentials:**
```
ZOHO_CLIENT_ID=1000.28T7ZV9M2HW0ZWNA8JRZ2M9I2GYJVA
ZOHO_CLIENT_SECRET=9e7b2561b5dadd1c22e5f803134ea58a8fa7694e24
ZOHO_REFRESH_TOKEN=1000.b07495c08fcecbff6a69683e47f7217b.609d217ad5a0ff1c849e884c28fbf5b2
ZOHO_DOMAIN=zoho.in
```

**AiSensy:**
```
AISENSY_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY5NjIzMjYzYzE3MTg2MGQ1MTA1OTA2YiIsIm5hbWUiOiJUZWNoY2xlYW4gSW5ub3ZhdGlvbnMgcHJpdmF0ZSBsaW1pdGVkIiwiYXBwTmFtZSI6IkFpU2Vuc3kiLCJjbGllbnRJZCI6IjY5NjIzMjYzYzE3MTg2MGQ1MTA1OTA2NiIsImFjdGl2ZVBsYW4iOiJGUkVFX0ZPUkVWRVIiLCJpYXQiOjE3NjgwNDMxMDd9.YL-6I4ZHityG7WIqe-f7UIMb6raQ41GfB-aVWR9Vppo
AISENSY_CAMPAIGN_NAME=techclean_first_campaign
```

**Google Sheets:**
```
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"zoho-whatsapp-integration",...}
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/1SxxssXpWb3lX3Wip1mCXClitSFZ1YGcooX52VN3X4FU/edit
```

**Email:**
```
REPORT_EMAIL=hello.tcinnovations@gmail.com
```

**Template:**
```
NEW_LEAD_TEMPLATE=your_approved_template_name
```

### Step 3: Deploy to Cloud Run

**Option A: Using gcloud CLI**

```bash
# Install gcloud CLI if needed
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set project zoho-whatsapp-integration

# Deploy
gcloud run deploy zoho-whatsapp-automation \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ZOHO_CLIENT_ID=...,ZOHO_CLIENT_SECRET=...,..."
```

**Option B: Using Cloud Console (Easier)**

1. Go to: https://console.cloud.google.com/run
2. Click **"CREATE SERVICE"**
3. Select **"Deploy one revision from an existing container image"**
4. Click **"Set up with Cloud Build"**
5. Choose: **"GitHub"**
6. Connect your GitHub account
7. Select repository: `kartavyasimpplifit/zoho-whatsapp-automation`
8. Click **"NEXT"**
9. Service name: `zoho-whatsapp-automation`
10. Region: `us-central1` (or closest to you)
11. Authentication: **Allow unauthenticated invocations**
12. Click **"Container, Variables & Secrets, Connections, Security"**
13. Add all environment variables from Step 2
14. Click **"CREATE"**

### Step 4: Get Your Service URL

After deployment, you'll get a URL like:
```
https://zoho-whatsapp-automation-xxxxx-uc.a.run.app
```

Copy this URL!

### Step 5: Update APPROVAL_BASE_URL

1. Go back to Cloud Run service
2. Edit environment variables
3. Add:
   ```
   APPROVAL_BASE_URL=https://zoho-whatsapp-automation-xxxxx-uc.a.run.app
   ```
4. Deploy new revision

### Step 6: Set up Zoho Webhook (For Instant Notifications)

1. Go to Zoho CRM → Setup → Automation → Webhooks
2. Click **"+ Configure Webhook"**
3. Module: **Leads**
4. Webhook on: **Create**
5. URL: `https://your-service-url.run.app/webhook/zoho`
6. Method: **POST**
7. Save

## ✅ Testing

### Test Webhook
```bash
curl -X POST https://your-service-url.run.app/webhook/zoho \
  -H "Content-Type: application/json" \
  -d '{"id":"test123","Lead_Status":"New","Lead_Source":"Website"}'
```

### Test Daily Report
```bash
curl -X POST https://your-service-url.run.app/daily-report
```

### Health Check
```bash
curl https://your-service-url.run.app/
```

## 📊 How It Works

### Flow 1: New Leads (Instant)
```
New lead created in Zoho
    ↓
Webhook triggers your Cloud Run service
    ↓
Lead data extracted
    ↓
WhatsApp sent via AiSensy
    ↓
Tracked in Google Sheets
    ↓
Note added to Zoho lead
```

### Flow 2: Daily Campaigns (Scheduled)
```
9 AM daily
    ↓
Fetch all leads from Zoho
    ↓
Get message history from Sheets
    ↓
Perform cohort analysis
    ↓
Generate email report with approval links
    ↓
You click approval link
    ↓
Campaign executes
    ↓
Summary email sent
```

## 📧 Email Reports

You'll receive daily emails at 9 AM with:

- **Never Contacted**: Leads with 0 messages
- **1st Message**: Leads with 1 message (follow-up candidates)
- **2nd Message**: Leads with 2 messages (offer candidates)
- **By Status**: Breakdown by lead status
- **By Source**: Breakdown by lead source  
- **High Potential**: Priority leads

Each section has a **"Send Campaign"** button - click to approve!

## 📈 Google Sheets Tracking

Your sheet has 2 worksheets:

1. **Message Log** - Every message sent with:
   - Timestamp, Lead ID, Name, Phone
   - Lead Status, Lead Source
   - Template used, Message count
   - Result (success/failed)
   - Campaign type (auto/manual)

2. **Summary** - Daily rollup with:
   - Date, Total sent, Success, Failed
   - New leads vs follow-ups
   - Campaign type

## 🔒 Security Best Practices

- ✅ All credentials in environment variables (not code)
- ✅ Private GitHub repository
- ✅ Service account for Google Sheets (not personal account)
- ✅ Zoho OAuth tokens (refresh automatically)
- ✅ HTTPS everywhere

## 💰 Cost

**Google Cloud Run:** FREE
- 2M requests/month free
- Your usage: ~10,000 requests/month
- Cost: $0/month

**Google Sheets API:** FREE
- Unlimited

**Other services:** Using your existing plans

## 🐛 Troubleshooting

### Webhook not triggering
- Check Zoho webhook is enabled
- Verify URL is correct
- Check Cloud Run logs

### Messages not sending
- Verify template is approved in AiSensy
- Check campaign is LIVE
- Confirm phone numbers have country code

### Sheets not updating
- Verify service account has Editor access
- Check credentials JSON is correct
- Review Cloud Run logs

### Emails not sending
- Check SENDER_EMAIL and SENDER_PASSWORD
- Use Gmail App Password (not regular password)
- Verify REPORT_EMAIL is correct

## 📝 Logs

View logs in Cloud Console:
```
https://console.cloud.google.com/run/detail/us-central1/zoho-whatsapp-automation/logs
```

## 🔄 Updating

To update the system:

```bash
git pull
gcloud run deploy zoho-whatsapp-automation --source .
```

Or use Cloud Build auto-deploy from GitHub!

## 📞 Support

- GitHub Issues: https://github.com/kartavyasimpplifit/zoho-whatsapp-automation/issues
- Email: hello.tcinnovations@gmail.com

## 📜 License

MIT License - Free to use and modify

---

**Built with ❤️ using Claude AI**
