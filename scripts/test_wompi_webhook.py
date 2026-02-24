"""
Test de verificación de firma del webhook de Wompi.
Usa el payload real del evento fallido (transaction 149606-1771901133-85846).

Ejecutar desde la raíz del proyecto:
    python manage.py shell < scripts/test_wompi_webhook.py
o:
    python scripts/test_wompi_webhook.py  (si Django ya está configurado)
"""
import hashlib
import hmac
import json

from django.conf import settings

PAYLOAD = {
    "data": {
        "transaction": {
            "id": "149606-1771901133-85846",
            "status": "APPROVED",
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

events_secret = getattr(settings, 'WOMPI_EVENTS_SECRET', '').strip()
print(f"WOMPI_EVENTS_SECRET configurado: {'SÍ (' + events_secret[:6] + '...)' if events_secret else 'NO (vacío)'}")

signature  = PAYLOAD.get('signature', {})
checksum   = signature.get('checksum', '')
properties = signature.get('properties', [])
timestamp  = PAYLOAD.get('timestamp', '')
data       = PAYLOAD.get('data', {})

print(f"\nPropiedades de la firma: {properties}")
print(f"Timestamp: {timestamp}")
print(f"Checksum esperado: {checksum}")

parts = []
for prop in properties:
    val = data
    for key in prop.split('.'):
        val = val.get(key, '') if isinstance(val, dict) else ''
    print(f"  {prop} = {val!r}")
    parts.append(str(val))

parts.append(str(timestamp))
if events_secret:
    parts.append(events_secret)
    raw = ''.join(parts)
    computed = hashlib.sha256(raw.encode()).hexdigest()
    match = hmac.compare_digest(computed, checksum)
    print(f"\nCadena a firmar: {''.join(parts[:-1])}[SECRET]")
    print(f"Checksum computado: {computed}")
    print(f"Checksum esperado:  {checksum}")
    print(f"\n{'✓ FIRMA VÁLIDA — el webhook sería ACEPTADO' if match else '✗ FIRMA INVÁLIDA — revisa que WOMPI_EVENTS_SECRET sea el correcto'}")
else:
    print("\nWOMPI_EVENTS_SECRET vacío — el webhook se ACEPTA sin verificar firma (ver warning en logs).")
    print("Configura WOMPI_EVENTS_SECRET en .env con el valor del panel de Wompi → Configuración → Eventos.")
