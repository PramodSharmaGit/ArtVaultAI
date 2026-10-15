# AGENTS.md — Art Vault

Shared project context for AI coding agents (Claude Code, Codex CLI, or any other tool used on this repo). Read this before making changes. This file sits at the repo root and is picked up automatically — keep it accurate as decisions change, since it's the one shared source of truth every tool on this team pulls from.

## Project Overview

The Art Vault is a tiered-access content library for printable kids' art activities (ages 2–12). Visitors can browse the full catalog for free, create a free account to save favorites and get a limited number of downloads, or subscribe to a paid membership for unlimited access.

Core concept — three access tiers, gating *downloads*, not *browsing*:

| Tier | Can browse | Can download |
|---|---|---|
| Anonymous (no account) | Everything | Nothing |
| Free account | Everything | Free-tier assets, up to a lifetime cap |
| Member | Everything | Everything, unlimited |

Everyone sees the same catalog and the same asset detail pages. The tier only controls whether the download button is live.

## Scope (1-week build)

### In scope
- Landing page — hero, how-it-works, catalog preview, pricing/membership section
- Signup / login
- Catalog browse page (public — works for anonymous visitors too)
- Asset detail page with tier-gated download
- Account/dashboard page — shows current plan, and either download usage (free) or unlimited status (member)
- "Upgrade to Membership" action — no real payment, just flips the user's tier

### Out of scope (explicitly, for this milestone)
- Real payment processing (Stripe, etc.)
- Any AI/agent-powered feature inside the app itself — not required by the assignment
- Monthly download-limit resets — use a flat lifetime cap for the free tier (currently 2 downloads total, ever), not a per-month counter, to avoid needing reset/cron logic
- Real, usable activity files — placeholder downloads are fine; preview images should be original, not pulled from real products/sites
- Password reset / email verification flows — nice-to-have only if time remains

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database + Auth:** Supabase (hosted Postgres; **Supabase Auth** for signup/login — decided, see "Decided" below)
- **Frontend:** Jinja2 templates + htmx for interactivity, plain CSS — no React, no build step
- **Deployment:** Render (single Python web service, no Dockerfile needed)
- Explicitly **not** using: Docker, Vercel, a separate frontend app/repo

## Brand / Design Tokens

Source of truth for colors and typography is `app/static/css/theme.css` — pulled directly from the approved landing-page mockup, not just a loose color name. Any agent building templates should use these tokens rather than inventing new colors or fonts.

- Background (cream): `#FBF6EE` · Section background: `#F4EBDB` · Card background: `#FFFDF9`
- Text: `#2B2420` (primary) · `#6B6253` (secondary) · Border/divider: `#E8DFD0`
- Accent — terracotta, used for primary actions and the Member tier: `#C1542E`
- Support — teal, used for the Free tier and secondary icons: `#2F6F63`
- Display font: **Fraunces** (serif, headings) · Body font: **Work Sans** (sans-serif), both loaded via Google Fonts
- Buttons: 7px border-radius · Cards: 12px border-radius

`theme.css` covers colors, typography and base components only — not page layout. Section order (nav → hero → how-it-works → catalog preview → pricing → footer) is described under Scope above; exact spacing/structure is left to whoever builds each page, matching the general feel rather than pixel-for-pixel.

## Architecture

- One FastAPI app serves both the HTML pages (via Jinja2) and any small JSON/partial endpoints htmx calls
- Supabase holds two things: the `auth.users` table it manages itself, and our own app tables (profiles, assets, etc.)
- **Tier checks always happen server-side in FastAPI route handlers.** Hiding a button in a template is UI only — it is never the actual access control.

## Database Schema

Source of truth is `app/models.py` (SQLAlchemy). Tables are created by running `python -m app.init_db` once against Supabase's Postgres — no manual SQL Editor step, safe to re-run. Three tables:

- **profiles** — extends Supabase's `auth.users` with `tier` (`'free'` | `'member'`) and `member_since`
- **assets** — the catalog: title, description, age range, preview image, download file, `tier_required`
- **downloads** — one row per completed download; enforces the free-tier lifetime cap and powers the "downloads used" display on the account page

Favorites is cut from this build to keep scope down — not in the schema.

- **Free-tier lifetime download cap: 2** (small on purpose so the limit is easy to demo; `FREE_DOWNLOAD_CAP` in `app/models.py`) — enforced in FastAPI route code (count a user's rows in `downloads`), not a DB constraint, so it's a one-line change if it ever needs to change.

## Suggested Project Structure

```
app/
  main.py
  routers/
    auth.py
    catalog.py
    account.py
  templates/
    base.html
    landing.html
    catalog.html
    asset_detail.html
    account.html
  static/
    css/
      theme.css   # design tokens — see "Brand / Design Tokens" above
    images/
  private/
    files/        # placeholder downloadable files for each asset. Deliberately NOT under static/ (which is public): only the tier-checked download route serves these
  models.py        # SQLAlchemy models — source of truth for the schema, see "Database Schema" above
  init_db.py        # creates tables from models.py: `python -m app.init_db`
  db.py             # Supabase/Postgres connection (reads DATABASE_URL)
.env.example
requirements.txt
AGENTS.md
README.md
```

## Conventions

- Standard FastAPI conventions — type hints where practical, keep route handlers thin, push logic into small helper functions
- Environment variables live in `.env` (never commit it) — commit `.env.example` with blank values instead. Needs `DATABASE_URL` (Supabase's Postgres connection string, for SQLAlchemy — Project Settings → Database in the Supabase dashboard), plus `SUPABASE_URL` and `SUPABASE_KEY` (for Supabase Auth — Project Settings → API)
- Committing directly to `main` is fine given the one-week timeline — keep commits small and working; don't push something that breaks the app for the rest of the team
- Confirm the app still runs locally (`uvicorn app.main:app --reload`) before pushing

## Environment Setup

1. Clone the repo
2. `python -m venv venv && source venv/bin/activate` (or the Windows equivalent)
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`, fill in the team's shared Supabase credentials (see Conventions above for which values)
5. `python -m app.init_db` — creates the tables (one-time, safe to re-run)
6. `uvicorn app.main:app --reload`

## Open Decisions — needs group input

- [ ] **Hero visual:** real photo/image vs. the current illustration-style graphic — fine to keep the placeholder illustration until the team has an actual image.
- [ ] **Card preview images:** currently placeholder icons; swap in real images via `preview_image_url` once catalog content is finalized.
- [ ] **Mobile nav cleanup:** deferred until core features (database, auth, tier-gated downloads) work. The layout is already responsive; only the nav needs a compact phone version. Do a quick phone-width check at the end of each new page.

## Decided (current state — not locked in; update this section + `theme.css` together whenever they change)

- **Auth:** Supabase's built-in Auth — no custom password hashing/session code.
- **Brand / Design:** "The Art Vault," terracotta/teal palette — concrete values in "Brand / Design Tokens" above and `app/static/css/theme.css`. If the palette changes, edit both in the same change so they don't drift out of sync.
- **Catalog content (demo seed data):** 6 activities, 3 free / 3 member (Squiggle Monster Maker was switched to free so the free-tier cap is easy to demo). The landing page's "120+ activities" line is marketing copy, not a literal content requirement — these 6 are the real seed data:
  1. Window Garden Collage — Free — ages 2–5 — tissue paper & glue
  2. Cloud Watching Journal — Free — ages 5–9 — printable journal
  3. Paper Rocket Kit — Member — ages 6–10 — cut & fold template
  4. Sunshine Suncatcher — Member — ages 3–8 — tissue paper & contact film
  5. Pressed Flower Cards — Member — ages 6–12 — pressed flowers & cardstock
  6. Squiggle Monster Maker — Free — ages 4–9 — markers & cut-outs
- **htmx:** included, but scoped to two things only — the favorite toggle on a catalog card, and live search/filter on the catalog page. Signup/login and the download/tier-gating flow stay plain server-rendered forms/pages — those need to be simple and reliable, not snappy, and keeping htmx out of that path means a UI bug there can't accidentally affect access control.