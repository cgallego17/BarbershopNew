# Cómo reducir que los correos caigan en spam

## 1. Autenticación DNS (lo más importante)

Los proveedores (Gmail, Outlook, etc.) comprueban que el servidor que envía está autorizado para tu dominio.

### SPF (Sender Policy Framework)
- Ya tienes un registro SPF en tu zona DNS.
- Asegúrate de que incluya la IP o el host que envía (ej. `mail.barbershop.com.co` o la IP de tu servidor de correo).
- Ejemplo: `v=spf1 +a +mx +ip4:162.0.235.248 include:spf.web-hosting.com ~all`
- Si envías desde otro servidor (ej. SendGrid), añade su include: `include:sendgrid.net` o el que indiquen.

### DKIM (firma del dominio)
- Ya tienes un registro DKIM (`default._domainkey.barbershop.com.co`).
- Debe estar configurado en el **servidor de correo** (cPanel / hosting) para que firme cada mensaje con esa clave.
- En el panel de tu hosting (correo/cPanel) revisa que “DKIM” esté activado para el dominio.

### DMARC (opcional pero recomendado)
- Indica qué hacer si fallan SPF o DKIM y dónde recibir informes.
- Añade un TXT en `_dmarc.barbershop.com.co`:
  - Ejemplo: `v=DMARC1; p=none; rua=mailto:admin@barbershop.com.co`
  - Luego puedes subir a `p=quarantine` o `p=reject` cuando todo funcione bien.

## 2. Configuración en la app (ya aplicada)

- **Reply-To:** Si en Panel → Configuración tienes “Email de contacto”, se usa como Reply-To. Así el From puede ser `noreply@...` y las respuestas llegan a un buzón real.
- **Cabeceras:** Se envían `X-Auto-Response-Suppress: All`, `Auto-Submitted: auto-generated` y prioridad normal para que los filtros traten los correos como transaccionales.

## 3. Buenas prácticas de contenido

- Evitar palabras típicas de spam (“GRATIS”, “URGENTE”, “¡Gana dinero!”, etc.) en asuntos y cuerpo.
- Incluir siempre versión texto además de HTML (ya lo haces).
- No enviar solo imágenes; mantener proporción texto/HTML razonable (ya lo haces).
- Que el dominio del “From” coincida con el que envía (noreply@barbershop.com.co con mail.barbershop.com.co está bien).

## 4. Si sigues yendo a spam: usar servicio transaccional

Servicios como **SendGrid**, **Mailgun** o **Amazon SES**:
- Usan dominios e IPs con buena reputación.
- Gestionan SPF/DKIM por su lado (te dan valores para tu DNS).
- Suelen mejorar mucho la llegada a bandeja de entrada.

En ese caso solo cambias en `.env` el `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` según las instrucciones del proveedor.

## 5. Comprobar tu configuración

- [mail-tester.com](https://www.mail-tester.com): envía un correo a la dirección que te dan y revisa la puntuación y sugerencias.
- [mxtoolbox.com](https://mxtoolbox.com): comprueba SPF, DKIM, blacklists y DNS del dominio.
