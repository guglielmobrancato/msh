"""
AI Analysis Module
Transforms raw news content into institutional-grade intelligence reports using Gemini API.
"""

import google.generativeai as genai
import os
import re
from typing import Dict, Optional
from pathlib import Path

from config import settings, TERMINOLOGY_MAP, PROHIBITED_TERMS


# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)


def load_system_prompt() -> str:
    """Load the institutional writer system prompt from file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "institutional_writer.txt"
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def analyze_with_gemini(
    raw_content: str,
    category: str,
    source_url: str = None,
    source_name: str = None,
) -> Dict[str, any]:
    """
    Transform raw news into institutional intelligence analysis using Gemini.
    
    Args:
        raw_content: Raw article text
        category: Article category (geopolitics, defense, cyber, finance)
        source_url: Source URL for citation
        source_name: Source name for citation
    
    Returns:
        Dictionary containing:
        - title: Article title
        - content: Full analysis (1500-3000 words)
        - summary: Executive summary
        - seo_description: Meta description
        - keywords: List of keywords
        - entities: Dict of entities (countries, organizations, technologies)
        - instagram_summary: Bullet points for Instagram
        - word_count: Actual word count
    """
    print(f"🤖 Analyzing content with Gemini AI (category: {category})...")
    
    # Load system prompt
    system_prompt = load_system_prompt()
    
    # Construct the full prompt
    user_prompt = f"""
Category: {category.upper()}
Source: {source_name or 'Unknown'}
URL: {source_url or 'N/A'}

Raw Content:
{raw_content}

---

Generate a complete intelligence analysis following the institutional writing guidelines.
Ensure the article is between 1500-3000 words and includes all required metadata.
"""
    
    try:
        # Use Gemini 2.0 Flash for analysis
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            system_instruction=system_prompt,
        )
        
        # Generate content
        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,  # Lower temperature for more consistent, professional output
                max_output_tokens=8000,  # Allow for long-form content
            ),
        )
        
        # Extract text
        full_response = response.text
        
        # Parse the response
        result = parse_gemini_response(full_response)
        
        print(f"✅ Generated {result['word_count']} word analysis")
        return result
        
    except Exception as e:
        print(f"❌ Error analyzing with Gemini: {e}")
        raise


def parse_gemini_response(response_text: str) -> Dict[str, any]:
    """
    Parse Gemini's response to extract article and metadata.
    
    Args:
        response_text: Full response from Gemini
    
    Returns:
        Dictionary with parsed components
    """
    # Split article content from metadata
    if "---METADATA---" in response_text:
        article_content, metadata_section = response_text.split("---METADATA---", 1)
        metadata_section = metadata_section.split("---END_METADATA---")[0]
    else:
        # Fallback if metadata section is missing
        print("⚠️  Warning: Metadata section not found in Gemini response")
        article_content = response_text
        metadata_section = ""
    
    # Extract title (first line or first heading)
    title_match = re.search(r'^#\s+(.+)$', article_content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        # Remove the title from content
        article_content = article_content.replace(title_match.group(0), '', 1).strip()
    else:
        # Fallback: use first line as title
        lines = article_content.split('\n')
        title = lines[0].strip() if lines else "Untitled Intelligence Report"
        article_content = '\n'.join(lines[1:]).strip()
    
    # Extract executive summary (first section after title)
    summary_match = re.search(
        r'(?:EXECUTIVE SUMMARY|Executive Summary)(.*?)(?=\n#{1,2}\s|\n[A-Z]{2,}|$)',
        article_content,
        re.DOTALL | re.IGNORECASE
    )
    if summary_match:
        summary = summary_match.group(1).strip()
        # Clean up markdown
        summary = re.sub(r'\*\*|__', '', summary)
        summary = summary[:500]  # Limit to 500 chars
    else:
        # Fallback: use first paragraph
        paragraphs = [p for p in article_content.split('\n\n') if p.strip()]
        summary = paragraphs[0][:500] if paragraphs else ""
    
    # Parse metadata section
    metadata = {}
    if metadata_section:
        # SEO Description
        seo_match = re.search(r'SEO_DESCRIPTION:\s*(.+)', metadata_section)
        metadata['seo_description'] = seo_match.group(1).strip() if seo_match else ""
        
        # Keywords
        keywords_match = re.search(r'KEYWORDS:\s*\[(.+?)\]', metadata_section)
        if keywords_match:
            keywords_str = keywords_match.group(1)
            metadata['keywords'] = [k.strip() for k in keywords_str.split(',')]
        else:
            metadata['keywords'] = []
        
        # Entities (JSON format)
        entities_match = re.search(r'ENTITIES:\s*(\{.+?\})', metadata_section, re.DOTALL)
        if entities_match:
            import json
            try:
                metadata['entities'] = json.loads(entities_match.group(1))
            except:
                metadata['entities'] = {}
        else:
            metadata['entities'] = {}
        
        # Category
        category_match = re.search(r'CATEGORY:\s*(.+)', metadata_section)
        metadata['category'] = category_match.group(1).strip() if category_match else "Geopolitics"
        
        # Instagram Summary
        instagram_match = re.search(
            r'INSTAGRAM_SUMMARY:\s*(.+?)(?=\n[A-Z_]+:|$)',
            metadata_section,
            re.DOTALL
        )
        if instagram_match:
            metadata['instagram_summary'] = instagram_match.group(1).strip()
        else:
            metadata['instagram_summary'] = summary[:300]
    else:
        # Fallback metadata
        metadata = {
            'seo_description': summary[:160],
            'keywords': [],
            'entities': {},
            'category': 'Geopolitics',
            'instagram_summary': summary[:300],
        }
    
    # Calculate word count
    word_count = len(article_content.split())
    
    return {
        'title': title,
        'content': article_content,
        'summary': summary,
        'seo_description': metadata['seo_description'],
        'keywords': metadata['keywords'],
        'entities': metadata['entities'],
        'instagram_summary': metadata['instagram_summary'],
        'word_count': word_count,
    }


def generate_metadata(content: str, title: str) -> Dict[str, any]:
    """
    Fallback function to generate basic metadata if Gemini doesn't provide it.
    
    Args:
        content: Article content
        title: Article title
    
    Returns:
        Dictionary with basic metadata
    """
    # Extract first paragraph as summary
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    summary = paragraphs[0][:500] if paragraphs else title
    
    # Simple keyword extraction (top words, excluding common words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    words = re.findall(r'\b[a-z]{4,}\b', content.lower())
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    keywords = sorted(word_freq, key=word_freq.get, reverse=True)[:10]
    
    return {
        'summary': summary,
        'seo_description': summary[:160],
        'keywords': keywords,
        'entities': {},
        'instagram_summary': summary[:300],
    }


def create_instagram_summary(article_text: str, max_length: int = 400) -> str:
    """
    Extract key points from article for Instagram caption.
    
    Args:
        article_text: Full article text
        max_length: Maximum length of summary
    
    Returns:
        Bullet-point Instagram summary
    """
    print("📸 Creating Instagram summary...")
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
Extract 3-5 key points from this intelligence analysis for an Instagram post.

Requirements:
- Use bullet points (• symbol)
- Data-driven, objective statements
- No emojis, no sensationalism
- Technical terminology maintained
- Each point: 1-2 sentences max
- Total length: under {max_length} characters

Article excerpt:
{article_text[:2000]}

Output only the bullet points, nothing else.
"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=500,
            ),
        )
        
        summary = response.text.strip()
        print(f"✅ Instagram summary created")
        return summary
        
    except Exception as e:
        print(f"⚠️  Error creating Instagram summary: {e}")
        # Fallback: use first few sentences
        sentences = article_text.split('.')[:3]
        return '\n'.join([f"• {s.strip()}" for s in sentences if s.strip()])[:max_length]


def validate_institutional_tone(text: str) -> Dict[str, any]:
    """
    Validate that text maintains institutional tone (no prohibited terms).
    
    Args:
        text: Text to validate
    
    Returns:
        Dictionary with validation results
    """
    issues = []
    
    text_lower = text.lower()
    
    # Check for prohibited sensational terms
    for term in PROHIBITED_TERMS:
        if term.lower() in text_lower:
            issues.append(f"Found prohibited term: '{term}'")
    
    # Check for informal language patterns
    informal_patterns = [
        r'\bOMG\b',
        r'\bwow\b',
        r'!!!',
        r'😀|😎|🔥',  # Emojis
    ]
    
    for pattern in informal_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"Found informal language pattern: {pattern}")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
    }
