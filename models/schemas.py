"""
Database Schemas and SQLAlchemy Models
Defines the PostgreSQL database structure for the intelligence archive.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, 
    ForeignKey, JSON, ARRAY, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum


Base = declarative_base()


class ArticleStatus(str, enum.Enum):
    """Article publication status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FAILED = "failed"


class ArticleCategory(str, enum.Enum):
    """Intelligence categories."""
    GEOPOLITICS = "geopolitics"
    DEFENSE = "defense"
    CYBER = "cyber"
    FINANCE = "finance"


class PublishPlatform(str, enum.Enum):
    """Publishing platforms."""
    STRAPI = "strapi"
    INSTAGRAM = "instagram"


class PublishStatus(str, enum.Enum):
    """Publishing queue status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Article(Base):
    """Main articles table - stores intelligence reports."""
    
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Categorization
    category = Column(SQLEnum(ArticleCategory), nullable=False, index=True)
    
    # Source tracking
    source_url = Column(Text, nullable=True)
    source_name = Column(String(200), nullable=True)
    raw_content = Column(Text, nullable=True)  # Original scraped content
    
    # Quality metrics
    word_count = Column(Integer, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    # Status
    status = Column(SQLEnum(ArticleStatus), default=ArticleStatus.DRAFT, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    metadata = relationship("Metadata", back_populates="article", cascade="all, delete-orphan")
    publish_queue = relationship("PublishQueue", back_populates="article", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', category={self.category})>"


class Metadata(Base):
    """Metadata table - tags, keywords, entities for searchable archive."""
    
    __tablename__ = "metadata"
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    
    # SEO and search
    tags = Column(ARRAY(String), nullable=True)  # ["Russia", "NATO", "Cybersecurity"]
    keywords = Column(ARRAY(String), nullable=True)  # ["APT28", "kinetic operations"]
    seo_description = Column(Text, nullable=True)  # Meta description for web
    
    # Entity extraction (stored as JSON)
    # Example: {"countries": ["USA", "China"], "organizations": ["NATO", "EU"], "technologies": ["AI", "Quantum"]}
    entities = Column(JSON, nullable=True)
    
    # Instagram-specific
    instagram_caption = Column(Text, nullable=True)
    instagram_hashtags = Column(ARRAY(String), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    article = relationship("Article", back_populates="metadata")
    
    def __repr__(self):
        return f"<Metadata(article_id={self.article_id}, tags={self.tags})>"


class PublishQueue(Base):
    """Publishing queue - schedules article distribution to platforms."""
    
    __tablename__ = "publish_queue"
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    
    # Platform config
    platform = Column(SQLEnum(PublishPlatform), nullable=False, index=True)
    status = Column(SQLEnum(PublishStatus), default=PublishStatus.PENDING, index=True)
    
    # Scheduling
    scheduled_time = Column(DateTime, nullable=True)
    published_time = Column(DateTime, nullable=True)
    
    # Error handling
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Platform-specific data (stored as JSON)
    # Example: {"strapi_id": 123, "instagram_post_id": "abc123"}
    platform_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    article = relationship("Article", back_populates="publish_queue")
    
    def __repr__(self):
        return f"<PublishQueue(id={self.id}, platform={self.platform}, status={self.status})>"


class SourceCache(Base):
    """Cache table to track processed sources and avoid duplicates."""
    
    __tablename__ = "source_cache"
    
    id = Column(Integer, primary_key=True)
    source_url = Column(String(500), unique=True, index=True, nullable=False)
    content_hash = Column(String(64), unique=True, index=True)  # SHA256 hash
    
    # Tracking
    first_seen = Column(DateTime, default=datetime.utcnow)
    processed = Column(DateTime, nullable=True)
    skipped = Column(Integer, default=0)  # Times skipped due to duplication
    
    def __repr__(self):
        return f"<SourceCache(url='{self.source_url[:50]}...', hash={self.content_hash[:8]})>"
