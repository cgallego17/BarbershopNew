import re
import urllib.request
from decimal import Decimal

from apps.orders.models import Order


def run():
    order = Order.objects.create(
        billing_first_name="Diag",
        billing_last_name="Wompi",
        billing_email="diag@example.com",
        billing_phone="3000000000",
        billing_address="Calle 1",
        billing_city="Bogota",
        billing_country="Colombia",
        subtotal=Decimal("57900.00"),
        shipping_total=Decimal("0.00"),
        total=Decimal("57900.00"),
    )
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:8000/pagos/pagar/{order.order_number}/",
            timeout=10,
        ) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        def extract(name):
            m = re.search(rf'name="{re.escape(name)}"\s+value="([^"]*)"', html)
            return m.group(1) if m else ""

        pub = extract("public-key")
        amount = extract("amount-in-cents")
        reference = extract("reference")
        signature = extract("signature:integrity")
        redirect_url = extract("redirect-url")

        print("ORDER", order.order_number)
        print("PUBLIC_KEY_EMPTY", pub == "")
        print("PUBLIC_KEY_PREFIX", pub[:12] if pub else "")
        print("AMOUNT", amount)
        print("REFERENCE", reference)
        print("SIGNATURE_LEN", len(signature))
        print("REDIRECT_URL", redirect_url)
    finally:
        order.delete()


if __name__ == "__main__":
    run()
