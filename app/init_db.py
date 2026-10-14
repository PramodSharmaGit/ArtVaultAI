"""Create the tables and seed the demo catalog. Safe to re-run: `python -m app.init_db`."""
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal, engine
from app.models import TIER_FREE, TIER_MEMBER, Asset, Base

# Demo seed data (see AGENTS.md "Decided"): 2 free, 4 member.
SEED_ASSETS = [
    ("Window Garden Collage", "Press colorful tissue paper onto a sunny window to grow a flower garden that glows.",
     2, 5, "Tissue paper & glue", "window-garden", TIER_FREE),
    ("Cloud Watching Journal", "A printable journal for spotting shapes in the clouds, drawing them and writing stories.",
     5, 9, "Printable journal", "cloud-journal", TIER_FREE),
    ("Paper Rocket Kit", "Cut, fold and decorate a paper rocket ready for blast-off.",
     6, 10, "Cut & fold template", "paper-rocket", TIER_MEMBER),
    ("Sunshine Suncatcher", "Layer tissue paper and contact film into a bright sun that lights up the window.",
     3, 8, "Tissue paper & contact film", "suncatcher", TIER_MEMBER),
    ("Pressed Flower Cards", "Arrange pressed flowers and leaves on cardstock to make greeting cards.",
     6, 12, "Pressed flowers & cardstock", "pressed-flowers", TIER_MEMBER),
    ("Squiggle Monster Maker", "Turn a wiggly squiggle into a silly monster with markers and cut-outs.",
     4, 9, "Markers & cut-outs", "squiggle-monster", TIER_MEMBER),
]


def seed_assets() -> int:
    """Insert any seed asset whose title is missing. Returns how many were added."""
    added = 0
    with SessionLocal() as session:
        existing = set(session.scalars(select(Asset.title)))
        for title, description, age_min, age_max, materials, slug, tier in SEED_ASSETS:
            if title in existing:
                continue
            session.add(Asset(
                title=title, description=description, age_min=age_min, age_max=age_max,
                materials=materials, preview_image_url=f"images/{slug}.jpeg",
                download_file_url=f"files/{slug}.txt", tier_required=tier,
            ))
            added += 1
        session.commit()
    return added


def main() -> None:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise SystemExit(f"Could not connect to the database. Check DATABASE_URL in .env.\n{type(exc).__name__}")
    print("Connected to the database.")

    Base.metadata.create_all(engine)
    print("Tables ready: profiles, assets, downloads.")

    print(f"Seeded {seed_assets()} new asset(s).")


if __name__ == "__main__":
    main()
