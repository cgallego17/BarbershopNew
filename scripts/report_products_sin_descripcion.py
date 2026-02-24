#!/usr/bin/env python
"""
Lista productos sin descripción o con descripción = "1".
Ejecutar desde la raíz del proyecto: python scripts/report_products_sin_descripcion.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.products.models import Product

bad = []
for p in Product.objects.all().only("id", "name", "sku", "description"):
    d = (p.description or "").strip()
    if not d or d == "1" or d.upper() == "NONE":
        bad.append(
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku or "-",
                "description": (p.description or "")[:100],
            }
        )

print(f"Total productos sin descripción, con '1' o 'NONE': {len(bad)}\n")
for r in bad:
    print(f"ID: {r['id']} | SKU: {r['sku']} | Nombre: {r['name'][:60]}")
    print(f"    Descripción: {repr(r['description'])}")
    print()
