#!/usr/bin/env python3
"""Generate a daily US bridal/women fashion trend blog post with Gemini.

Outputs:
- public/blog/<slug>.md
- public/blog/index.json (latest 30 posts metadata)
- public/blog/images/<slug>.png (Gemini generated cover image when available)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo

import feedparser
import requests

try:
    from google import genai
    from google.genai import types
except Exception as exc:  # pragma: no cover
    raise RuntimeError("google-genai package is required") from exc

ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "public" / "blog"
IMAGE_DIR = BLOG_DIR / "images"
INDEX_PATH = BLOG_DIR / "index.json"

TEXT_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"
MAX_NEWS = 24
SELECTED_NEWS = 10
MIN_WORDS = 800
MAX_WORDS = 1400
HARD_MAX_WORDS = MAX_WORDS + 2000

CONTENT_TYPES = [
    "Trend report",
    "Style inspiration",
    "Event outfit",
    "Bridal style",
    "Bachelorette",
    "Bridal shower",
    "Wedding guest",
    "Aesthetic trend",
]

SEARCH_QUERIES = [
    "bridal fashion trend United States",
    "wedding guest dresses trend US",
    "bridal shower outfit ideas USA",
    "bachelorette style trend tiktok",
    "pinterest bridal trend United States",
    "celebrity bridal look trend",
    "fashion week wedding style US",
    "rehearsal dinner outfit ideas USA",
    "hamptons wedding guest fashion",
    "new york bachelorette outfit trend",
]


@dataclass
class Article:
    title: str
    url: str
    source: str
    published: str


def get_api_key() -> str:
    key = (
        os.environ.get("GEMINI_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("VITE_GEMINI_API_KEY")
    )
    if not key:
        raise ValueError("GEMINI_KEY (or GEMINI_API_KEY) is required.")
    return key


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        target = parse_qs(parsed.query).get("url", [None])[0]
        if target:
            return clean_url(target)

    if not parsed.query:
        return url

    keep: list[tuple[str, str]] = []
    for key, values in parse_qs(parsed.query, keep_blank_values=True).items():
        low = key.lower()
        if low.startswith("utm") or low in {"oc", "ved", "usg", "ei", "sa", "source"}:
            continue
        for value in values:
            keep.append((key, value))

    query = urlencode(keep, doseq=True)
    return urlunparse(parsed._replace(query=query, fragment=""))


def fetch_us_fashion_news(limit: int = MAX_NEWS) -> list[Article]:
    feeds = [
        f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        for query in SEARCH_QUERIES
    ]

    seen: set[str] = set()
    articles: list[Article] = []

    with requests.Session() as session:
        for feed in feeds:
            parsed = feedparser.parse(feed)
            for entry in parsed.entries:
                link = getattr(entry, "link", "").strip()
                title = getattr(entry, "title", "").strip()
                if not link or not title or link in seen:
                    continue
                seen.add(link)

                final_url = link
                try:
                    resp = session.get(link, allow_redirects=True, timeout=10, stream=True)
                    resp.raise_for_status()
                    final_url = resp.url or link
                    resp.close()
                except requests.RequestException:
                    pass

                source = "Unknown"
                if hasattr(entry, "source") and isinstance(entry.source, dict):
                    source = entry.source.get("title") or "Unknown"

                articles.append(
                    Article(
                        title=title,
                        url=clean_url(final_url),
                        source=source,
                        published=getattr(entry, "published", "") or "",
                    )
                )

                if len(articles) >= limit:
                    return articles

    return articles


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON found in Gemini output")
    return json.loads(cleaned[start : end + 1])


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", value.lower()).strip("-")


def _normalize_url_for_match(url: str) -> str:
    parsed = urlparse(clean_url(url))
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{netloc}{path}{query}"


def _normalize_title_for_match(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def _resolve_source_url(
    raw_url: str,
    source_title: str,
    fallback_url: str,
    allowed_urls: set[str],
    canonical_url_map: dict[str, str],
    title_to_url: dict[str, str],
) -> str:
    source_url = clean_url(raw_url.strip())
    if source_url in allowed_urls:
        return source_url

    if source_url:
        normalized = _normalize_url_for_match(source_url)
        matched = canonical_url_map.get(normalized)
        if matched:
            return matched

    normalized_title = _normalize_title_for_match(source_title)
    if normalized_title and normalized_title in title_to_url:
        return title_to_url[normalized_title]

    return fallback_url


def _pick_content_type(date_slug: str) -> str:
    # deterministic rotation based on date for predictable daily variety
    ordinal = sum(ord(ch) for ch in date_slug)
    return CONTENT_TYPES[ordinal % len(CONTENT_TYPES)]


def _truncate_words(text: str, max_words: int) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if max_words <= 0 or not cleaned:
        return ""
    words = cleaned.split(" ")
    if len(words) <= max_words:
        return cleaned
    return " ".join(words[:max_words]).rstrip(" ,;:-") + "..."


def build_blog_payload(client: genai.Client, articles: list[Article], date_str: str) -> dict[str, Any]:
    source_lines = "\n".join([f"- {a.title} | {a.source} | {a.url}" for a in articles])

    prompt = f"""
SYSTEM ROLE:
You are an autonomous SEO Wedding Content Strategist for ZuzuMood (USA wedding market).
You research, analyze trends, and generate a fully optimized blog post ready for GitHub markdown publishing.

Date: {date_str}
STEP 1: Research Phase (Mandatory)
- Use API-based live research from the provided source list to analyze:
  - Google Trends (USA region)
  - Etsy USA search trends
  - Pinterest wedding trends
  - Long-tail keyword variations
- Primary categories to prioritize:
  - Bridal Gifts
  - Bridesmaid Proposal Gifts
  - Mother of the Bride Gifts
  - Wedding Morning Gifts
- Extract exactly:
  - 5 high-volume keywords
  - 5 long-tail keywords
  - 3 trending angles

STEP 2: Content Creation Rules
- Language: American English
- Target Market: United States
- Tone: Luxury wedding consultant, emotionally intelligent, boutique-style
- Never mention AI.
- Subtly integrate brand philosophy: "The Universe Always Says Yes" to intentional love and meaningful preparation.
- Naturally integrate ZuzuMood minimalist design, clean typography, premium aesthetic.

STEP 3: Return ONLY strict JSON with this schema:
{{
  "title": "SEO optimized blog title, max 65 chars",
  "metaDescription": "150-160 chars",
  "slug": "seo-friendly-url-slug",
  "tags": ["Bridal Gifts", "Bridesmaid Proposal", "Mother of the Bride", "Wedding Gifts"],
  "openingHook": "150-200 words emotional hook paragraph",
  "highVolumeKeywords": ["5 keywords"],
  "longTailKeywords": ["5 keywords"],
  "trendingAngles": ["3 trend angles"],
  "h2Sections": [
    {{
      "heading": "H2 heading",
      "content": "section content",
      "h3Subsections": [
        {{"title": "H3 heading", "content": "subsection content"}}
      ]
    }}
  ],
  "finalThoughts": "emotional closing paragraph",
  "callToAction": "encourage reader to explore Etsy shop",
  "pinterestPinDescription": "2-3 SEO optimized sentences",
  "tiktokHook": "1 emotionally powerful sentence under 15 words",
  "heroPrompt": "English image prompt, no text in image",
  "imageSuggestions": [
    {{
      "description": "image description",
      "altText": "high-volume USA wedding keyword optimized alt text"
    }}
  ]
}}

Critical constraints:
- h2Sections length 3-5.
- each h2 section must include at least one h3 subsection.
- imageSuggestions length 3-5.
- Keywords must be natural; avoid keyword stuffing.
- No AI mentions.
- Content must be 100% English and US-focused.
- CTA must include this exact URL: https://www.etsy.com/shop/ZuzuMood

Sources:
{source_lines}
"""

    resp = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.45),
    )

    payload = _extract_json((resp.text or "").strip())
    payload = enforce_payload_rules(payload, articles, date_str)
    return payload


def _sanitize_list(value: Any, min_len: int, max_len: int, fallback_prefix: str) -> list[str]:
    items = value if isinstance(value, list) else []
    cleaned = [_truncate_words(str(item).strip(), 12) for item in items if str(item).strip()]
    cleaned = [item for item in cleaned if item]
    while len(cleaned) < min_len:
        cleaned.append(f"{fallback_prefix} {len(cleaned) + 1}")
    return cleaned[:max_len]


def _looks_non_english(value: str) -> bool:
    lowered = (value or "").lower()
    turkish_markers = ["ş", "ğ", "ı", "ç", "ö", "ü", "moda", "gelin", "trendleri", "abd"]
    return any(marker in lowered for marker in turkish_markers)


def enforce_payload_rules(payload: dict[str, Any], articles: list[Article], date_slug: str) -> dict[str, Any]:
    allowed_urls = {clean_url(a.url) for a in articles}
    canonical_url_map = {_normalize_url_for_match(url): url for url in allowed_urls}
    title_to_url = {
        _normalize_title_for_match(a.title): clean_url(a.url)
        for a in articles
        if _normalize_title_for_match(a.title)
    }
    fallback_url = clean_url(articles[0].url)

    title = str(payload.get("title", "")).strip() or "US Bridal Trend Report"
    if _looks_non_english(title):
        title = "USA Wedding Gift Trends Brides Are Shopping Right Now"
    payload["title"] = title[:65]

    meta_description = str(payload.get("metaDescription", "")).strip()
    if not meta_description or _looks_non_english(meta_description):
        meta_description = (
            "Discover USA wedding gift trends for bridal parties, mothers, and wedding mornings with"
            " elegant, intentional styling guidance from ZuzuMood."
        )
    payload["metaDescription"] = _truncate_words(meta_description, 25)[:160]

    slug = str(payload.get("slug", "")).strip() or f"{date_slug}-us-bridal-fashion-trends"
    payload["slug"] = _slugify(slug)

    payload["tags"] = [
        "Bridal Gifts",
        "Bridesmaid Proposal",
        "Mother of the Bride",
        "Wedding Gifts",
    ]

    hook = _truncate_words(payload.get("openingHook", ""), 170)
    if not hook or _looks_non_english(hook):
        hook = (
            "Planning a wedding in the United States now means making hundreds of emotional decisions while trying"
            " to keep every gift meaningful, personal, and visually beautiful. Brides are balancing timeless taste with"
            " trend-driven inspiration from Pinterest and Etsy, and many feel pressure to choose gifts that photograph well"
            " and carry real sentiment. The most confident wedding mornings start with intentional details: bridesmaid proposal"
            " pieces that feel personal, mother-of-the-bride gifts that honor legacy, and bridal keepsakes that look refined"
            " without feeling overdone. This guide translates current search behavior into clear styling direction so you can"
            " choose gifts with emotional value and boutique-level polish."
        )
    payload["openingHook"] = hook

    payload["highVolumeKeywords"] = _sanitize_list(payload.get("highVolumeKeywords", []), 5, 5, "bridal gifts usa")
    payload["longTailKeywords"] = _sanitize_list(payload.get("longTailKeywords", []), 5, 5, "bridal gift ideas")
    payload["trendingAngles"] = _sanitize_list(payload.get("trendingAngles", []), 3, 3, "wedding trend")

    sections = payload.get("h2Sections", [])
    if not isinstance(sections, list):
        sections = []
    if len(sections) < 3:
        raise ValueError("h2Sections must contain at least 3 entries")
    payload["h2Sections"] = sections[:5]

    for section in payload["h2Sections"]:
        if not isinstance(section, dict):
            continue
        section["heading"] = _truncate_words(section.get("heading", "Wedding Trend Insight"), 10)
        section["content"] = _truncate_words(section.get("content", ""), 140)
        h3 = section.get("h3Subsections", [])
        if not isinstance(h3, list) or not h3:
            h3 = [{"title": "How to apply this trend", "content": "Use this direction to build a meaningful wedding gift story with minimalist, premium details."}]
        cleaned_h3: list[dict[str, str]] = []
        for item in h3[:3]:
            if not isinstance(item, dict):
                continue
            cleaned_h3.append(
                {
                    "title": _truncate_words(item.get("title", "Wedding styling note"), 8),
                    "content": _truncate_words(item.get("content", ""), 80),
                }
            )
        if not cleaned_h3:
            cleaned_h3 = [{"title": "Wedding styling note", "content": "Choose details that feel emotionally intentional and visually clean."}]
        section["h3Subsections"] = cleaned_h3

    payload["finalThoughts"] = _truncate_words(payload.get("finalThoughts", ""), 90)
    if not payload["finalThoughts"]:
        payload["finalThoughts"] = (
            "Great wedding gifting is not about buying more, it is about choosing with purpose. "
            "When every piece reflects emotion and intention, the celebration feels elevated, personal, and unforgettable."
        )

    call_to_action = str(payload.get("callToAction", "")).strip()
    if "https://www.etsy.com/shop/ZuzuMood" not in call_to_action:
        call_to_action = (
            "Explore the ZuzuMood Etsy collection for minimalist wedding gifts crafted for intentional, meaningful celebration: "
            "https://www.etsy.com/shop/ZuzuMood"
        )
    payload["callToAction"] = call_to_action

    payload["pinterestPinDescription"] = _truncate_words(payload.get("pinterestPinDescription", ""), 60)
    if not payload["pinterestPinDescription"]:
        payload["pinterestPinDescription"] = (
            "USA brides are choosing intentional bridal gifts with minimalist luxury styling. "
            "Save this guide for bridesmaid proposals, mother-of-the-bride moments, and meaningful wedding morning details."
        )

    tiktok_hook = _truncate_words(payload.get("tiktokHook", ""), 14)
    if not tiktok_hook:
        tiktok_hook = "Your wedding gifts should feel as intentional as your vows."
    payload["tiktokHook"] = tiktok_hook

    image_suggestions = payload.get("imageSuggestions", [])
    if not isinstance(image_suggestions, list):
        image_suggestions = []
    cleaned_images: list[dict[str, str]] = []
    for suggestion in image_suggestions[:5]:
        if not isinstance(suggestion, dict):
            continue
        cleaned_images.append(
            {
                "description": _truncate_words(suggestion.get("description", "Wedding gift flatlay with premium minimalist styling"), 20),
                "altText": _truncate_words(suggestion.get("altText", "USA bridal gifts wedding morning gift ideas"), 20),
            }
        )
    while len(cleaned_images) < 3:
        idx = len(cleaned_images) + 1
        cleaned_images.append(
            {
                "description": f"Minimalist bridal gifting visual concept {idx}",
                "altText": f"USA bridal gifts trend inspired wedding image {idx}",
            }
        )
    payload["imageSuggestions"] = cleaned_images[:5]

    return payload

def generate_cover_image(client: genai.Client, prompt: str, output_path: Path) -> bool:
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="16:9"),
        ),
    )

    for candidate in response.candidates or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(inline.data)
                return True
    return False


def to_markdown(payload: dict[str, Any], date_iso: str, image_path: str) -> str:
    title = str(payload.get("title", "")).strip()
    meta_description = str(payload.get("metaDescription", "")).strip()
    opening_hook = str(payload.get("openingHook", "")).strip()
    sections = payload.get("h2Sections", [])

    lines = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"meta_description: {json.dumps(meta_description, ensure_ascii=False)}",
        f"slug: {json.dumps(str(payload.get('slug', '')), ensure_ascii=False)}",
        f"date: {date_iso}",
        f"tags: {json.dumps(payload.get('tags', []), ensure_ascii=False)}",
        f"description: {json.dumps(meta_description, ensure_ascii=False)}",
        f"image: {image_path}",
        f"highVolumeKeywords: {json.dumps(payload.get('highVolumeKeywords', []), ensure_ascii=False)}",
        f"longTailKeywords: {json.dumps(payload.get('longTailKeywords', []), ensure_ascii=False)}",
        f"trendingAngles: {json.dumps(payload.get('trendingAngles', []), ensure_ascii=False)}",
        "locale: en-US",
        "region: us",
        "category: wedding-gift-trends",
        "---",
        "",
        f"# {title}",
        "",
        opening_hook,
        "",
    ]

    for section in sections:
        lines.extend(
            [
                f"## {str(section.get('heading', '')).strip()}",
                "",
                str(section.get("content", "")).strip(),
                "",
            ]
        )
        for subsection in section.get("h3Subsections", []):
            lines.extend(
                [
                    f"### {str(subsection.get('title', '')).strip()}",
                    "",
                    str(subsection.get("content", "")).strip(),
                    "",
                ]
            )

    lines.extend(
        [
            "---",
            "",
            "## Image Suggestions",
            "",
            *[
                f"{idx}. {item.get('description', '').strip()}  \nALT Text: \"{item.get('altText', '').strip()}\""
                for idx, item in enumerate(payload.get("imageSuggestions", []), start=1)
            ],
            "",
            "---",
            "",
            "## Final Thoughts",
            "",
            str(payload.get("finalThoughts", "")).strip(),
            "",
            "---",
            "",
            "## Call to Action",
            "",
            str(payload.get("callToAction", "")).strip(),
            "",
            "---",
            "",
            "## Pinterest Pin Description",
            "",
            str(payload.get("pinterestPinDescription", "")).strip(),
            "",
            "---",
            "",
            "## TikTok Hook",
            "",
            str(payload.get("tiktokHook", "")).strip(),
        ]
    )

    markdown = "\n".join(lines).strip() + "\n"
    word_count = len(re.findall(r"\b\w+\b", markdown))
    if word_count < MIN_WORDS or word_count > HARD_MAX_WORDS:
        raise ValueError(f"Generated markdown word count out of expected range: {word_count}")
    return markdown

def update_index(slug: str, title: str, summary: str, date_iso: str, image_path: str) -> None:
    entries: list[dict[str, str]] = []
    if INDEX_PATH.exists():
        try:
            entries = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []

    english_only_entries: list[dict[str, str]] = []
    for entry in entries:
        title_value = str(entry.get("title", ""))
        summary_value = str(entry.get("summary", ""))
        if _looks_non_english(f"{title_value} {summary_value}"):
            continue
        english_only_entries.append(entry)

    entries = [entry for entry in english_only_entries if entry.get("slug") != slug]
    entries.append(
        {
            "slug": slug,
            "title": title,
            "summary": summary,
            "date": date_iso,
            "path": f"/blog/{slug}.md",
            "image": image_path,
        },
    )

    entries.sort(key=lambda item: str(item.get("date", "")), reverse=True)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(entries[:30], ensure_ascii=False, indent=2), encoding="utf-8")

def main() -> None:
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)

    texas_tz = ZoneInfo("America/Chicago")
    now_local = dt.datetime.now(texas_tz)
    now_utc = now_local.astimezone(dt.timezone.utc)
    date_slug = now_local.strftime("%Y-%m-%d")
    date_iso = now_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    articles = fetch_us_fashion_news()
    if not articles:
        raise RuntimeError("No US bridal/fashion news found from RSS feeds")

    payload = build_blog_payload(client, articles, date_slug)
    slug = payload.get("slug") or f"{date_slug}-us-bridal-fashion-trends"
    slug = _slugify(slug)

    image_rel = f"/blog/images/{slug}.png"
    image_out = IMAGE_DIR / f"{slug}.png"
    image_ok = False
    try:
        image_ok = generate_cover_image(client, str(payload.get("heroPrompt", "bridal fashion editorial")), image_out)
    except Exception:
        image_ok = False

    if not image_ok:
        image_rel = "/blog/images/default-fashion.svg"

    md = to_markdown(payload, date_iso, image_rel)
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BLOG_DIR / f"{slug}.md"
    out_path.write_text(md, encoding="utf-8")

    update_index(
        slug=slug,
        title=str(payload.get("title", slug)),
        summary=str(payload.get("metaDescription", "")),
        date_iso=date_iso,
        image_path=image_rel,
    )

    print(f"✅ Blog generated: {out_path.relative_to(ROOT)}")
    if image_ok:
        print(f"✅ Cover image generated: {image_out.relative_to(ROOT)}")
    else:
        print("⚠️ Cover image generation failed; fallback image used.")


if __name__ == "__main__":
    main()
