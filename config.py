"""
Ancile AI - Configuration Management
Strategic Intelligence Platform - Named after the sacred shield of Mars
Centralized configuration loading from environment variables with validation.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Main configuration class with validation."""
    
    # ============ AI & Content Generation ============
    gemini_api_key: str = Field(..., min_length=30)
    gemini_max_rpm: int = Field(default=15)
    
    # ============ News & Data Sources ============
    news_api_key: str = Field(..., min_length=30)
    alphavantage_api_key: Optional[str] = Field(default=None)
    
    # ============ Database ============
    database_url: str = Field(..., min_length=10)
    
    # ============ Headless CMS (Strapi) ============
    strapi_url: str = Field(default="http://localhost:1337")
    strapi_api_token: str = Field(..., min_length=30)
    
    # ============ Instagram Automation ============
    instagram_username: Optional[str] = Field(default=None)
    instagram_password: Optional[str] = Field(default=None)
    make_webhook_url: Optional[str] = Field(default=None)
    instagram_enabled: bool = Field(default=True)
    instagram_method: str = Field(default="instagrapi")  # instagrapi or make
    
    # ============ System Configuration ============
    max_articles_per_run: int = Field(default=5, ge=1, le=20)
    min_relevance_score: float = Field(default=0.7, ge=0.0, le=1.0)
    article_min_words: int = Field(default=1500)
    article_max_words: int = Field(default=3000)
    pipeline_interval_hours: int = Field(default=6)
    
    # ============ Optional: Monitoring ============
    sentry_dsn: Optional[str] = Field(default=None)
    alert_email: Optional[str] = Field(default=None)
    smtp_server: Optional[str] = Field(default=None)
    smtp_port: int = Field(default=587)
    smtp_username: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    
    # ============ Security ============
    environment: str = Field(default="development")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    @validator("instagram_method")
    def validate_instagram_method(cls, v):
        """Ensure instagram_method is valid."""
        if v not in ["instagrapi", "make"]:
            raise ValueError("instagram_method must be 'instagrapi' or 'make'")
        return v
    
    @validator("instagram_enabled")
    def validate_instagram_credentials(cls, v, values):
        """Ensure Instagram credentials are provided if enabled."""
        if v:  # If Instagram is enabled
            method = values.get("instagram_method")
            if method == "instagrapi":
                if not values.get("instagram_username") or not values.get("instagram_password"):
                    raise ValueError(
                        "Instagram username and password required when using instagrapi method"
                    )
            elif method == "make":
                if not values.get("make_webhook_url"):
                    raise ValueError(
                        "Make.com webhook URL required when using make method"
                    )
        return v


# ============ RSS Feed Sources ============
RSS_FEEDS = {
    "geopolitics": [
        "https://www.csis.org/analysis/feed",
        "https://feeds.feedburner.com/ReutersWorldNews",
        "https://www.defensenews.com/arc/outboundfeeds/rss/",
        "https://www.nato.int/cps/en/natohq/news.rss",
    ],
    "finance": [
        "https://feeds.a.dj.com/rss/RSSWorldNews.xml",  # WSJ
        "https://www.ft.com/rss/world",  # Financial Times
        "https://www.reuters.com/finance",
    ],
    "cyber": [
        "https://www.darkreading.com/rss.xml",
        "https://www.bleepingcomputer.com/feed/",
        "https://threatpost.com/feed/",
        "https://www.csoonline.com/feed",
    ],
    "defense": [
        "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx",
        "https://www.janes.com/feeds/defence-news",
    ],
}

# ============ Government Portals ============
GOV_PORTALS = [
    {
        "name": "US Department of Defense",
        "url": "https://www.defense.gov/News/Releases/",
        "category": "defense",
    },
    {
        "name": "EU Commission Press Releases",
        "url": "https://ec.europa.eu/commission/presscorner/home/en",
        "category": "geopolitics",
    },
    {
        "name": "NATO Newsroom",
        "url": "https://www.nato.int/cps/en/natohq/news.htm",
        "category": "defense",
    },
]

# ============ Relevance Keywords by Category ============
RELEVANCE_KEYWORDS = {
    "geopolitics": [
        "sovereignty", "multilateral", "bilateral", "treaty", "sanctions",
        "diplomatic", "territorial", "strategic partnership", "alliance",
        "geopolitical", "foreign policy", "international relations",
    ],
    "defense": [
        "kinetic", "military", "defense", "armed forces", "weapons system",
        "deterrence", "force projection", "strategic assets", "NATO",
        "joint exercises", "combat", "operations", "security cooperation",
    ],
    "cyber": [
        "APT", "threat actor", "vulnerability", "cyber attack", "malware",
        "ransomware", "threat landscape", "attribution", "cyber espionage",
        "zero-day", "intrusion", "breach", "cybersecurity",
    ],
    "finance": [
        "fiscal", "monetary policy", "sovereign debt", "liquidity",
        "central bank", "interest rate", "inflation", "GDP", "bond yield",
        "market volatility", "financial stability", "economic indicator",
    ],
}

# ============ Prohibited Sensational Terms ============
# These will be filtered out or replaced during content analysis
PROHIBITED_TERMS = [
    "shocking", "amazing", "incredible", "unbelievable", "stunning",
    "mind-blowing", "crazy", "insane", "epic", "game-changer",
]

# ============ Institutional Terminology Mapping ============
# Raw term -> Professional replacement
TERMINOLOGY_MAP = {
    "war": "kinetic operations",
    "attack": "offensive operation",
    "market crash": "significant market volatility",
    "hacker": "threat actor",
    "spy": "intelligence operative",
    "threat": "security vector",
    "explosion": "kinetic event",
    "killed": "neutralized",
}


def get_settings() -> Settings:
    """Load and validate settings from environment variables."""
    try:
        return Settings()
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        print("\n⚠️  Please ensure your .env file is properly configured.")
        print("📄 Copy .env.example to .env and add your API keys.\n")
        raise


# Global settings instance
settings = get_settings()
