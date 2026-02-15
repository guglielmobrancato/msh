# Strapi CMS Quick Setup Guide for Ancile AI

## Prerequisites
- Node.js 18+ installed
- PostgreSQL running (same instance can be used for both Strapi and main app)

## Installation

### 1. Create Strapi Project

```bash
# Navigate to your project root
cd "c:\Users\gbran\Desktop\Intelligence website"

# Create Strapi CMS (use SQLite for quick start, or PostgreSQL for production)
npx create-strapi-app@latest ancile-ai-cms --quickstart

# For PostgreSQL instead of SQLite:
# npx create-strapi-app@latest ancile-ai-cms --dbclient=postgres
```

### 2. Configure Content Type

After Strapi starts (http://localhost:1337/admin):

1. Create admin account
2. Go to **Content-Type Builder**
3. Create new **Collection Type** called "Article"
4. Add fields:
   - `title` (Text, required, short text)
   - `content` (Rich Text, required)
   - `summary` (Text)
   - `category` (Enumeration: geopolitics, defense, cyber, finance)
   - `source_url` (Text, URL format)
   - `word_count` (Number, integer)
5. **Save** and restart Strapi

### 3. Generate API Token

1. Go to **Settings → API Tokens**
2. Click **Create new API Token**
3. Name: "Intelligence Portal"
4. Token type: **Full access** (or custom with `articles.create` permission)
5. **Save** and copy the token
6. Add to your `.env` file:
   ```
   STRAPI_API_TOKEN=your_token_here
   ```

### 4. Enable Public API Access (Optional)

If you want the frontend accessible:

1. Go to **Settings → Roles → Public**
2. Check permissions for `article.find` and `article.findOne`
3. **Save**

## Production Deployment

For production VPS:

```bash
# Build Strapi for production
cd ancile-ai-cms
npm run build
npm run start

# Or use PM2 for process management
npm install -g pm2
pm2 start npm --name "strapi" -- start
pm2 save
pm2 startup
```

## Querying Articles

Once articles are published, access via:

- Admin: http://localhost:1337/admin
- API: http://localhost:1337/api/articles
- Single article: http://localhost:1337/api/articles/1

## Troubleshooting

**Issue: "Cannot connect to database"**
- Ensure PostgreSQL is running
- Check connection string in `.env`

**Issue: "API token invalid"**
- Regenerate token in Strapi admin
- Ensure no extra spaces in `.env` file

**Issue: "Cannot create article"**
- Verify API token has `articles.create` permission
- Check Content-Type fields match the payload
