from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from xml.sax.saxutils import escape

BASE_URL = "https://zuzumood.com"
ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "products" / "EtsyListingsDownload.csv"
BLOG_INDEX_PATH = ROOT / "public" / "blog" / "index.json"
SITEMAP_PATH = ROOT / "public" / "sitemap.xml"

SHOP_CATEGORY_IDS = [
    "all",
    "valentines",
    "aesthetic",
    "healing",
    "music",
    "teacher",
    "patriotic",
    "bridal",
    "family",
]


@dataclass(frozen=True)
class UrlEntry:
    loc: str
    changefreq: str
    priority: str
    lastmod: str | None = None


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _to_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return re.sub(r"^-+|-+$", "", slug)[:80]


def _product_id(sku: str, title: str, row_index: int) -> str:
    sku_value = re.sub(r"[^a-z0-9]+", "-", sku.lower())
    if sku_value:
        return sku_value
    title_slug = _to_slug(title)
    if title_slug:
        return title_slug
    return f"product-{row_index + 1}"


def _load_products() -> list[str]:
    product_ids: list[str] = []
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            title = (row.get("TITLE") or "").strip()
            image = (row.get("IMAGE1") or "").strip()
            try:
                price = float((row.get("PRICE") or "").strip())
            except ValueError:
                price = float("nan")
            if not title or not image or price != price:
                continue
            sku = (row.get("SKU") or "").strip()
            product_ids.append(_product_id(sku, title, idx))
    return sorted(set(product_ids))


def _load_blog_slugs() -> list[tuple[str, str | None]]:
    if not BLOG_INDEX_PATH.exists():
        return []
    data = json.loads(BLOG_INDEX_PATH.read_text(encoding="utf-8"))
    items: list[tuple[str, str | None]] = []
    for post in data:
        slug = str(post.get("slug") or "").strip()
        date = str(post.get("date") or "").strip()
        if not slug:
            continue
        lastmod = None
        if date:
            try:
                lastmod = datetime.fromisoformat(date.replace("Z", "+00:00")).strftime("%Y-%m-%d")
            except ValueError:
                lastmod = None
        items.append((slug, lastmod))
    return items


def _render(entries: list[UrlEntry]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for e in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(e.loc)}</loc>")
        if e.lastmod:
            lines.append(f"    <lastmod>{e.lastmod}</lastmod>")
        lines.append(f"    <changefreq>{e.changefreq}</changefreq>")
        lines.append(f"    <priority>{e.priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> None:
    today = _now_iso()
    entries: list[UrlEntry] = [
        UrlEntry(f"{BASE_URL}/", "daily", "1.0", today),
        UrlEntry(f"{BASE_URL}/#/shop", "daily", "0.95", today),
        UrlEntry(f"{BASE_URL}/#/blog", "daily", "0.9", today),
        UrlEntry(f"{BASE_URL}/#/terms", "monthly", "0.6", today),
        UrlEntry(f"{BASE_URL}/#/privacy", "monthly", "0.6", today),
    ]

    for category in SHOP_CATEGORY_IDS:
        entries.append(
            UrlEntry(
                loc=f"{BASE_URL}/#/shop?cat={category}",
                changefreq="weekly",
                priority="0.8" if category != "all" else "0.85",
                lastmod=today,
            )
        )

    for product_id in _load_products():
        entries.append(
            UrlEntry(
                loc=f"{BASE_URL}/#/product/{product_id}",
                changefreq="weekly",
                priority="0.7",
                lastmod=today,
            )
        )

    for slug, lastmod in _load_blog_slugs():
        entries.append(
            UrlEntry(
                loc=f"{BASE_URL}/#/blog?post={slug}",
                changefreq="weekly",
                priority="0.75",
                lastmod=lastmod or today,
            )
        )

    SITEMAP_PATH.write_text(_render(entries), encoding="utf-8")


if __name__ == "__main__":
    main()
