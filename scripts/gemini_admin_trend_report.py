#!/usr/bin/env python3
"""Generate an internal US/Texas admin trend report for ZuzuMood designers.

Outputs:
- public/admin/<slug>.md
- public/admin/index.json (latest 30 reports metadata)
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
except Exception as exc:  # pragma: no cover
    raise RuntimeError("google-genai package is required") from exc

ROOT = Path(__file__).resolve().parent.parent
ADMIN_DIR = ROOT / "public" / "admin"
INDEX_PATH = ADMIN_DIR / "index.json"

TEXT_MODEL = "gemini-2.5-flash"
MAX_NEWS = 40
SELECTED_NEWS = 14

SEARCH_QUERIES = [
    "Etsy t-shirt trend USA",
    "Etsy hoodie trend USA",
    "Etsy sweatshirt trend USA",
    "bridal t-shirt trend US Etsy",
    "bachelorette sweatshirt trend US Etsy",
    "graphic hoodie trend US fashion",
    "TikTok t-shirt trend forecast US",
    "Pinterest hoodie trend US",
    "teacher sweatshirt trend Etsy USA",
    "western graphic t-shirt trend Texas",
]

ALLOWED_TEXTILE_TYPES = ("t-shirt", "tee", "hoodie", "sweatshirt")


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


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", value.lower()).strip("-")


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


def build_report_payload(client: genai.Client, articles: list[Article], date_str: str) -> dict[str, Any]:
    selected = articles[:SELECTED_NEWS]
    news_context = "\n".join(
        f"- {article.title} | {article.source} | {article.url}" for article in selected
    )

    prompt = f"""
You are the internal strategy analyst for ZuzuMood design team.
Return ONLY valid JSON.
Research signals must come from US market sources, but ALL narrative fields in output must be Turkish.
Focus ONLY on Etsy opportunities for t-shirt, hoodie, and sweatshirt categories in the US market.
Do not suggest any other product families (no tote, mug, jewelry, accessory, home decor, etc.).\nAnswer designer-facing questions explicitly: which t-shirt/hoodie/sweatshirt directions to prioritize, what visual direction to design, and why those decisions can convert in the next 30 days.

Date: {date_str}

News and trend signals:
{news_context}

Rules:
- Produce practical guidance for designers for now, +15 days, +20 days, +30 days.
- Include Etsy-friendly t-shirt/hoodie/sweatshirt product ideas, motif/color/material guidance, and quick execution hints.
- Include specific example links from provided sources in every horizon section.
- Keep tone direct, clear, and workshop-ready for a Turkish-speaking internal team.
- Never use markdown in JSON fields.

JSON schema:
{{
  "slug": "{date_str}-us-etsy-trend-radar",
  "title": "string (Turkish)",
  "summary": "string 140-260 chars (Turkish)",
  "marketPulse": "string (Turkish)",
  "weeklyFocus": ["string", "string", "string"],
  "horizons": [
    {{
      "window": "This week | 15 days | 20 days | 30 days",
      "trendName": "string",
      "whyNow": "string (Turkish)",
      "etsyOpportunity": "string (Turkish)",
      "designDirections": ["string", "string", "string"],
      "exampleLinks": [
        {{"label": "string", "url": "https://..."}},
        {{"label": "string", "url": "https://..."}}
      ]
    }}
  ],
  "competitorWatch": ["string", "string", "string"],
  "actionChecklist": ["string", "string", "string", "string"]
}}
""".strip()

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config={"temperature": 0.4},
    )

    text = getattr(response, "text", "") or ""
    payload = _extract_json(text)
    return enforce_payload_rules(payload, selected, date_str)


def enforce_payload_rules(payload: dict[str, Any], articles: list[Article], date_str: str) -> dict[str, Any]:
    payload["slug"] = _slugify(str(payload.get("slug") or f"{date_str}-us-etsy-trend-radar"))
    payload["title"] = str(payload.get("title") or "ZuzuMood İç Trend Radarı").strip()
    payload["summary"] = str(payload.get("summary") or "ABD trend sinyallerini Etsy odaklı tasarım aksiyonlarına çeviren şirket içi günlük rapor.").strip()
    payload["marketPulse"] = str(payload.get("marketPulse") or "Bu rapor ABD trend ivmesini pratik Etsy satış fırsatlarına dönüştürür.").strip()

    weekly_focus = payload.get("weeklyFocus")
    if not isinstance(weekly_focus, list):
        weekly_focus = []
    payload["weeklyFocus"] = [str(item).strip() for item in weekly_focus if str(item).strip()][:3]
    if len(payload["weeklyFocus"]) < 3:
        payload["weeklyFocus"] += [
            "Bu hafta mini kapsül koleksiyon için hızlı prototipleri yayına hazır hale getirin.",
            "Etsy başlıklarında trend terimlerini net kullanım senaryolarıyla eşleştirin.",
            "Pin ve kısa video varlıklarında tek bir görsel dil standardı koruyun.",
        ][: 3 - len(payload["weeklyFocus"])]

    fallback_links = [{"label": article.title, "url": article.url} for article in articles[:4]]

    horizons = payload.get("horizons")
    if not isinstance(horizons, list):
        horizons = []

    normalized_horizons: list[dict[str, Any]] = []
    expected_windows = ["This week", "15 days", "20 days", "30 days"]
    for index, window in enumerate(expected_windows):
        source = horizons[index] if index < len(horizons) and isinstance(horizons[index], dict) else {}
        links = source.get("exampleLinks") if isinstance(source.get("exampleLinks"), list) else []
        valid_links = []
        for item in links:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "").strip()
            label = str(item.get("label") or "Source").strip()
            if url.startswith("http"):
                valid_links.append({"label": label, "url": clean_url(url)})

        if len(valid_links) < 2:
            valid_links = (valid_links + fallback_links)[:2]

        design_directions = source.get("designDirections") if isinstance(source.get("designDirections"), list) else []
        design_directions = [str(item).strip() for item in design_directions if str(item).strip()][:3]
        if len(design_directions) < 3:
            design_directions += [
                "Silueti sade tutun; fark yaratan etkiyi aksesuar katmanında verin.",
                "Ürün fotoğraflarında nötr arka plan ve tek vurgu rengi kullanın.",
                "Açıklamalara net kullanım bağlamı ekleyin (bridal shower, prova yemeği, city hall nikahı).",
            ][: 3 - len(design_directions)]

        normalized_horizons.append(
            {
                "window": window,
                "trendName": str(source.get("trendName") or f"US Trend Opportunity {index + 1}").strip(),
                "whyNow": str(source.get("whyNow") or "Sinyal yoğunluğu artıyor; hızlı uygulama dönüşüm avantajı yaratır.").strip(),
                "etsyOpportunity": str(source.get("etsyOpportunity") or "Yüksek niyetli niş aramalara odaklanan kişiselleştirilebilir ürünlerde güçlü Etsy fırsatı var.").strip(),
                "designDirections": design_directions,
                "exampleLinks": valid_links,
            }
        )

    payload["horizons"] = normalized_horizons

    competitor = payload.get("competitorWatch")
    if not isinstance(competitor, list):
        competitor = []
    payload["competitorWatch"] = [str(item).strip() for item in competitor if str(item).strip()][:3]
    if len(payload["competitorWatch"]) < 3:
        payload["competitorWatch"] += [
            "Rakipler paketleme ve hero görsellerde lifestyle sahneleri artırıyor.",
            "'Gift for bride' ve 'bridal shower' kombinli başlık yapıları ivmesini koruyor.",
            "Aynı SKU için 2-3 renk varyantı stratejisi dönüşümü yükseltiyor.",
        ][: 3 - len(payload["competitorWatch"])]

    checklist = payload.get("actionChecklist")
    if not isinstance(checklist, list):
        checklist = []
    payload["actionChecklist"] = [str(item).strip() for item in checklist if str(item).strip()][:4]
    if len(payload["actionChecklist"]) < 4:
        payload["actionChecklist"] += [
            "Bu hafta 3 yeni konsepti moodboard ve üretime hazır eskizlerle tamamlayın.",
            "Listelemeden önce her tasarım için Etsy anahtar kelime varyasyonlarını eşleyin.",
            "Yaklaşan çekimler için tek ve tutarlı bir görsel yön belirleyin.",
            "Bir sonraki rapor döngüsüne kadar satış ve favori artışını takip edin.",
        ][: 4 - len(payload["actionChecklist"])]

    textile_strategy = payload.get("textileProductStrategy")
    if not isinstance(textile_strategy, list):
        textile_strategy = []

    normalized_textile_strategy: list[dict[str, str]] = []
    for item in textile_strategy[:5]:
        if not isinstance(item, dict):
            continue
        product_type = str(item.get("textileProductType") or "").strip()
        why_sell_now = str(item.get("whySellNow") or "").strip()
        design_direction = str(item.get("designDirection") or "").strip()
        price_band = str(item.get("priceBandUsd") or "").strip()
        production_note = str(item.get("productionNote") or "").strip()
        low_type = product_type.lower()
        if product_type and any(allowed in low_type for allowed in ALLOWED_TEXTILE_TYPES):
            normalized_textile_strategy.append(
                {
                    "textileProductType": product_type,
                    "whySellNow": why_sell_now or "ABD arama niyeti ve mevsim etkisi bu ürün tipinde hızlı dönüşüm potansiyeli yaratıyor.",
                    "designDirection": design_direction or "Tipografi ve motifi sade ama fark edilir tutun; kullanım senaryosunu ürün görselinde net anlatın.",
                    "priceBandUsd": price_band or "28-42",
                    "productionNote": production_note or "Baskı yoğunluğu orta seviyede tutulup hızlı teslim edilebilir varyant sayısı artırılmalı.",
                }
            )

    if len(normalized_textile_strategy) < 4:
        normalized_textile_strategy += [
            {
                "textileProductType": "Comfort Colors premium t-shirt",
                "whySellNow": "Yaz sezonuna geçişte günlük kullanıma uygun hafif ürün aramaları yükseliyor.",
                "designDirection": "Ön göğüs minimal sembol + sırtta hikâye anlatan kısa mesaj kompozisyonu kullanın.",
                "priceBandUsd": "28-38",
                "productionNote": "2 nötr + 1 trend renk paletiyle hızlı test yayınına çıkın.",
            },
            {
                "textileProductType": "Midweight unisex hoodie",
                "whySellNow": "Akşam etkinliği ve seyahat temalı satın alma niyeti için yıl boyu güçlü kategori.",
                "designDirection": "Tipografide el yazısı + serif kombinasyonu ile duygusal ama premium görünüm hedefleyin.",
                "priceBandUsd": "44-62",
                "productionNote": "Aynı tasarımın 2 baskı boyutlu varyantını çıkararak CTR testi yapın.",
            },
            {
                "textileProductType": "Bridal getting-ready sweatshirt",
                "whySellNow": "Bridal shower ve bachelorette aramaları etkinlik takvimleriyle paralel artıyor.",
                "designDirection": "İnce çizgi illüstrasyon + kişiselleştirilebilir isim/tarih alanı ekleyin.",
                "priceBandUsd": "36-52",
                "productionNote": "Sipariş formunda isim ve tarih formatını doğrulayan net alanlar kullanın.",
            },
            {
                "textileProductType": "Teacher quote crewneck sweatshirt",
                "whySellNow": "Okul dönemi ve hediye sezonunda öğretmen temalı sweatshirt aramaları istikrarlı talep üretir.",
                "designDirection": "Uzak mesafeden okunabilen net tipografi + küçük ikon detaylarıyla temiz kompozisyon kurun.",
                "priceBandUsd": "34-48",
                "productionNote": "Aynı tasarımın 2 renk varyantını stoklayıp mockup testleriyle kazanan rengi hızlı belirleyin.",
            },
        ][: 4 - len(normalized_textile_strategy)]

    payload["textileProductStrategy"] = normalized_textile_strategy[:5]

    designer_qa = payload.get("designerQa")
    if not isinstance(designer_qa, list):
        designer_qa = []

    normalized_qa: list[dict[str, str]] = []
    for item in designer_qa[:4]:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip()
        if question and answer:
            normalized_qa.append({"question": question, "answer": answer})

    if len(normalized_qa) < 3:
        normalized_qa += [
            {
                "question": "Bu hafta ZuzuMood hangi tekstil ürünlerini önceliklendirmeli?",
                "answer": "Öncelik sırası: premium t-shirt, bridal sweatshirt ve midweight hoodie olmalı. Bu üçlü hem yıl boyu aranıyor hem de kişiselleştirme ile sepet tutarını artırıyor.",
            },
            {
                "question": "Tasarımlarda hangi görsel dil daha iyi dönüşüm getirir?",
                "answer": "Tek ana fikirli, uzaktan okunabilen tipografi + tek vurgu illüstrasyonu en stabil sonuç verir. Kalabalık kompozisyon yerine sade ama karakterli yerleşim tercih edin.",
            },
            {
                "question": "ZuzuMood nasıl daha hızlı test ve öğrenme yapabilir?",
                "answer": "Her konsept için 2 renk ve 2 mockup varyantı ile 7 günlük mini test açın; favori oranı ve tıklama verisine göre kazanan tasarımı genişletin.",
            },
        ][: 3 - len(normalized_qa)]

    payload["designerQa"] = normalized_qa[:4]

    return payload


def to_markdown(payload: dict[str, Any], date_iso: str) -> str:
    lines = [
        "---",
        f'title: "{str(payload["title"]).replace(chr(34), chr(39))}"',
        f"date: {date_iso}",
        f'description: "{str(payload["summary"]).replace(chr(34), chr(39))}"',
        "locale: tr-TR",
        "region: us",
        "category: internal-trend-guide",
        "---",
        "",
        f"# {payload['title']}",
        "",
        payload["summary"],
        "",
        "## Pazar Nabzı",
        "",
        payload["marketPulse"],
        "",
        "## Bu Haftanın Odağı",
        "",
        *[f"- {item}" for item in payload["weeklyFocus"]],
        "",
        "## Trend Ufukları (Şimdi + 15/20/30 Gün)",
        "",
    ]

    for horizon in payload["horizons"]:
        lines.extend(
            [
                f"### {horizon['window']} — {horizon['trendName']}",
                "",
                f"**Neden şimdi:** {horizon['whyNow']}",
                "",
                f"**Etsy fırsatı:** {horizon['etsyOpportunity']}",
                "",
                "**Tasarım yönleri:**",
                *[f"- {item}" for item in horizon["designDirections"]],
                "",
                "**Örnek kaynaklar:**",
                *[f"- [{link['label']}]({link['url']})" for link in horizon["exampleLinks"]],
                "",
            ]
        )

    lines.extend(
        [
            "## Rakip ve Platform Takibi",
            "",
            *[f"- {item}" for item in payload["competitorWatch"]],
            "",
            "## Aksiyon Kontrol Listesi",
            "",
            *[f"- {item}" for item in payload["actionChecklist"]],
            "",
            "## Satılabilir Tekstil Ürün Stratejisi",
            "",
            *[
                line
                for item in payload["textileProductStrategy"]
                for line in [
                    f"### {item['textileProductType']}",
                    "",
                    f"- **Neden şimdi satılır:** {item['whySellNow']}",
                    f"- **Tasarım yönü:** {item['designDirection']}",
                    f"- **Önerilen fiyat bandı (USD):** {item['priceBandUsd']}",
                    f"- **Üretim notu:** {item['productionNote']}",
                    "",
                ]
            ],
            "## Tasarımcı Soru-Cevap",
            "",
            *[
                line
                for item in payload["designerQa"]
                for line in [
                    f"- **Soru:** {item['question']}",
                    f"  **Yanıt:** {item['answer']}",
                ]
            ],
            "",
            "---",
            "",
            "Bu rapor yalnızca şirket içi ekip kullanımı içindir.",
            "",
        ]
    )

    return "\n".join(lines)


def update_index(slug: str, title: str, summary: str, date_iso: str) -> None:
    entries: list[dict[str, str]] = []
    if INDEX_PATH.exists():
        try:
            entries = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []

    entries = [entry for entry in entries if entry.get("slug") != slug]
    entries.append(
        {
            "slug": slug,
            "title": title,
            "summary": summary,
            "date": date_iso,
            "path": f"/admin/{slug}.md",
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
        raise RuntimeError("No US fashion news found from RSS feeds")

    payload = build_report_payload(client, articles, date_slug)
    slug = payload.get("slug") or f"{date_slug}-us-etsy-trend-radar"
    slug = _slugify(slug)

    md = to_markdown(payload, date_iso)
    ADMIN_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ADMIN_DIR / f"{slug}.md"
    out_path.write_text(md, encoding="utf-8")

    update_index(
        slug=slug,
        title=str(payload.get("title", slug)),
        summary=str(payload.get("summary", "")),
        date_iso=date_iso,
    )

    print(f"✅ Admin report generated: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
