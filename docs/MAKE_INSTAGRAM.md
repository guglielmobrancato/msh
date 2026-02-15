# Make.com Instagram Automation Setup

This guide shows how to set up Instagram posting via Make.com (recommended method).

## Why Make.com?

- ✅ **ToS Compliant**: Uses official Instagram API
- ✅ **Reliable**: Handles rate limits, 2FA automatically
- ✅ **No Code**: Visual workflow builder
- ✅ **Professional**: Instagram Business account integration
- ❌ **Cost**: ~$9/month (Core plan)

## Prerequisites

1. Instagram **Business** or **Creator** account (required for API access)
2. Facebook Page connected to your Instagram account
3. Make.com account (free trial available)

## Setup Steps

### 1. Convert to Instagram Business Account

1. Open Instagram app
2. Go to **Settings → Account → Switch to Professional Account**
3. Choose **Business** or **Creator**
4. Connect to your Facebook Page (create one if needed)

### 2. Create Make.com Account

1. Sign up at [make.com](https://www.make.com)
2. Start free trial or subscribe to Core plan ($9/month)

### 3. Build Instagram Posting Workflow

#### Step 1: Create New Scenario

1. Click **Create a new scenario**
2. Search for **Webhooks** and add it as the first module
3. Click **Add** → **Custom webhook**
4. **Create a webhook** → Copy the webhook URL
5. Add this URL to your `.env` file:
   ```
   MAKE_WEBHOOK_URL=https://hook.make.com/your-unique-webhook-url
   ```

#### Step 2: Add Instagram Module

1. Click **+** to add next module
2. Search for **Instagram** and select **Instagram for Business**
3. Choose action: **Create an Image Post**
4. Click **Create a connection**
5. **Sign in with Facebook** (this connects your Instagram Business account)
6. Grant permissions

#### Step 3: Configure Instagram Post

Map the webhook data to Instagram fields:

- **Instagram Account**: Select your account
- **Caption**: Click the field → Select `caption` from webhook data
- **Image URL**: Click the field → Select `image_url` from webhook data
  - Note: Image must be publicly accessible URL
  - Alternative: Use Data Store to save images first

#### Step 4: Image Handling (Advanced)

Since the Python script sends base64-encoded images, add an intermediate step:

1. **After Webhook**: Add **HTTP** module → **Get a file**
2. Map this configuration:
   - URL: We'll upload to temporary storage first
   
**Better approach**: Upload image to S3/CloudFlare first, send URL

Simplified workflow for base64:
1. **Webhook** receives: `{"image_base64": "...", "caption": "..."}`
2. **Tools → Base64** → Decode to file
3. **Instagram** → Create post using decoded file

#### Step 5: Test Webhook

1. Click **Run once**
2. From your local terminal, test the webhook:

```bash
# Test webhook with sample data
curl -X POST https://hook.make.com/your-webhook-url \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Test post from Ancile AI\n\n#IntelligenceAnalysis #Geopolitics",
    "image_url": "https://picsum.photos/1080"
  }'
```

3. Check Make.com - it should receive the data
4. If it posts to Instagram successfully, workflow is ready!

#### Step 6: Activate Scenario

1. Click **Save** (bottom-right)
2. Toggle **ON** the scenario
3. Your webhook is now live 24/7

## Integration with Python Script

Your `instagram.py` module already has the Make.com integration:

```python
def post_to_instagram_make(image_path: str, caption: str):
    # Reads image file
    # Sends to Make.com webhook
    # Make.com posts to Instagram
```

Ensure `.env` is configured:
```
INSTAGRAM_ENABLED=true
INSTAGRAM_METHOD=make
MAKE_WEBHOOK_URL=https://hook.make.com/your-webhook-url
```

## Image Upload Strategy

**Option A: Upload to S3/CloudFlare (Recommended)**

1. Add AWS S3 or CloudFlare R2 to your setup
2. Python script uploads image to S3, gets public URL
3. Send URL to Make.com webhook
4. Make.com downloads from URL and posts

**Option B: Base64 via Webhook (Simple but limited)**

1. Python script encodes image as base64
2. Send base64 string to webhook
3. Make.com decodes and posts
4. Note: Webhook payload size limits (~1MB)

**Option C: Direct file upload (Advanced)**

Use Make.com Data Store:
1. Python sends image as multipart/form-data
2. Make.com stores in Data Store
3. Instagram module retrieves from Data Store

## Monitoring & Troubleshooting

### View Execution History

1. Make.com dashboard → **History**
2. See all webhook calls and their status
3. Click on any execution to see detailed logs

### Common Errors

**"Invalid Instagram Account"**
- Ensure you connected Instagram **Business** account
- Reconnect Instagram in Make.com settings

**"Image URL not accessible"**
- Image must be publicly accessible via HTTPS
- Test URL in browser first

**"Webhook timeout"**
- Make.com has 40-second timeout
- Ensure image processing is fast

**"Caption too long"**
- Instagram captions max: 2,200 characters
- Python script already handles this

## Advanced Features

### Scheduling Posts

Add **Tools → Sleep** module before Instagram:
- Delay posting by X hours
- Spread posts throughout the day

### Error Handling

Add error handler:
1. Click wrench icon on Instagram module
2. Add **Error handler** → **Ignore**
3. Or send error notification to email

### Multiple Instagram Accounts

1. Duplicate the Instagram module
2. Connect different accounts
3. Use **Router** to conditionally post to different accounts

## Cost Management

- **Free tier**: 1,000 operations/month
- **Core plan** ($9/month): 10,000 operations/month
- Each Instagram post = ~2-3 operations (webhook + post + error handling)
- For 10 posts/day: ~900 operations/month (within free tier!)

## Testing Checklist

- [ ] Webhook receives data correctly
- [ ] Image appears in Instagram post
- [ ] Caption text is formatted correctly  
- [ ] Hashtags are clickable
- [ ] Post appears on Instagram profile
- [ ] Make.com scenario stays active (doesn't auto-disable)

## Alternative: Zapier

If you prefer Zapier over Make.com:

1. Create **Webhook** trigger
2. Add **Instagram Business** action
3. Same process, slightly different UI
4. Cost: $20/month (Starter plan)

---

**Your Instagram automation is now hands-free!**
