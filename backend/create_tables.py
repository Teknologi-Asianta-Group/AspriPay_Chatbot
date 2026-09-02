"""
Script buat bikin semua tabel di MySQL berdasarkan SQLAlchemy models.
Jalanin sekali aja pas awal setup (atau setiap ada model baru).

Cara pakai: python create_tables.py
"""

from app.db.session import Base, engine
from app.models import models  # import biar semua model ke-register ke Base


def main():
    print("Membuat tabel di database...")
    Base.metadata.create_all(bind=engine)
    print("Selesai. Tabel-tabel berikut sudah dibuat/dicek:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    main()