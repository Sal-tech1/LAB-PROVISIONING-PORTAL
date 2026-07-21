"""Seed script to populate initial lab template data."""

from backend.database import Base, SessionLocal, engine
from backend.models.models import LabTemplate


def seed_lab_templates() -> None:
    """Insert dummy lab templates when the table is empty.

    Returns:
        None
    """
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_count = db.query(LabTemplate).count()
        if existing_count > 0:
            print(f"Skipping seed: {existing_count} lab template(s) already exist.")
            return

        templates = [
            LabTemplate(
                name="Python Sandbox",
                image_tag="python:3.11-slim",
                cpu_limit="0.5",
                ram_limit="512m",
                description=(
                    "Lightweight Python environment for scripting and data exercises."
                ),
            ),
            LabTemplate(
                name="Node.js Workshop",
                image_tag="node:20-alpine",
                cpu_limit="1.0",
                ram_limit="1g",
                description=(
                    "Alpine-based Node.js lab for API and frontend development tasks."
                ),
            ),
        ]

        db.add_all(templates)
        db.commit()
        print(f"Seeded {len(templates)} lab template(s).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_lab_templates()
