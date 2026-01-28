import json
from pathlib import Path

from app.core.supabase import supabase


BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR)
PAGES_FILE = BASE_DIR / "pages.json"


def load_pages() -> list[dict]:
    if not PAGES_FILE.exists():
        raise FileNotFoundError(f"pages.json not found at {PAGES_FILE}")

    with PAGES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def upsert_page(page: dict):
    slug = page["slug"]

    existing = (
        supabase
        .table("pages")
        .select("id")
        .eq("slug", slug)
        .limit(1)
        .execute()
    )

    if existing.data:
        (
            supabase
            .table("pages")
            .update(page)
            .eq("slug", slug)
            .execute()
        )
        print(f" - Updated page: {slug}")
    else:
        (
            supabase
            .table("pages")
            .insert(page)
            .execute()
        )
        print(f" - Inserted page: {slug}")


def seed_pages():
    print("Seeding pages...\n")

    pages = load_pages()

    for page in pages:
        upsert_page(page)

    print("\nPage seeding completed!")


if __name__ == "__main__":
    seed_pages()
