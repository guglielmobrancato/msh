"""
Publishing Module
Handles automated publishing to Strapi CMS and queuing system.
"""

import requests
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session

from config import settings
from models.schemas import Article, PublishPlatform, PublishStatus


def publish_to_strapi(article: Article) -> Dict[str, any]:
    """
    Publish article to Strapi CMS via REST API.
    
    Args:
        article: Article object from database
    
    Returns:
        Response data from Strapi
    """
    print(f"📤 Publishing to Strapi: {article.title[:50]}...")
    
    if not settings.strapi_api_token or settings.strapi_api_token == "your_strapi_api_token_here":
        print("⚠️  Strapi API token not configured")
        return {"error": "Strapi not configured"}
    
    # Prepare payload
    payload = {
        "data": {
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "category": article.category.value,
            "source_url": article.source_url,
            "word_count": article.word_count,
            "publishedAt": datetime.utcnow().isoformat(),
        }
    }
    
    # API headers
    headers = {
        "Authorization": f"Bearer {settings.strapi_api_token}",
        "Content-Type": "application/json",
    }
    
    try:
        # POST to Strapi
        response = requests.post(
            f"{settings.strapi_url}/api/articles",
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Published to Strapi (ID: {data.get('data', {}).get('id', 'unknown')})")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error publishing to Strapi: {e}")
        raise


def schedule_publication(
    db: Session,
    article_id: int,
    platform: PublishPlatform,
    scheduled_time: datetime = None,
) -> None:
    """
    Add article to publishing queue.
    
    Args:
        db: Database session
        article_id: Article ID
        platform: Target platform
        scheduled_time: When to publish (None = immediate)
    """
    from modules.database import add_to_publish_queue
    
    add_to_publish_queue(
        db=db,
        article_id=article_id,
        platform=platform,
        scheduled_time=scheduled_time,
    )


def process_publish_queue(db: Session) -> None:
    """
    Process pending publications from the queue.
    
    Args:
        db: Database session
    """
    from modules.database import get_pending_publications, update_publish_status, mark_article_published
    
    print("\n" + "="*60)
    print("📋 PROCESSING PUBLISH QUEUE")
    print("="*60 + "\n")
    
    # Get pending publications
    pending = get_pending_publications(db)
    
    if not pending:
        print("✅ No pending publications")
        return
    
    print(f"Found {len(pending)} pending publications")
    
    for queue_entry in pending:
        article = db.query(Article).filter(Article.id == queue_entry.article_id).first()
        
        if not article:
            print(f"⚠️  Article {queue_entry.article_id} not found, skipping")
            continue
        
        print(f"\n→ Publishing: {article.title[:50]}...")
        print(f"  Platform: {queue_entry.platform.value}")
        
        try:
            # Update status to processing
            update_publish_status(
                db=db,
                queue_id=queue_entry.id,
                status=PublishStatus.PROCESSING,
            )
            
            # Publish based on platform
            if queue_entry.platform == PublishPlatform.STRAPI:
                result = publish_to_strapi(article)
                
                # Update status to completed
                update_publish_status(
                    db=db,
                    queue_id=queue_entry.id,
                    status=PublishStatus.COMPLETED,
                    platform_data=result,
                )
                
                # Mark article as published
                mark_article_published(db=db, article_id=article.id)
                
            elif queue_entry.platform == PublishPlatform.INSTAGRAM:
                # Instagram publishing handled by instagram module
                from modules.instagram import post_to_instagram
                
                # Get metadata
                metadata = article.metadata[0] if article.metadata else None
                
                result = post_to_instagram(
                    article=article,
                    metadata=metadata,
                )
                
                # Update status
                update_publish_status(
                    db=db,
                    queue_id=queue_entry.id,
                    status=PublishStatus.COMPLETED,
                    platform_data=result,
                )
            
            print(f"  ✅ Published successfully")
            
        except Exception as e:
            print(f"  ❌ Error publishing: {e}")
            
            # Update status to failed
            update_publish_status(
                db=db,
                queue_id=queue_entry.id,
                status=PublishStatus.FAILED,
                error_message=str(e),
            )
    
    print("\n" + "="*60)
    print(f"✅ Queue processing complete")
    print("="*60 + "\n")


def create_seo_metadata(article: Article, metadata) -> Dict[str, str]:
    """
    Generate SEO-optimized metadata for web publishing.
    
    Args:
        article: Article object
        metadata: Metadata object
    
    Returns:
        Dictionary with SEO metadata
    """
    return {
        "title": article.title,
        "description": metadata.seo_description if metadata else article.summary[:160],
        "keywords": ", ".join(metadata.keywords) if metadata and metadata.keywords else "",
        "author": "Ancile AI",
        "og:type": "article",
        "og:title": article.title,
        "og:description": metadata.seo_description if metadata else article.summary[:160],
        "article:published_time": article.published_at.isoformat() if article.published_at else "",
        "article:section": article.category.value,
    }
