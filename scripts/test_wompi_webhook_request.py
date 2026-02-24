"""
Simula un POST real al endpoint del webhook de Wompi usando el cliente de Django.
Usa el payload exacto del evento fallido (transaction 149606-1771901133-85846).

Ejecutar:
    python manage.py shell < scripts/test_wompi_webhook_request.py
"""
import json
from django.test import RequestFactory
from apps.payments.views import wompi_webhook

PAYLOAD = {
    "data": {
        "transaction": {
            "id": "149606-1771901133-85846",
            "origin": None,
            "status": "APPROVED",
            "currency": "COP",
            "reference": "ORD-20260224-5B6B6A4D",
            "created_at": "2026-02-24T02:45:33.820Z",
            "billing_data": None,
            "finalized_at": "2026-02-24T02:45:34.342Z",
            "redirect_url": "https://barbershop.com.co/pagos/confirmacion/",
            "customer_email": "info@megadominio.co",
            "payment_method_type": "NEQUI",
            "status_message": None,
            "amount_in_cents": 1830000,
        }
    },
    "event": "transaction.updated",
    "sent_at": "2026-02-24T02:45:34.597Z",
    "signature": {
        "checksum": "4adb7de1822810e1d7028cba70609637d39648f9b05128a63bc0bfdfcfe6258f",
        "properties": [
            "transaction.id",
            "transaction.status",
            "transaction.amount_in_cents",
        ],
    },
    "timestamp": 1771901134,
    "environment": "test",
}

body = json.dumps(PAYLOAD).encode()

factory = RequestFactory()
request = factory.post(
    '/pagos/wompi/webhook/',
    data=body,
    content_type='application/json',
    HTTP_X_EVENT_CHECKSUM='4adb7de1822810e1d7028cba70609637d39648f9b05128a63bc0bfdfcfe6258f',
)

response = wompi_webhook(request)

print(f"Status HTTP:  {response.status_code}")
print(f"Respuesta:    {response.content.decode()}")

if response.status_code == 200:
    print("\n✓ Webhook aceptado correctamente")
    from apps.orders.models import Order
    order = Order.objects.filter(order_number='ORD-20260224-5B6B6A4D').first()
    if order:
        print(f"  Pedido encontrado: {order.order_number}")
        print(f"  Estado de pago:    {order.payment_status}")
        print(f"  Estado pedido:     {order.status}")
    else:
        print("  (Pedido ORD-20260224-5B6B6A4D no existe en BD — normal en sandbox)")
elif response.status_code == 401:
    print("\n✗ Firma rechazada — verifica WOMPI_EVENTS_SECRET")
elif response.status_code == 400:
    print("\n✗ Payload inválido")
