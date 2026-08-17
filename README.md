# Affiliate Auto Tool

Local-first Streamlit MVP for a responsible affiliate-content workflow:

`Research or verified import → transparent winner scoring → reviewed content → vertical media → Ready-to-Post package → analytics → next action`

## What is implemented

- Public-page research for Shopee, TikTok Shop and Lazada through Playwright when product metadata is available.
- CSV import for verified affiliate-product exports; commission and affiliate links are never invented.
- Explainable winner score with data-confidence and caveats.
- Multi-provider content generation (Gemini, Groq, OpenRouter, OpenAI, AIML API, Cerebras and NVIDIA NIM).
- Optional Gemini image analysis, Vietnamese gTTS audio, FFmpeg-first vertical video rendering, and MoviePy fallback.
- Ready-to-Post folders with reviewed copy, media, thumbnail where available, affiliate link, JSON manifest and publication checklist.
- Append-only, duplicate-safe analytics imports with KPI and optimization insights.
- Local assistant that routes questions to product, content and analytics data.

## Quick start

Requires Python 3.11+ and FFmpeg is recommended (the bundled `imageio-ffmpeg` renderer is used first).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Open the address printed by Streamlit, usually `http://localhost:8501`.

Use **Product research** to search public pages, or import an affiliate-portal CSV when sales, commission or affiliate links need to be verified. Select a winner, review generated copy in **Content studio**, create media in **Video studio**, then export a folder in **Ready to post**.

## Data and safety

- Keep API keys in `.env` locally, or in Streamlit deployment secrets. Never commit them.
- `data/affiliate.db` is the local MVP database. Back it up before replacing a machine or deploying. The application retains historical analytics and ignores exact duplicates.
- Only upload media you own or are licensed to use. The app does not implement copyright-bypass behaviour.
- Review price, availability, product claims, affiliate link and platform disclosure before publishing.

## Deployment

The application is designed for Streamlit, not a static Vercel deployment. Push `refactor/foundation` to GitHub, link that branch in Streamlit Community Cloud, and set required API keys in **App settings → Secrets**.

For a personal demo, SQLite is sufficient. For a multi-user SaaS or durable cloud analytics history, replace the local SQLite database with managed Postgres before launch; Community Cloud filesystems are not a durable production database.

## Quality checks

```powershell
python -B -m unittest discover -s tests -v
python -B -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8-sig')) for p in pathlib.Path('.').rglob('*.py')]"
```
