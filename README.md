# The Art Vault

**Little Hands. Limitless Ideas.**

The Art Vault is a tiered-access library of printable art activities for kids aged 2–12. Anyone can browse the whole catalog. A free account unlocks a small number of downloads, and a membership unlocks everything.

There are no real payments: "Become a member" simply flips an account to the member tier so the whole flow can be demoed end to end.

## Features

- **Landing page** with a video hero, how-it-works steps, a catalog preview and a plan-aware pricing section
- **Catalog** with live search and filters by age and tier (htmx), open to everyone
- **Activity detail pages** with a download box that changes depending on who is looking
- **Sign up and log in** through Supabase Auth, with a "return to where you were" redirect
- **Tier-gated downloads** with a lifetime cap for free accounts, enforced on the server
- **My account page** showing the current plan, downloads used, and download history
- **Demo membership upgrade** that needs no payment details

## Access tiers

| Tier | Browse the catalog | Download |
|---|---|---|
| Visitor (no account) | Everything | Nothing |
| Free account | Everything | Free activities only, up to **2 downloads in total** |
| Member | Everything | Every activity, unlimited |

The tier only controls the download. Everyone sees the same catalog and the same detail pages.

**Where the rules are enforced:** tier and cap checks happen in the FastAPI download route (`app/routers/catalog.py`), never just in the template. Hiding a button is cosmetic. The route also locks the user's profile row while it checks, so two simultaneous clicks can't both slip under the cap. The download files live in `app/private/files/`, outside the public `static/` folder, so the only way to reach one is through the checked route.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python) |
| Templates | Jinja2, plain CSS, a little vanilla JavaScript |
| Interactivity | htmx, only for catalog search and filters |
| Database | Supabase Postgres, accessed with SQLAlchemy |
| Auth | Supabase Auth (tokens held in HttpOnly cookies) |
| Hosting | Render |

No React, no build step, no Docker.

## Getting started

You need Python 3.11 or newer (developed on 3.13) and access to the team's Supabase project.

1. **Clone the repo**
   ```bash
   git clone https://github.com/PramodSharmaGit/ArtVaultAI.git
   cd ArtVaultAI
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux / Git Bash on Windows: source venv/Scripts/activate
   venv\Scripts\activate           # Windows Command Prompt / PowerShell
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your environment variables.** Copy the template, then fill it in with the team's shared Supabase values (ask a teammate, and never commit this file):
   ```bash
   cp .env.example .env
   ```

   | Variable | What it is | Where to find it |
   |---|---|---|
   | `DATABASE_URL` | Postgres connection string for SQLAlchemy | Supabase dashboard → Connect → Session pooler |
   | `SUPABASE_URL` | Project URL (just the base URL, no `/rest/v1/`) | Project Settings → API |
   | `SUPABASE_KEY` | The **publishable** (anon) key | Project Settings → API Keys |

   Never use the `service_role` / secret key in this app.

5. **Run the app** from the project root
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   Then open <http://127.0.0.1:8000>.

### Database setup

The team shares one Supabase database that is already set up and seeded, so **teammates can skip this**. If you are starting from an empty database, create the tables and the 6 demo activities once:

```bash
python -m app.init_db
```

It is safe to re-run: existing tables and activities are left alone.

## Trying it out

1. Browse `/catalog` without an account and open any activity. You'll be offered "Sign up free to download".
2. Sign up, then download a free activity. The page shows "1 of 2 free downloads used".
3. Download a second one, then try a third. You'll be blocked with an upgrade prompt.
4. Open a member-only activity as a free user. It is blocked too.
5. Click **Become a member**. Downloads are now unlimited, and **My account** (from the profile menu) shows the member plan.

To reset a test account back to free, edit its row in the `profiles` table in Supabase (set `tier` to `free` and clear `member_since`) and delete its rows in `downloads`.

## Demo content

The catalog is seeded with 6 activities (3 free, 3 member-only):

| Activity | Tier | Ages |
|---|---|---|
| Window Garden Collage | Free | 2–5 |
| Cloud Watching Journal | Free | 5–9 |
| Squiggle Monster Maker | Free | 4–9 |
| Paper Rocket Kit | Member | 6–10 |
| Sunshine Suncatcher | Member | 3–8 |
| Pressed Flower Cards | Member | 6–12 |

Downloads are placeholder `.txt` files. The "120+ activities" on the landing page is marketing copy.

## Project structure

```
app/
  main.py            App setup, landing route, session-cookie middleware
  db.py              Database connection (reads DATABASE_URL)
  models.py          SQLAlchemy models: Profile, Asset, Download (schema source of truth)
  init_db.py         Creates tables and seeds the demo activities
  auth.py            Supabase Auth helpers, cookies, current user and tier
  templating.py      Jinja2 setup, plus current user/tier for every template
  routers/
    auth.py          Sign up, log in, log out
    catalog.py       Catalog, activity detail, gated download
    account.py       My account page, demo upgrade
  templates/         Jinja2 pages and partials
  static/            CSS, JavaScript and images (public)
  private/files/     Downloadable files (not public; served only by the download route)
AGENTS.md            Shared project context for AI coding tools and the team
.env.example         Environment variable template
requirements.txt
```

## Working on the project

- `AGENTS.md` is the shared source of truth for scope, design tokens (`app/static/css/theme.css`) and decisions. Read it before making changes, and update it when a decision changes.
- Commit small, working changes to `main`, and check the app still runs locally before you push.
- After pulling new changes, run `pip install -r requirements.txt` in case dependencies changed.
- Keep `.env` out of git. It is already in `.gitignore`.

## Known limitations

- No real payments. The upgrade button is a demo.
- No email verification or password reset. Turn off "Confirm email" in the Supabase Auth settings so new sign-ups can log in straight away.
- The free-tier cap is a lifetime total, not a monthly one. Re-downloading the same activity counts again.
- No way to cancel a membership from the app.
- The navigation bar is not yet compacted for very small phone screens.

## Roadmap

- Friendly 404 and error pages
- Compact mobile navigation
