"""Seed the MongoDB database with sample products from data/sample_products.csv.

Usage:
    Start the backend first:   uvicorn backend.main:app --reload
    Then run this script:      python seed.py
"""

import csv
import sys

import requests

API_BASE = "http://localhost:8000"
PRODUCTS_CSV = "data/sample_products.csv"


def seed_products() -> list[dict]:
    created = []
    try:
        with open(PRODUCTS_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["name"].startswith("#"):
                    continue  # skip comment rows
                payload = {
                    "name": row["name"],
                    "category": row["category"],
                    "cost_price": float(row["cost_price"]),
                    "selling_price": float(row["selling_price"]),
                    "stock": int(row["stock"]),
                    "minimum_stock": int(row["minimum_stock"]),
                    "supplier": row["supplier"],
                }
                r = requests.post(f"{API_BASE}/products", json=payload, timeout=10)
                if r.status_code == 201:
                    created.append(r.json())
                    print(f"  ✓ {row['name']}")
                else:
                    print(f"  ✗ {row['name']}: {r.text}")
    except FileNotFoundError:
        print(f"File not found: {PRODUCTS_CSV}", file=sys.stderr)
        sys.exit(1)
    except requests.ConnectionError:
        print("Cannot connect to backend. Make sure it is running:", file=sys.stderr)
        print(f"  uvicorn backend.main:app --reload", file=sys.stderr)
        sys.exit(1)
    return created


if __name__ == "__main__":
    print(f"Seeding products from {PRODUCTS_CSV}...")
    products = seed_products()
    print(f"\n✅ Seeded {len(products)} products into MongoDB.")
    print("\nNext steps:")
    print("  1. Open the frontend: streamlit run frontend/dashboard.py")
    print("  2. Go to Sales → Record Sale to add transactions.")
    print("  3. View analytics, finance, and inventory health.")
