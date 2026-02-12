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
MIN_WORDS = 1500
MAX_WORDS = 2200
HARD_MAX_WORDS = MAX_WORDS + 400

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
    "bridesmaid proposal gifts USA",
    "bridal gifts ideas United States",
    "mother of the bride gift USA",
    "wedding morning gifts for bride",
    "maid of honor gift trend USA",
    "bridal shower gift ideas 2026",
    "personalized wedding gifts USA",
    "etsy bridesmaid proposal gifts",
    "minimalist wedding gift ideas",
    "luxury wedding keepsake gifts",
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


def _existing_slugs() -> set[str]:
    slugs: set[str] = set()
    if INDEX_PATH.exists():
        try:
            entries = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict):
                        slug = str(entry.get("slug", "")).strip()
                        if slug:
                            slugs.add(slug)
        except Exception:
            pass

    for md_file in BLOG_DIR.glob("*.md"):
        slugs.add(md_file.stem)
    return slugs


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
    existing_slugs = sorted(_existing_slugs())[-80:]
    existing_slug_lines = "\n".join([f"- {slug}" for slug in existing_slugs]) or "- none"

    prompt = f"""
SYSTEM ROLE
You are an autonomous SEO Wedding Content Strategist for ZuzuMood.

Your mission:
Generate high-traffic, conversion-focused blog posts for the USA wedding market and publish-ready markdown content for GitHub automation.

Primary goal:
Increase organic Google traffic and convert readers into Etsy customers.

Target audience:
USA brides, bridesmaids, maids of honor, mothers of the bride (age 23–40).

Language:
American English only.

STEP 1 — DAILY LIVE RESEARCH (MANDATORY)
Before writing anything:
1) Analyze Google Trends style signals from sources for USA only (last 30 days + rising intent) and extract:
- 5 rising keywords
- 5 breakout queries
- 3 seasonal angles

2) SERP intent analysis for top 3 trending keywords and classify intent mix.
ZuzuMood target: Commercial + Informational hybrid intent.

3) Topic selection rule:
Select ONE topic with rising momentum, category fit, and commercial potential.
Avoid duplicates with these existing slugs:
{existing_slug_lines}

STEP 2 — SEO STRATEGY REQUIREMENTS
- 1500-2200 words.
- Use primary keyword in title, first 100 words, one H2, and meta description.
- Include at least 5 long-tail variations.
- Include FAQ section with 3 SEO questions.
- Include list section with at least 10 specific ideas.
- Short scannable paragraphs.
- Never mention AI.
- Integrate ZuzuMood naturally, not salesy.
- Mention minimalist design, clean typography, premium aesthetic, and emotional keepsake value.
- Include this philosophy naturally once: “The Universe Always Says Yes”.
- CTA must include exact URL: https://www.etsy.com/shop/ZuzuMood

Return ONLY strict JSON with this schema:
{{
  "title": "<65 chars, include primary keyword and emotional/benefit trigger>",
  "metaDescription": "150-160 chars with primary keyword",
  "slug": "seo-friendly-slug",
  "primaryKeyword": "main keyword",
  "secondaryKeywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
  "intro": "Hook paragraph with keyword in first 100 words",
  "whyTrendRising": "Trend analysis with USA context",
  "usaTrendingNow": "Optional freshness section if momentum is high",
  "chooseGuide": "How to choose the perfect primary keyword item",
  "ideasHeading": "Numbered list section heading",
  "ideas": [
    {{"title": "idea title", "explanation": "mini explanation"}}
  ],
  "budgetGuide": "Optional budget guidance",
  "luxuryVsMinimalist": "Comparison section with subtle ZuzuMood positioning",
  "faq": [
    {{"question": "SEO question", "answer": "answer"}}
  ],
  "imageSuggestions": [
    {{"description": "image description", "altText": "SEO keyword phrase"}}
  ],
  "finalThoughts": "Closing paragraph",
  "callToAction": "Include exact Etsy URL",
  "pinterestPinDescription": "2-3 SEO-optimized sentences",
  "tiktokHook": "Under 15 words",
  "heroPrompt": "English image prompt, no text in image"
}}

Critical constraints:
- ideas length >= 10
- faq length exactly 3
- imageSuggestions length 3-5
- output must be 100% American English

Sources:
{source_lines}
"""

    resp = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.4),
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
    existing_slugs = _existing_slugs()

    title = str(payload.get("title", "")).strip() or "15 Best Bridesmaid Proposal Gifts for 2026"
    if _looks_non_english(title):
        title = "15 Best Bridesmaid Proposal Gifts for 2026"
    payload["title"] = title[:65]

    primary_keyword = str(payload.get("primaryKeyword", "")).strip() or "bridesmaid proposal gifts"
    if _looks_non_english(primary_keyword):
        primary_keyword = "bridesmaid proposal gifts"
    payload["primaryKeyword"] = primary_keyword

    meta_description = str(payload.get("metaDescription", "")).strip()
    if not meta_description or _looks_non_english(meta_description):
        meta_description = (
            f"Discover {primary_keyword} ideas for USA weddings with minimalist, meaningful picks for bridesmaids, mothers, and wedding morning moments."
        )
    payload["metaDescription"] = _truncate_words(meta_description, 26)[:160]

    slug = _slugify(str(payload.get("slug", "")).strip() or f"{date_slug}-{primary_keyword}")
    if slug in existing_slugs:
        slug = f"{slug}-{date_slug}"
    payload["slug"] = slug

    secondary = payload.get("secondaryKeywords", [])
    payload["secondaryKeywords"] = _sanitize_list(secondary, 5, 7, "wedding gift ideas")[:5]

    intro = _truncate_words(str(payload.get("intro", "")).strip(), 220)
    if not intro or _looks_non_english(intro):
        intro = (
            f"If you are searching for {primary_keyword}, you are not alone. Across the USA, brides are choosing gifts that feel personal, premium, and photo-ready while still practical for real wedding timelines. "
            "This guide breaks down what is trending, what converts into meaningful keepsakes, and how to choose pieces that bridesmaids and family members will actually use long after the wedding day."
        )
    payload["intro"] = intro

    payload["whyTrendRising"] = _truncate_words(str(payload.get("whyTrendRising", "")).strip(), 260) or (
        "Search demand is climbing because brides want personalized gifts that feel elevated without looking overdesigned. Etsy-style customization, social media unboxing moments, and wedding weekend content culture are pushing this category forward in the U.S. market."
    )

    payload["usaTrendingNow"] = _truncate_words(str(payload.get("usaTrendingNow", "")).strip(), 140)
    payload["chooseGuide"] = _truncate_words(str(payload.get("chooseGuide", "")).strip(), 240) or (
        "Choose by recipient role, event timing, and repeat-use value. Prioritize clean typography, neutral palettes, and customization options that make each gift look intentional in photos and feel genuinely personal in real life."
    )

    ideas_heading = str(payload.get("ideasHeading", "")).strip() or f"10 Best {primary_keyword.title()} Ideas"
    payload["ideasHeading"] = _truncate_words(ideas_heading, 12)

    ideas = payload.get("ideas", [])
    cleaned_ideas: list[dict[str, str]] = []
    if isinstance(ideas, list):
        for item in ideas:
            if not isinstance(item, dict):
                continue
            t = _truncate_words(str(item.get("title", "")).strip(), 10)
            e = _truncate_words(str(item.get("explanation", "")).strip(), 45)
            if t and e:
                cleaned_ideas.append({"title": t, "explanation": e})
    while len(cleaned_ideas) < 10:
        idx = len(cleaned_ideas) + 1
        cleaned_ideas.append(
            {
                "title": f"Idea {idx}: Personalized minimalist keepsake",
                "explanation": "Use premium materials, clean typography, and recipient-specific personalization so the gift feels elevated and wedding-photo ready.",
            }
        )
    payload["ideas"] = cleaned_ideas[:12]

    payload["budgetGuide"] = _truncate_words(str(payload.get("budgetGuide", "")).strip(), 160)
    payload["luxuryVsMinimalist"] = _truncate_words(str(payload.get("luxuryVsMinimalist", "")).strip(), 220) or (
        "Modern brides are choosing minimalist gifts with premium finishes over loud, overly themed products. This blend gives a luxury feel while staying timeless, giftable, and easy to style for wedding content."
    )

    faq = payload.get("faq", [])
    cleaned_faq: list[dict[str, str]] = []
    if isinstance(faq, list):
        for item in faq:
            if not isinstance(item, dict):
                continue
            q = _truncate_words(str(item.get("question", "")).strip(), 14)
            a = _truncate_words(str(item.get("answer", "")).strip(), 55)
            if q and a:
                cleaned_faq.append({"question": q, "answer": a})
    while len(cleaned_faq) < 3:
        n = len(cleaned_faq) + 1
        cleaned_faq.append(
            {
                "question": f"What are the best {primary_keyword} for USA weddings?",
                "answer": "Choose gifts that balance personalization, practical use, and visual consistency with your wedding palette.",
            }
        )
    payload["faq"] = cleaned_faq[:3]

    payload["finalThoughts"] = _truncate_words(str(payload.get("finalThoughts", "")).strip(), 90) or (
        "Great wedding gifting is intentional. When every detail reflects care, your celebration feels more personal, more memorable, and more aligned with the love story you are building."
    )

    call_to_action = str(payload.get("callToAction", "")).strip()
    if "https://www.etsy.com/shop/ZuzuMood" not in call_to_action:
        call_to_action = "Explore ZuzuMood's Etsy collection for minimalist wedding keepsakes: https://www.etsy.com/shop/ZuzuMood"
    payload["callToAction"] = call_to_action

    payload["pinterestPinDescription"] = _truncate_words(str(payload.get("pinterestPinDescription", "")).strip(), 70) or (
        "Looking for bridesmaid proposal gifts and wedding keepsakes that feel premium and personal? Save this USA-focused guide for minimalist, meaningful ideas brides actually buy."
    )
    payload["tiktokHook"] = _truncate_words(str(payload.get("tiktokHook", "")).strip(), 14) or "The bridesmaid gift trend every USA bride is saving right now."

    image_suggestions = payload.get("imageSuggestions", [])
    cleaned_images: list[dict[str, str]] = []
    if isinstance(image_suggestions, list):
        for suggestion in image_suggestions[:5]:
            if not isinstance(suggestion, dict):
                continue
            cleaned_images.append(
                {
                    "description": _truncate_words(str(suggestion.get("description", "Wedding gift flatlay with premium minimalist styling")), 20),
                    "altText": _truncate_words(str(suggestion.get("altText", "USA wedding gift ideas for bridesmaids and bridal party")), 18),
                }
            )
    while len(cleaned_images) < 3:
        i = len(cleaned_images) + 1
        cleaned_images.append(
            {
                "description": f"Minimalist wedding gift concept {i}",
                "altText": f"USA {primary_keyword} inspiration {i}",
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
    slug = str(payload.get("slug", "")).strip()
    primary_keyword = str(payload.get("primaryKeyword", "")).strip()
    secondary_keywords = payload.get("secondaryKeywords", [])

    lines = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"meta_description: {json.dumps(meta_description, ensure_ascii=False)}",
        f"slug: {json.dumps(slug, ensure_ascii=False)}",
        f"date: {json.dumps(date_iso, ensure_ascii=False)}",
        f"primary_keyword: {json.dumps(primary_keyword, ensure_ascii=False)}",
        f"secondary_keywords: {json.dumps(secondary_keywords, ensure_ascii=False)}",
        "---",
        "",
        f"# {title}",
        "",
        str(payload.get("intro", "")).strip(),
        "",
        "## Why This Gift Trend Is Rising in 2026",
        "",
        str(payload.get("whyTrendRising", "")).strip(),
        "",
    ]

    usa_trending_now = str(payload.get("usaTrendingNow", "")).strip()
    if usa_trending_now:
        lines.extend(
            [
                "## Why This Is Trending in the USA Right Now",
                "",
                usa_trending_now,
                "",
            ]
        )

    lines.extend(
        [
            f"## How to Choose the Perfect {primary_keyword.title()}",
            "",
            str(payload.get("chooseGuide", "")).strip(),
            "",
            f"## {str(payload.get('ideasHeading', '')).strip()}",
            "",
        ]
    )

    for idx, item in enumerate(payload.get("ideas", []), start=1):
        lines.extend(
            [
                f"{idx}. **{str(item.get('title', '')).strip()}** — {str(item.get('explanation', '')).strip()}",
            ]
        )
    lines.append("")

    budget_guide = str(payload.get("budgetGuide", "")).strip()
    if budget_guide:
        lines.extend(
            [
                "## Budget Guide",
                "",
                budget_guide,
                "",
            ]
        )

    lines.extend(
        [
            "## Luxury vs Minimalist: What Modern Brides Prefer",
            "",
            str(payload.get("luxuryVsMinimalist", "")).strip(),
            "",
            "## FAQ",
            "",
        ]
    )

    for item in payload.get("faq", []):
        lines.extend(
            [
                f"### {str(item.get('question', '')).strip()}",
                str(item.get("answer", "")).strip(),
                "",
            ]
        )

    lines.extend(["---", "", "## Image Suggestions", ""])
    for idx, item in enumerate(payload.get("imageSuggestions", []), start=1):
        lines.extend(
            [
                f"{idx}. {str(item.get('description', '')).strip()}  ",
                f"   ALT: \"{str(item.get('altText', '')).strip()}\"",
                "",
            ]
        )

    lines.extend(
        [
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
