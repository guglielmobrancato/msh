# 🛡️ Ancile AI - Setup Instructions

## Automated Daily Article Generation

This repository is configured to automatically generate 4 intelligence articles every day using GitHub Actions.

### 🔑 Required API Keys

You need to add two secrets to your GitHub repository:

#### 1. Gemini API Key (Free)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key

#### 2. NewsAPI Key (Free)
1. Go to [NewsAPI.org](https://newsapi.org/register)
2. Sign up for free account
3. Copy your API key

### ⚙️ Add Secrets to GitHub

1. Go to your repository: `https://github.com/guglielmobrancato/msh`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these two secrets:

**Secret 1:**
- Name: `GEMINI_API_KEY`
- Value: Your Gemini API key

**Secret 2:**
- Name: `NEWS_API_KEY`
- Value: Your NewsAPI key

### 🚀 How It Works

Once secrets are configured:

- **Automatic**: Runs every day at 6:00 AM UTC (7:00 AM CET)
- **Manual**: You can also trigger manually from Actions tab
- **Output**: Generates 4 articles (Geopolitics, Defense, Cyber, Finance)
- **Updates**: Automatically updates the website

### 📂 File Structure

```
msh/
├── index.html                    # Homepage (auto-updated)
├── articles/                     # Generated articles
│   ├── 2026-02-15-geopolitics.html
│   ├── 2026-02-15-defense.html
│   ├── 2026-02-15-cyber.html
│   └── 2026-02-15-finance.html
├── scripts/
│   └── generate_daily_articles.py  # Article generator
└── .github/workflows/
    └── generate-articles.yml       # GitHub Actions workflow
```

### 🧪 Test Manually

To test the workflow manually:

1. Go to **Actions** tab in GitHub
2. Click **Generate Daily Intelligence Articles**
3. Click **Run workflow**
4. Wait 2-3 minutes
5. Check the website for new articles!

### 🌐 Website

Your site is live at: **https://msh.martestudios.com**

Articles are automatically added daily with clickable links.

---

**Need help?** Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
