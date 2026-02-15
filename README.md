# Ancile AI - Strategic Intelligence Platform

*Named after Ancile, the sacred shield of Mars that fell from the heavens*

A fully automated, headless intelligence publication system that operates 24/7 with zero human intervention, producing institutional-grade analysis matching the rigor of ACN, AISI, and CSIS.

## 🎯 Core Features

- **Autonomous Content Pipeline**: Automatically scrapes, analyzes, and publishes intelligence reports every 6 hours
- **AI-Powered Analysis**: Gemini 2.0 Flash transforms raw news into 1500-3000 word academic reports
- **Institutional Tone**: Enforces technical, objective language (e.g., "kinetic operations" vs "war")
- **Headless CMS**: Strapi-based publishing with searchable archive
- **Instagram Automation**: Auto-generates technical infographics and professional captions
- **Complete Anonymity**: All credentials stored in environment variables, no identifying metadata

## 🏗️ Architecture

```
Cron Scheduler (6h intervals)
  ↓
Ingestion Module (RSS/APIs/Gov Portals)
  ↓
Content Filter (Relevance Scoring)
  ↓
Gemini AI Analysis (Institutional Rewrite)
  ↓
PostgreSQL Database
  ↓
Strapi CMS Publishing + Instagram Automation
```

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Gemini API key (get from [Google AI Studio](https://aistudio.google.com/app/apikey))
- NewsAPI key (free tier available at [NewsAPI.org](https://newsapi.org/))
- Strapi CMS instance
- Instagram Business account (for automation)
- VPS for 24/7 operation (DigitalOcean, Linode, AWS EC2)

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd "c:\Users\gbran\Desktop\Intelligence website\intelligence-portal"
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your API keys
```

**Critical Environment Variables**:
- `GEMINI_API_KEY` - Your Gemini API key
- `NEWS_API_KEY` - Your NewsAPI key
- `DATABASE_URL` - PostgreSQL connection string
- `STRAPI_URL` + `STRAPI_API_TOKEN` - Strapi CMS credentials
- `INSTAGRAM_USERNAME` + `INSTAGRAM_PASSWORD` - Instagram credentials

### 3. Initialize Database

```bash
python scripts/setup_database.py
```

### 4. Test the Pipeline

```bash
# Dry run (no actual publishing)
python scripts/run_pipeline.py --dry-run

# Full run (publishes to Strapi + Instagram)
python scripts/run_pipeline.py
```

## 🔧 Configuration

Edit `config.py` for:
- RSS feed sources
- Government portal scraping targets
- Relevance keywords by category
- Institutional terminology mappings
- Content generation parameters

## 📊 Database Schema

### Tables
- **articles**: Main content storage
- **metadata**: Tags, keywords, entities
- **publish_queue**: Scheduling system for multi-platform publishing

See `models/schemas.py` for full schema.

## 🤖 AI System Prompt

The institutional writer prompt (`prompts/institutional_writer.txt`) enforces:
- Academic, objective tone
- Technical terminology (APT vectors, kinetic operations, fiscal solvency)
- Data-driven analysis with specific citations
- Long-form structure (1500-3000 words)

## 📸 Instagram Automation

Two methods available:

### Option A: Instagrapi (Python Library)
- ✅ Free, full control
- ❌ Higher risk (violates Instagram ToS)
- Set `INSTAGRAM_METHOD=instagrapi` in `.env`

### Option B: Make.com (No-Code Automation)
- ✅ ToS-compliant, reliable
- ❌ Costs ~$9/month
- Set `INSTAGRAM_METHOD=make` in `.env`
- Configure webhook in Make.com workflow

## 🖥️ VPS Deployment

### Ubuntu 22.04 Setup

```bash
# Install dependencies
sudo apt update
sudo apt install python3.11 python3-pip postgresql nginx

# Setup PostgreSQL
sudo -u postgres psql
CREATE DATABASE ancile_ai;
CREATE USER intel_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ancile_ai TO intel_user;
\q

# Deploy application
git clone <your-repo-url>
cd intelligence-portal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add production API keys
python scripts/setup_database.py
```

### Configure Cron Job

```bash
crontab -e

# Run pipeline every 6 hours
0 */6 * * * /home/user/intelligence-portal/venv/bin/python /home/user/intelligence-portal/scripts/run_pipeline.py >> /var/log/intel_pipeline.log 2>&1
```

## 💰 Estimated Costs

| Service | Monthly Cost | Purpose |
|---------|--------------|---------|
| VPS (DigitalOcean) | $12 | Hosting backend + database |
| Gemini API | $15-30 | AI analysis + image generation (10 articles/day) |
| NewsAPI | $0-49 | News aggregation (free tier available) |
| Make.com (optional) | $9 | Instagram automation |
| **Total** | **$36-100** | Fully autonomous operation |

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_ingestion.py -v
pytest tests/test_analysis.py -v

# Coverage report
pytest --cov=modules tests/
```

## 📁 Project Structure

```
intelligence-portal/
├── .env.example          # Environment template
├── config.py             # Central configuration
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── modules/
│   ├── ingestion.py     # RSS/API scraping
│   ├── analysis.py      # Gemini AI integration
│   ├── database.py      # SQLAlchemy models
│   ├── publishing.py    # Strapi publishing
│   └── instagram.py     # Instagram automation
├── models/
│   └── schemas.py       # Database schemas
├── prompts/
│   └── institutional_writer.txt  # AI system prompt
├── scripts/
│   ├── setup_database.py
│   └── run_pipeline.py
└── tests/
    └── test_pipeline.py
```

## 🔒 Security & Anonymity

- ✅ All API keys in `.env` (never in code)
- ✅ `.env` in `.gitignore` (never committed)
- ✅ VPS access via SSH key only
- ✅ Database user has minimal permissions
- ✅ No identifying metadata in generated content

## 📖 Documentation

- [Implementation Plan](../brain/implementation_plan.md)
- [System Architecture Diagram](../brain/implementation_plan.md#system-architecture)
- [AI System Prompt Details](prompts/institutional_writer.txt)

## 🆘 Troubleshooting

### "Configuration Error: validation error for Settings"
→ Missing required environment variables. Copy `.env.example` to `.env` and fill in all values.

### "Connection to database failed"
→ Ensure PostgreSQL is running: `sudo systemctl status postgresql`

### "Gemini API rate limit exceeded"
→ Free tier has 15 RPM limit. Reduce `MAX_ARTICLES_PER_RUN` in `.env`.

### Instagram posts not appearing
→ Check logs: `tail -f /var/log/intel_pipeline.log`
→ Verify credentials in `.env`
→ If using Instagrapi, account may be flagged (switch to Make.com)

## 📝 License

This is a private intelligence automation system. All generated content is owned by the system operator.

## ⚠️ Legal Notice

- **Content Attribution**: System cites all sources in generated articles
- **Instagram ToS**: Instagrapi method may violate Instagram's Terms of Service (use at own risk)
- **News API**: Respect API terms and rate limits

---

**Built for zero-touch autonomous intelligence publishing.**
