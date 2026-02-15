"""
Instagram Automation Module
Handles image generation and Instagram posting via Instagrapi or Make.com.
"""

import google.generativeai as genai
import requests
from PIL import Image
from io import BytesIO
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from config import settings
from models.schemas import Article, Metadata


# Configure Gemini for image generation
genai.configure(api_key=settings.gemini_api_key)


def generate_technical_infographic(
    article_summary: str,
    category: str,
    title: str,
) -> str:
    """
    Generate technical intelligence infographic using Gemini Imagen.
    
    Args:
        article_summary: Article summary for context
        category: Article category
        title: Article title
    
    Returns:
        Path to saved image file
    """
    print(f"🎨 Generating technical infographic for: {title[:50]}...")
    
    # Craft the image generation prompt
    prompt = f"""
Create a high-resolution technical intelligence infographic (1080x1080 pixels) for an intelligence analysis report.

Style requirements:
- Minimalist, dark mode aesthetic with dark blue/grey/black color scheme
- Clean, high-density typography suitable for intelligence briefings
- Resembling satellite imagery, military intelligence briefings, or geopolitical analysis maps
- No sensationalism, purely data-driven and technical visualization
- Professional, institutional appearance matching ACN, CSIS, or AISI publications
- Monochromatic with strategic accent colors for data points (electric blue, cyan, white)

Category: {category.upper()}
Title: {title}

Content Context:
{article_summary[:500]}

Visual elements to include:
- For GEOPOLITICS: World/regional maps with highlighted zones, diplomatic relationships, territorial markers
- For DEFENSE: Military asset deployments, force projection diagrams, strategic corridors
- For CYBER: Network topology diagrams, threat actor attribution maps, attack vector visualizations
- For FINANCE: Economic charts, market volatility graphs, sovereign debt indicators

Design aesthetic: Cold, technical, institutional, high-information density
Typography: Sans-serif, clean, military/intelligence briefing style
Layout: Grid-based, structured, with subtle geometric patterns

NO bright colors, NO cartoon elements, NO generic stock imagery
"""
    
    try:
        # Generate image using Imagen 3
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
        )
        
        # Save image
        output_dir = Path("generated_images")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intel_{category}_{timestamp}.png"
        filepath = output_dir / filename
        
        # Download and save image
        image_data = response.images[0]
        image_data.save(filepath)
        
        print(f"✅ Infographic saved: {filepath}")
        return str(filepath)
        
    except Exception as e:
        print(f"❌ Error generating infographic: {e}")
        print("⚠️  Falling back to text-based placeholder image...")
        
        # Fallback: Create a simple dark placeholder image with text
        return create_placeholder_image(title, category)


def create_placeholder_image(title: str, category: str) -> str:
    """
    Create a simple dark placeholder image when API fails.
    
    Args:
        title: Article title
        category: Category
    
    Returns:
        Path to placeholder image
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # Create dark image
    img = Image.new('RGB', (1080, 1080), color=(15, 20, 30))
    draw = ImageDraw.Draw(img)
    
    # Draw category badge
    draw.rectangle([(0, 0), (1080, 100)], fill=(30, 40, 60))
    
    # Add text (simplified - would need font file for production)
    # In production, use: font = ImageFont.truetype("arial.ttf", 40)
    text = f"{category.upper()}\n\nANCILE AI"
    
    # Save
    output_dir = Path("generated_images")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"placeholder_{timestamp}.png"
    img.save(filepath)
    
    return str(filepath)


def generate_instagram_caption(
    article: Article,
    metadata: Optional[Metadata] = None,
) -> str:
    """
    Generate professional Instagram caption with data-driven bullet points.
    
    Args:
        article: Article object
        metadata: Metadata object (optional)
    
    Returns:
        Instagram caption text
    """
    print(f"✍️  Generating Instagram caption...")
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
Create a professional Instagram caption for this intelligence analysis.

Requirements:
- 3-5 bullet points using • symbol
- Data-driven, objective, technical tone
- Use institutional terminology (kinetic operations, APT vectors, fiscal solvency, etc.)
- NO emojis, NO sensationalism, NO informal language
- Each point: 1-2 concise sentences with specific data when possible
- End with 12-15 professional hashtags

Article Title: {article.title}
Category: {article.category.value}
Summary: {article.summary[:500]}

Hashtag categories to use:
- Category-specific: #{article.category.value}
- General: #IntelligenceAnalysis #Geopolitics #GlobalSecurity #StrategicAnalysis
- Technical: #OSINT #ThreatIntelligence #DefenseAnalysis

Output the caption only, ready to post.
"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=800,
            ),
        )
        
        caption = response.text.strip()
        
        # Add source link if available
        if article.source_url:
            caption += f"\n\n🔗 Source: {article.source_url}"
        
        # Add branding
        caption += "\n\n---\n🛡️ Ancile AI | Strategic Intelligence Analysis"
        
        print(f"✅ Caption generated ({len(caption)} chars)")
        return caption
        
    except Exception as e:
        print(f"⚠️  Error generating caption: {e}")
        
        # Fallback caption
        caption = f"""• {article.title}

• Category: {article.category.value.upper()}
• Analysis available now

#IntelligenceAnalysis #{article.category.value} #Geopolitics #GlobalSecurity #OSINT #ThreatIntelligence #StrategicAnalysis #DefenseIntel #CyberSecurity #FinancialAnalysis

---
🛡️ Ancile AI | Strategic Intelligence Analysis
"""
        return caption


def post_to_instagram_instagrapi(image_path: str, caption: str) -> Dict[str, any]:
    """
    Post to Instagram using Instagrapi library.
    
    WARNING: This method may violate Instagram's Terms of Service.
    Use at your own risk. Recommended: Use Make.com instead.
    
    Args:
        image_path: Path to image file
        caption: Post caption
    
    Returns:
        Response data
    """
    print(f"📸 Posting to Instagram via Instagrapi...")
    
    if not settings.instagram_username or not settings.instagram_password:
        raise ValueError("Instagram credentials not configured")
    
    try:
        from instagrapi import Client
        
        cl = Client()
        cl.login(settings.instagram_username, settings.instagram_password)
        
        # Upload photo
        media = cl.photo_upload(
            image_path,
            caption=caption,
        )
        
        print(f"✅ Posted to Instagram (Media ID: {media.pk})")
        
        return {
            "method": "instagrapi",
            "media_id": str(media.pk),
            "success": True,
        }
        
    except Exception as e:
        print(f"❌ Error posting to Instagram: {e}")
        raise


def post_to_instagram_make(image_path: str, caption: str) -> Dict[str, any]:
    """
    Post to Instagram via Make.com webhook.
    
    This is the RECOMMENDED method as it complies with Instagram ToS.
    
    Args:
        image_path: Path to image file
        caption: Post caption
    
    Returns:
        Response data
    """
    print(f"📸 Posting to Instagram via Make.com webhook...")
    
    if not settings.make_webhook_url:
        raise ValueError("Make.com webhook URL not configured")
    
    try:
        # Upload image to a temporary hosting service or send as base64
        # For simplicity, we'll send the local path (Make.com workflow would need to fetch it)
        # In production, upload to S3/CloudFlare and send URL
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Encode as base64 to send via webhook
        import base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            "image_base64": image_base64,
            "caption": caption,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        response = requests.post(
            settings.make_webhook_url,
            json=payload,
            timeout=30,
        )
        
        response.raise_for_status()
        
        print(f"✅ Webhook triggered successfully")
        
        return {
            "method": "make_webhook",
            "response": response.json() if response.text else {},
            "success": True,
        }
        
    except Exception as e:
        print(f"❌ Error posting via Make.com: {e}")
        raise


def post_to_instagram(
    article: Article,
    metadata: Optional[Metadata] = None,
) -> Dict[str, any]:
    """
    Main Instagram posting function - routes to correct method.
    
    Args:
        article: Article object
        metadata: Metadata object
    
    Returns:
        Response data
    """
    if not settings.instagram_enabled:
        print("ℹ️  Instagram posting disabled in configuration")
        return {"success": False, "reason": "disabled"}
    
    print("\n" + "="*60)
    print("📸 INSTAGRAM AUTOMATION")
    print("="*60 + "\n")
    
    # Generate infographic
    image_path = generate_technical_infographic(
        article_summary=metadata.instagram_summary if metadata else article.summary,
        category=article.category.value,
        title=article.title,
    )
    
    # Generate caption
    caption = generate_instagram_caption(article, metadata)
    
    # Post to Instagram
    if settings.instagram_method == "instagrapi":
        print("📱 Method: Instagrapi (Python library)")
        result = post_to_instagram_instagrapi(image_path, caption)
    elif settings.instagram_method == "make":
        print("📱 Method: Make.com webhook")
        result = post_to_instagram_make(image_path, caption)
    else:
        raise ValueError(f"Unknown Instagram method: {settings.instagram_method}")
    
    print("\n" + "="*60)
    print("✅ Instagram automation complete")
    print("="*60 + "\n")
    
    return result
