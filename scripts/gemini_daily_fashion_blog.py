#!/usr/bin/env python3
"""Generate a daily US fashion trend blog post with Gemini.

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
MAX_NEWS = 12
SELECTED_NEWS = 5


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

    keep = []
    for k, values in parse_qs(parsed.query, keep_blank_values=True).items():
        low = k.lower()
        if low.startswith("utm") or low in {"oc", "ved", "usg", "ei", "sa", "source"}:
            continue
        for v in values:
            keep.append((k, v))

    query = urlencode(keep, doseq=True)
    return urlunparse(parsed._replace(query=query, fragment=""))


def fetch_us_fashion_news(limit: int = MAX_NEWS) -> list[Article]:
    queries = [
        "fashion trend United States",
        "street style US fashion",
        "fashion week US designers",
        "celebrity fashion trend",
        "viral fashion trend tiktok",
        "sustainable fashion US",
    ]

    feeds = [
        f"https://news.google.com/rss/search?q={q.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        for q in queries
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
                published = getattr(entry, "published", "") or ""

                articles.append(
                    Article(
                        title=title,
                        url=clean_url(final_url),
                        source=source,
                        published=published,
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


def build_blog_payload(client: genai.Client, articles: list[Article], date_str: str) -> dict[str, Any]:
    source_lines = "\n".join(
        [f"- {a.title} | {a.source} | {a.url}" for a in articles]
    )

    prompt = f"""
You are a senior fashion editor and e-commerce SEO strategist.
Task: Create a DAILY Turkish blog draft about current trending/hit fashion news in the United States for {date_str}.
Business goal: drive qualified organic traffic to Etsy store https://www.etsy.com/shop/ZuzuMood.

Use ONLY the source list below.
Select exactly {SELECTED_NEWS} strongest trend stories.

Return only strict JSON with this schema:
{{
  "title": "string",
  "slug": "yyyy-mm-dd-us-fashion-trends",
  "summary": "max 180 chars Turkish summary",
  "heroPrompt": "English prompt for image generation, no text in image",
  "items": [
    {{
      "icon": "single emoji",
      "headline": "short Turkish heading",
      "whyItIsHot": "2-3 Turkish sentences",
      "styleTip": "1 Turkish practical style tip",
      "sourceTitle": "original source title",
      "sourceUrl": "https://..."
    }}
  ],
  "seo": {{
    "metaTitle": "max 60 chars",
    "metaDescription": "max 155 chars"
  }}
}}

Rules:
- "items" must contain exactly {SELECTED_NEWS} entries.
- Keep tone practical, modern, and concise.
- Optimize wording for Etsy purchase intent and US fashion search intent.
- Mention "Etsy" or "ZuzuMood" naturally in summary or tips to support conversion SEO.
- Do not invent brands or links.
- sourceUrl must be one from provided sources.

Sources:
{source_lines}
"""

    resp = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.5),
    )

    text = (resp.text or "").strip()
    payload = _extract_json(text)
    payload = enforce_etsy_focus(payload)

    if len(payload.get("items", [])) != SELECTED_NEWS:
        raise ValueError("Gemini did not return expected number of items")

    return payload




def enforce_etsy_focus(payload: dict[str, Any]) -> dict[str, Any]:
    summary = str(payload.get("summary", "")).strip()
    if "etsy" not in summary.lower() and "zuzumood" not in summary.lower():
        payload["summary"] = f"{summary} ZuzuMood Etsy mağazası için trend odaklı stil fikirleri içerir.".strip()

    items = payload.get("items", [])
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            tip = str(item.get("styleTip", "")).strip()
            if "etsy" not in tip.lower() and "zuzumood" not in tip.lower():
                item["styleTip"] = f"{tip} Uyumlu parçalar için ZuzuMood Etsy mağazasına göz at.".strip()

    seo = payload.get("seo", {})
    if isinstance(seo, dict):
        meta_title = str(seo.get("metaTitle", "")).strip()
        meta_description = str(seo.get("metaDescription", "")).strip()

        if meta_title and "etsy" not in meta_title.lower() and "zuzumood" not in meta_title.lower():
            seo["metaTitle"] = f"{meta_title} | ZuzuMood Etsy"[:60]

        if meta_description and "etsy" not in meta_description.lower() and "zuzumood" not in meta_description.lower():
            seo["metaDescription"] = f"{meta_description} Trend parçalar için ZuzuMood Etsy mağazasını ziyaret edin."[:155]

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
    title = payload["title"].strip()
    summary = payload["summary"].strip()
    seo = payload.get("seo", {})

    lines = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"date: {date_iso}",
        f"description: {json.dumps(summary, ensure_ascii=False)}",
        f"image: {image_path}",
        f"metaTitle: {json.dumps(seo.get('metaTitle', title), ensure_ascii=False)}",
        f"metaDescription: {json.dumps(seo.get('metaDescription', summary), ensure_ascii=False)}",
        "locale: tr-TR",
        "region: us",
        "category: fashion-trends",
        "---",
        "",
        f"# {title}",
        "",
        summary,
        "",
    ]

    for idx, item in enumerate(payload.get("items", []), start=1):
        lines.extend(
            [
                f"## {idx}. {item.get('icon', '✨')} {item.get('headline', '').strip()}",
                "",
                item.get("whyItIsHot", "").strip(),
                "",
                f"**Stil Önerisi:** {item.get('styleTip', '').strip()}",
                "",
                f"Kaynak: [{item.get('sourceTitle', 'Haber')}]({item.get('sourceUrl', '#')})",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "ABD trendlerini Etsy odaklı alışverişe çevirmek için mağazamızı ziyaret edin: https://www.etsy.com/shop/ZuzuMood",
            "",
            "Bu içerik her gün otomatik olarak Gemini ile güncellenir.",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def update_index(slug: str, title: str, summary: str, date_iso: str, image_path: str) -> None:
    entries: list[dict[str, str]] = []
    if INDEX_PATH.exists():
        try:
            entries = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []

    entries = [e for e in entries if e.get("slug") != slug]
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
        raise RuntimeError("No US fashion news found from RSS feeds")

    payload = build_blog_payload(client, articles, date_slug)
    slug = payload.get("slug") or f"{date_slug}-us-fashion-trends"
    slug = re.sub(r"[^a-z0-9-]", "-", slug.lower()).strip("-")

    image_rel = f"/blog/images/{slug}.png"
    image_out = IMAGE_DIR / f"{slug}.png"
    image_ok = False
    try:
        image_ok = generate_cover_image(client, payload.get("heroPrompt", "fashion editorial photo"), image_out)
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
        title=payload.get("title", slug),
        summary=payload.get("summary", ""),
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
