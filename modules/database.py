"""
Database Management Module
Handles database connections, session management, and CRUD operations.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
import hashlib

from config import settings
from models.schemas import Base, Article, Metadata, PublishQueue, SourceCache
from models.schemas import ArticleStatus, ArticleCategory, PublishPlatform, PublishStatus


# Create database engine
engine = create_engine(
    settings.database_url,
    poolclass=NullPool if settings.environment == "development" else None,
    echo=settings.environment == "development",  # Log SQL in dev mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize database - create all tables."""
    print("🔧 Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def drop_all_tables():
    """⚠️ WARNING: Drops all tables. Use only in development."""
    if settings.environment == "production":
        raise RuntimeError("Cannot drop tables in production environment!")
    print("⚠️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables dropped")


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def create_content_hash(content: str) -> str:
    """Create SHA256 hash of content for deduplication."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def is_duplicate(db: Session, url: str, content: str) -> bool:
    """Check if content already exists in database."""
    content_hash = create_content_hash(content)
    
    # Check by URL
    url_exists = db.query(SourceCache).filter(SourceCache.source_url == url).first()
    if url_exists:
        return True
    
    # Check by content hash
    hash_exists = db.query(SourceCache).filter(SourceCache.content_hash == content_hash).first()
    if hash_exists:
        return True
    
    return False


def save_article(
    db: Session,
    title: str,
    content: str,
    summary: str,
    category: ArticleCategory,
    source_url: str = None,
    source_name: str = None,
    raw_content: str = None,
    word_count: int = None,
    relevance_score: float = None,
) -> Article:
    """Save a new article to the database."""
    
    article = Article(
        title=title,
        content=content,
        summary=summary,
        category=category,
        source_url=source_url,
        source_name=source_name,
        raw_content=raw_content,
        word_count=word_count,
        relevance_score=relevance_score,
        status=ArticleStatus.DRAFT,
    )
    
    db.add(article)
    db.commit()
    db.refresh(article)
    
    # Add to source cache for deduplication
    if source_url and content:
        cache_entry = SourceCache(
            source_url=source_url,
            content_hash=create_content_hash(content),
        )
        db.add(cache_entry)
        db.commit()
    
    print(f"💾 Saved article: {title[:50]}... (ID: {article.id})")
    return article


def save_metadata(
    db: Session,
    article_id: int,
    tags: list = None,
    keywords: list = None,
    seo_description: str = None,
    entities: dict = None,
    instagram_caption: str = None,
    instagram_hashtags: list = None,
) -> Metadata:
    """Save metadata for an article."""
    
    metadata = Metadata(
        article_id=article_id,
        tags=tags,
        keywords=keywords,
        seo_description=seo_description,
        entities=entities,
        instagram_caption=instagram_caption,
        instagram_hashtags=instagram_hashtags,
    )
    
    db.add(metadata)
    db.commit()
    db.refresh(metadata)
    
    print(f"🏷️  Saved metadata for article ID: {article_id}")
    return metadata


def add_to_publish_queue(
    db: Session,
    article_id: int,
    platform: PublishPlatform,
    scheduled_time = None,
) -> PublishQueue:
    """Add article to publishing queue."""
    
    queue_entry = PublishQueue(
        article_id=article_id,
        platform=platform,
        status=PublishStatus.PENDING,
        scheduled_time=scheduled_time,
    )
    
    db.add(queue_entry)
    db.commit()
    db.refresh(queue_entry)
    
    print(f"📋 Added to {platform.value} publish queue: Article ID {article_id}")
    return queue_entry


def get_pending_publications(db: Session, platform: PublishPlatform = None):
    """Get all pending publications, optionally filtered by platform."""
    query = db.query(PublishQueue).filter(PublishQueue.status == PublishStatus.PENDING)
    
    if platform:
        query = query.filter(PublishQueue.platform == platform)
    
    return query.all()


def update_publish_status(
    db: Session,
    queue_id: int,
    status: PublishStatus,
    error_message: str = None,
    platform_data: dict = None,
):
    """Update publishing queue entry status."""
    
    queue_entry = db.query(PublishQueue).filter(PublishQueue.id == queue_id).first()
    if not queue_entry:
        raise ValueError(f"Queue entry {queue_id} not found")
    
    queue_entry.status = status
    
    if status == PublishStatus.COMPLETED:
        from datetime import datetime
        queue_entry.published_time = datetime.utcnow()
    
    if status == PublishStatus.FAILED:
        queue_entry.retry_count += 1
        queue_entry.error_message = error_message
    
    if platform_data:
        queue_entry.platform_data = platform_data
    
    db.commit()
    print(f"✏️  Updated publish queue {queue_id}: {status.value}")


def mark_article_published(db: Session, article_id: int):
    """Mark an article as published."""
    from datetime import datetime
    
    article = db.query(Article).filter(Article.id == article_id).first()
    if article:
        article.status = ArticleStatus.PUBLISHED
        article.published_at = datetime.utcnow()
        db.commit()
        print(f"✅ Marked article {article_id} as published")


def get_recent_articles(db: Session, limit: int = 10, category: ArticleCategory = None):
    """Get recent articles, optionally filtered by category."""
    query = db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED)
    
    if category:
        query = query.filter(Article.category == category)
    
    return query.order_by(Article.published_at.desc()).limit(limit).all()
