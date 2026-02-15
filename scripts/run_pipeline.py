"""
Main Intelligence Pipeline
Orchestrates the complete autonomous content pipeline:
Ingest → Analyze → Publish → Instagram
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.ingestion import fetch_all_sources
from modules.analysis import analyze_with_gemini, create_instagram_summary
from modules.database import get_db, save_article, save_metadata, is_duplicate
from modules.publishing import publish_to_strapi, process_publish_queue
from modules.instagram import post_to_instagram
from models.schemas import ArticleCategory, PublishPlatform
from config import settings


def run_pipeline(dry_run: bool = False, max_articles: int = None):
    """
    Main pipeline execution.
    
    Args:
        dry_run: If True, don't actually publish (test mode)
        max_articles: Maximum articles to process (overrides config)
    """
    start_time = datetime.utcnow()
    
    print("\n" + "="*70)
    print("🛡️  ANCILE AI - STRATEGIC INTELLIGENCE PIPELINE")
    print("="*70)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Mode: {'DRY RUN (Test)' if dry_run else 'PRODUCTION'}")
    print("="*70 + "\n")
    
    max_articles = max_articles or settings.max_articles_per_run
    
    # STAGE 1: INGESTION
    print("📥 STAGE 1: CONTENT INGESTION")
    print("-" * 70)
    raw_articles = fetch_all_sources(hours_lookback=24)
    
    if not raw_articles:
        print("\n⚠️  No articles found. Pipeline complete.\n")
        return
    
    # Limit to max articles
    articles_to_process = raw_articles[:max_articles]
    print(f"\n✅ Processing top {len(articles_to_process)} articles\n")
    
    # STAGE 2: ANALYSIS & DATABASE
    print("\n🤖 STAGE 2: AI ANALYSIS")
    print("-" * 70)
    
    processed_count = 0
    skipped_count = 0
    
    with get_db() as db:
        for idx, raw_article in enumerate(articles_to_process, 1):
            print(f"\n[{idx}/{len(articles_to_process)}] Processing: {raw_article.title[:60]}...")
            
            # Check for duplicates
            if is_duplicate(db, raw_article.url, raw_article.content):
                print("  ⏭️  Skipped (duplicate)")
                skipped_count += 1
                continue
            
            try:
                # Analyze with Gemini
                analysis = analyze_with_gemini(
                    raw_content=raw_article.content,
                    category=raw_article.category.value,
                    source_url=raw_article.url,
                    source_name=raw_article.source,
                )
                
                # Validate word count
                if analysis['word_count'] < settings.article_min_words:
                    print(f"  ⚠️  Skipped (too short: {analysis['word_count']} words)")
                    skipped_count += 1
                    continue
                
                # Save to database
                article = save_article(
                    db=db,
                    title=analysis['title'],
                    content=analysis['content'],
                    summary=analysis['summary'],
                    category=raw_article.category,
                    source_url=raw_article.url,
                    source_name=raw_article.source,
                    raw_content=raw_article.content,
                    word_count=analysis['word_count'],
                    relevance_score=raw_article.relevance_score,
                )
                
                # Save metadata
                save_metadata(
                    db=db,
                    article_id=article.id,
                    tags=analysis['keywords'][:5] if analysis['keywords'] else [],
                    keywords=analysis['keywords'],
                    seo_description=analysis['seo_description'],
                    entities=analysis['entities'],
                    instagram_summary=analysis['instagram_summary'],
                )
                
                print(f"  ✅ Analyzed & saved (Article ID: {article.id})")
                processed_count += 1
                
                # STAGE 3: PUBLISHING
                if not dry_run:
                    print("\n  📤 Publishing...")
                    
                    # Publish to Strapi
                    try:
                        publish_to_strapi(article)
                        
                        # Mark as published
                        from modules.database import mark_article_published
                        mark_article_published(db, article.id)
                        
                    except Exception as e:
                        print(f"  ⚠️  Strapi publish failed: {e}")
                    
                    # Instagram automation
                    if settings.instagram_enabled:
                        try:
                            metadata = article.metadata[0] if article.metadata else None
                            post_to_instagram(article, metadata)
                        except Exception as e:
                            print(f"  ⚠️  Instagram post failed: {e}")
                else:
                    print("  ℹ️  DRY RUN - Skipping publication")
                
            except Exception as e:
                print(f"  ❌ Error processing article: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # SUMMARY
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("📊 PIPELINE SUMMARY")
    print("="*70)
    print(f"✅ Processed: {processed_count} articles")
    print(f"⏭️  Skipped: {skipped_count} articles (duplicates or low quality)")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"🏁 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No articles were published")
    
    print("="*70 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ancile AI - Strategic Intelligence Pipeline"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - analyze but don't publish"
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        help="Maximum articles to process (overrides config)"
    )
    
    args = parser.parse_args()
    
    try:
        run_pipeline(
            dry_run=args.dry_run,
            max_articles=args.max_articles,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
