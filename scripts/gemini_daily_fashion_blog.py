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
    content_type = _pick_content_type(date_str)
    source_lines = "\n".join([f"- {a.title} | {a.source} | {a.url}" for a in articles])

    prompt = f"""
You are a US bridal stylist consultant writing shopping-intent fashion analysis.
Date: {date_str}
Audience: women in the United States searching bridal and event fashion.
Daily content type for rotation: {content_type}

Primary business goals (strict):
1) Win Google Discover visibility.
2) Attract Pinterest traffic.
3) Rank on long-tail US searches.
4) Build authority in bridal & women's fashion.

Core message to reinforce naturally:
"This site follows fashion daily like a real fashion source."

Critical writing objective:
- Do NOT write a news summary.
- Build a decision guide that moves readers one step closer to choosing a bridal aesthetic identity.

Research and filtering rules:
- Use ONLY the source list provided below.
- Content must be US-centered. Do NOT write Turkey-focused content.
- Reject non-trend angles. A trend is valid only if at least 2 are true and explicitly stated in validation:
  - seen on a celebrity/runway/public figure
  - launched at multiple retailers
  - rising on TikTok or Pinterest
  - seasonal fit for current period
  - clear US search intent

Keyword strategy:
- Provide exactly 1 primary long-tail keyword + exactly 5 supporting long-tail keywords.
- Keep usage natural, no keyword stuffing.

Structure rules (mandatory SEO magnet format):
- Title max 60 characters, consultant-style.
- searchIntentHook must be 90-120 words and start with a real bride problem/decision conflict.
- For each trend section, write in Observation -> Meaning -> Action logic.
- For each trend section, explain behavior psychology (why this trend exists now).
- For each trend section, include buyer decision guidance:
  - who should wear it
  - who should NOT wear it
  - body effect
  - best event fit
- Product matching must be soft styling guidance, never direct selling language.
- End with "who should wear this and when" guidance + mistakes block + related searches block.
- Length target between {MIN_WORDS} and {MAX_WORDS} words.

Hard bans:
- keyword stuffing
- generic fashion guide
- encyclopedic style
- men's fashion
- fashion history
- step-by-step outfit tutorial tone

Return ONLY strict JSON with this schema:
{{
  "title": "string <= 60 chars",
  "slug": "yyyy-mm-dd-us-bridal-fashion-trends",
  "summary": "120-180 chars, English",
  "searchIntentHook": "90-120 words, English, decision conflict oriented",
  "heroPrompt": "English image prompt, no text in image",
  "contentType": "one of {CONTENT_TYPES}",
  "primaryKeyword": "string",
  "supportingKeywords": ["k1", "k2", "k3", "k4", "k5"],
  "trendValidation": [
    {{
      "claim": "short trend claim",
      "checksPassed": ["from the 5 checks above, at least 2"],
      "evidenceSources": ["https://...", "https://..."]
    }}
  ],
  "sections": [
    {{
      "heading": "string",
      "observation": "1-2 sentences",
      "meaning": "1-2 sentences explaining psychology/behavior shift",
      "action": "1-2 sentences with styling decision",
      "goodFor": ["...", "..."],
      "notIdealFor": ["...", "..."],
      "bodyEffect": "short explanation",
      "bestEventFit": "short explanation",
      "styleIdea": "1-2 sentences, soft product matching",
      "seenOn": "short phrase",
      "spottedIn": "short phrase",
      "sourceTitle": "string",
      "sourceUrl": "https://..."
    }}
  ],
  "relatedSearches": ["6-8 long-tail searches"],
  "stylingAlternatives": ["3-5 alternatives"],
  "mistakesToAvoid": ["4-6 mistakes"],
  "closing": "3-5 sentences answering who should wear this and when",
  "seo": {{
    "metaTitle": "max 60 chars",
    "metaDescription": "max 155 chars"
  }}
}}

Critical constraints:
- sections length must be exactly {SELECTED_NEWS}.
- supportingKeywords length must be exactly 5.
- trendValidation length must be at least 3.
- relatedSearches length 6-8.
- stylingAlternatives length 3-5.
- mistakesToAvoid length 4-6.
- Every sourceUrl and evidenceSources URL must exist in source list.
- Content must be 100% English.
- Mention Etsy or ZuzuMood naturally in summary/closing for conversion intent.

Sources:
{source_lines}
"""

    resp = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.45),
    )

    payload = _extract_json((resp.text or "").strip())
    payload = enforce_payload_rules(payload, articles, date_str, content_type)
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


def enforce_payload_rules(
    payload: dict[str, Any], articles: list[Article], date_slug: str, content_type: str
) -> dict[str, Any]:
    allowed_urls = {clean_url(a.url) for a in articles}
    canonical_url_map = {_normalize_url_for_match(url): url for url in allowed_urls}
    title_to_url = {
        _normalize_title_for_match(a.title): clean_url(a.url)
        for a in articles
        if _normalize_title_for_match(a.title)
    }
    fallback_url = clean_url(articles[0].url)

    payload["contentType"] = payload.get("contentType") or content_type
    payload["summary"] = _truncate_words(payload.get("summary", ""), 22)
    if _looks_non_english(payload["summary"]):
        payload["summary"] = "US brides are navigating fast-changing style choices. This guide helps you decide what to wear, why trends are rising, and how to style bridal signals with confidence on ZuzuMood Etsy."
    if "etsy" not in payload["summary"].lower() and "zuzumood" not in payload["summary"].lower():
        payload["summary"] = (payload["summary"] + " Discover matching pieces on ZuzuMood Etsy.").strip()

    hook = _truncate_words(payload.get("searchIntentHook", ""), 85)
    if not hook or _looks_non_english(hook):
        hook = (
            "Many US brides searching for modern bridal outfits are not choosing a traditional gown for every wedding moment. "
            "They are deciding between courthouse looks, second-look party dresses, and photo-ready symbolic pieces that still feel bridal. "
            "The common mistake is picking an outfit that looks trendy in person but reads casual in photos. "
            "This guide breaks down what each trend means, who it works for, and how to make a confident styling decision."
        )
    payload["searchIntentHook"] = hook

    title = str(payload.get("title", "")).strip() or "US Bridal Trend Report"
    if _looks_non_english(title):
        title = "US Bridal Trends: What to Wear and Why"
    payload["title"] = title[:60]

    slug = str(payload.get("slug", "")).strip() or f"{date_slug}-us-bridal-fashion-trends"
    payload["slug"] = _slugify(slug)

    primary_keyword = str(payload.get("primaryKeyword", "")).strip()
    if not primary_keyword:
        primary_keyword = f"{date_slug[:4]} bridal second look outfit ideas usa"
    payload["primaryKeyword"] = primary_keyword

    supporting = payload.get("supportingKeywords", [])
    if not isinstance(supporting, list):
        supporting = []
    supporting = [str(item).strip() for item in supporting if str(item).strip()]
    while len(supporting) < 5:
        supporting.append(f"bridal trend idea {len(supporting) + 1} usa")
    payload["supportingKeywords"] = supporting[:5]

    sections = payload.get("sections", [])
    if not isinstance(sections, list):
        raise ValueError("sections must be a list")
    if len(sections) != SELECTED_NEWS:
        raise ValueError(f"Gemini did not return exactly {SELECTED_NEWS} sections")

    for section in sections:
        if not isinstance(section, dict):
            raise ValueError("section entry must be object")
        section["heading"] = _truncate_words(section.get("heading", "Trend highlight"), 7)
        section["observation"] = _truncate_words(section.get("observation", ""), 14)
        section["meaning"] = _truncate_words(section.get("meaning", ""), 14)
        section["action"] = _truncate_words(section.get("action", ""), 14)
        section["goodFor"] = _sanitize_list(section.get("goodFor", []), 2, 4, "Best for")
        section["notIdealFor"] = _sanitize_list(section.get("notIdealFor", []), 2, 4, "Avoid for")
        section["bodyEffect"] = _truncate_words(section.get("bodyEffect", ""), 8)
        section["bestEventFit"] = _truncate_words(section.get("bestEventFit", ""), 8)
        section["styleIdea"] = _truncate_words(section.get("styleIdea", ""), 10)
        section["seenOn"] = _truncate_words(section.get("seenOn", ""), 5)
        section["spottedIn"] = _truncate_words(section.get("spottedIn", ""), 5)
        section["sourceTitle"] = _truncate_words(section.get("sourceTitle", "Source"), 8)
        source_url = _resolve_source_url(
            raw_url=str(section.get("sourceUrl", "")),
            source_title=str(section.get("sourceTitle", "")),
            fallback_url=fallback_url,
            allowed_urls=allowed_urls,
            canonical_url_map=canonical_url_map,
            title_to_url=title_to_url,
        )
        section["sourceUrl"] = source_url

    validations = payload.get("trendValidation", [])
    if not isinstance(validations, list) or len(validations) < 3:
        raise ValueError("trendValidation must contain at least 3 entries")
    # Keep the markdown output within the hard word budget by limiting validation rows.
    # URLs in evidence lines are word-heavy for regex-based word counting.
    validations = validations[:3]
    payload["trendValidation"] = validations

    for validation in validations:
        if not isinstance(validation, dict):
            raise ValueError("trendValidation item must be object")
        validation["claim"] = _truncate_words(validation.get("claim", "Trend signal"), 8)
        checks = validation.get("checksPassed", [])
        if not isinstance(checks, list) or len(checks) < 2:
            raise ValueError("each trendValidation item must pass at least 2 checks")
        validation["checksPassed"] = [
            _truncate_words(item, 4) for item in checks if _truncate_words(item, 4)
        ][:3]
        evidence = validation.get("evidenceSources", [])
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("trendValidation item must include evidenceSources")
        cleaned_evidence: list[str] = []
        for url in evidence:
            matched_url = _resolve_source_url(
                raw_url=str(url),
                source_title="",
                fallback_url="",
                allowed_urls=allowed_urls,
                canonical_url_map=canonical_url_map,
                title_to_url=title_to_url,
            )
            if matched_url:
                cleaned_evidence.append(matched_url)

        cleaned_evidence = list(dict.fromkeys(cleaned_evidence))
        if not cleaned_evidence:
            cleaned_evidence = [fallback_url]
        validation["evidenceSources"] = cleaned_evidence[:1]

    payload["relatedSearches"] = _sanitize_list(payload.get("relatedSearches", []), 6, 8, "bridal search")
    payload["stylingAlternatives"] = _sanitize_list(payload.get("stylingAlternatives", []), 3, 5, "styling alternative")
    payload["mistakesToAvoid"] = _sanitize_list(payload.get("mistakesToAvoid", []), 4, 6, "bridal mistake")

    seo = payload.get("seo", {})
    if not isinstance(seo, dict):
        seo = {}
    meta_title = str(seo.get("metaTitle", payload["title"])).strip()
    meta_description = str(seo.get("metaDescription", payload["summary"])).strip()
    if "zuzumood" not in meta_title.lower() and "etsy" not in meta_title.lower():
        meta_title = f"{meta_title} | ZuzuMood"[:60]
    if "zuzumood" not in meta_description.lower() and "etsy" not in meta_description.lower():
        meta_description = f"{meta_description} Explore ZuzuMood Etsy."[:155]
    payload["seo"] = {"metaTitle": meta_title[:60], "metaDescription": meta_description[:155]}
    payload["closing"] = _truncate_words(payload.get("closing", ""), 45)

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
    summary = str(payload.get("summary", "")).strip()
    hook = str(payload.get("searchIntentHook", "")).strip()
    seo = payload.get("seo", {})
    sections = payload.get("sections", [])
    validations = payload.get("trendValidation", [])

    lines = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"date: {date_iso}",
        f"description: {json.dumps(summary, ensure_ascii=False)}",
        f"image: {image_path}",
        f"metaTitle: {json.dumps(seo.get('metaTitle', title), ensure_ascii=False)}",
        f"metaDescription: {json.dumps(seo.get('metaDescription', summary), ensure_ascii=False)}",
        f"contentType: {json.dumps(payload.get('contentType', ''), ensure_ascii=False)}",
        f"primaryKeyword: {json.dumps(payload.get('primaryKeyword', ''), ensure_ascii=False)}",
        f"supportingKeywords: {json.dumps(payload.get('supportingKeywords', []), ensure_ascii=False)}",
        "locale: en-US",
        "region: us",
        "category: bridal-fashion-trends",
        "---",
        "",
        f"# {title}",
        "",
        summary,
        "",
        "## Search Intent Hook",
        "",
        hook,
        "",
        "## Trend Validation Snapshot",
        "",
    ]

    for validation in validations:
        claim = str(validation.get("claim", "Trend signal")).strip()
        checks = validation.get("checksPassed", [])
        checks_text = ", ".join(str(item).strip() for item in checks if str(item).strip())
        evidence_links = " | ".join(f"[{url}]({url})" for url in validation.get("evidenceSources", []))
        lines.extend(
            [
                f"- **{claim}** — checks passed: {checks_text}",
                f"  - evidence: {evidence_links}",
            ]
        )

    lines.extend(["", "## Bridal Decision Trend Breakdown", ""])

    for idx, section in enumerate(sections, start=1):
        good_for = ", ".join(section.get("goodFor", []))
        not_ideal = ", ".join(section.get("notIdealFor", []))
        lines.extend(
            [
                f"### {idx}. {str(section.get('heading', '')).strip()}",
                "",
                f"**Observation:** {str(section.get('observation', '')).strip()}",
                "",
                f"**Meaning:** {str(section.get('meaning', '')).strip()}",
                "",
                f"**Action:** {str(section.get('action', '')).strip()}",
                "",
                f"**Good for:** {good_for}",
                "",
                f"**Not ideal for:** {not_ideal}",
                "",
                f"**Body effect:** {str(section.get('bodyEffect', '')).strip()}",
                "",
                f"**Best event fit:** {str(section.get('bestEventFit', '')).strip()}",
                "",
                f"**Style idea:** {str(section.get('styleIdea', '')).strip()}",
                "",
                f"Seen on: {str(section.get('seenOn', '')).strip()}",
                "",
                f"Spotted in: {str(section.get('spottedIn', '')).strip()}",
                "",
                f"Source: [{str(section.get('sourceTitle', 'Source')).strip()}]({str(section.get('sourceUrl', '#')).strip()})",
                "",
            ]
        )

    lines.extend(
        [
            "## Primary and Supporting Searches",
            "",
            f"- Primary: **{payload.get('primaryKeyword', '')}**",
            *[f"- Supporting: {kw}" for kw in payload.get("supportingKeywords", [])],
            "",
            "## Related Searches Brides Also Use",
            "",
            *[f"- {item}" for item in payload.get("relatedSearches", [])],
            "",
            "## Styling Alternatives",
            "",
            *[f"- {item}" for item in payload.get("stylingAlternatives", [])],
            "",
            "## Mistakes Brides Make",
            "",
            *[f"- {item}" for item in payload.get("mistakesToAvoid", [])],
            "",
            "## Who Should Wear This and When",
            "",
            str(payload.get("closing", "")).strip(),
            "",
            "---",
            "",
            "If you want trend-aligned bridal pieces, browse ZuzuMood on Etsy: https://www.etsy.com/shop/ZuzuMood",
            "",
            "This post is generated daily to track what women in the US are searching and saving lately.",
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
    entries.insert(
        0,
        {
            "slug": slug,
            "title": title,
            "summary": summary,
            "date": date_iso,
            "path": f"/blog/{slug}.md",
            "image": image_path,
        },
    )

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
        summary=str(payload.get("summary", "")),
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
