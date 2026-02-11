<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# ZuzuMood

React + TypeScript + Vite tabanlı ZuzuMood storefront projesi.

## Run Locally

**Prerequisites:** Node.js

1. Install dependencies:
   `npm install`
2. Set `VITE_GEMINI_API_KEY` (recommended) in `.env.local`.
   - Backward-compatible fallbacks: `GEMINI_API_KEY`, `GEMINI_KEY`, `API_KEY`.
3. Run the app:
   `npm run dev`

## Daily Fashion Blog Automation

Bu repoda GitHub Actions ile her gün ABD moda trend haberlerini toplayıp Gemini ile blog üreten otomasyon bulunur.

- Workflow: `.github/workflows/daily-fashion-blog.yml`
- Script: `scripts/gemini_daily_fashion_blog.py`
- Output:
  - `public/blog/<slug>.md`
  - `public/blog/index.json`
  - `public/blog/images/<slug>.png`

### Required GitHub Secret

- `GEMINI_KEY`: Gemini API key (workflow içinde bu isimle okunur).

### Manual run

```bash
pip install -r requirements.txt
GEMINI_KEY=... python scripts/gemini_daily_fashion_blog.py
```
