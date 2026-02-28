# Cómo reducir que los correos caigan en spam

## Checklist rápido

- [ ] **DNS:** SPF, DKIM (y opcional DMARC) configurados y activos.
- [ ] **Panel:** Configuración con Email de contacto, Teléfono y Dirección completos.
- [ ] **From:** Usar un correo del mismo dominio que el SMTP (ej. noreply@barbershop.com.co).
- [ ] **Probar:** Enviar a [mail-tester.com](https://www.mail-tester.com) y revisar puntuación.

---

## 1. Autenticación DNS (lo más importante)

Los proveedores (Gmail, Outlook, etc.) comprueban que el servidor que envía está autorizado para tu dominio.

### SPF (Sender Policy Framework)
- Debe existir un registro TXT en tu dominio (ej. `barbershop.com.co`) con `v=spf1 ...`.
- Tiene que incluir la IP o el host desde el que envías (ej. `ip4:162.0.235.248` o `include:spf.web-hosting.com`).
- Si usas un servicio (SendGrid, Mailgun), añade su `include:...` según su documentación.

### DKIM (firma del dominio)
- Debe existir un registro TXT en `selector._domainkey.tudominio.com` con la clave pública.
- En el **servidor de correo** (cPanel / hosting) DKIM debe estar **activado** para el dominio, para que cada mensaje se firme con la clave privada.
- Sin DKIM activo en el servidor, los correos se consideran no firmados y es más fácil que caigan en spam.

### DMARC (recomendado)
- Registro TXT en `_dmarc.barbershop.com.co`.
- Ejemplo: `v=DMARC1; p=none; rua=mailto:admin@barbershop.com.co`
- Cuando SPF y DKIM estén bien, puedes pasar a `p=quarantine` o `p=reject`.

---

## 2. Configuración en la app (ya aplicada)

- **Reply-To:** Si en Panel → Configuración tienes "Email de contacto", se usa como Reply-To en todos los correos. Las respuestas llegan a un buzón real.
- **Cabeceras anti-spam:**
  - `X-Auto-Response-Suppress: All` (Outlook no envía auto-respuestas)
  - `Precedence: auto` (correo automático)
  - `Auto-Submitted: auto-generated` (transaccional)
  - `X-Priority: 3` (prioridad normal)
  - `X-Mailer` (identificación del envío)
- **Pie de correo:** Se incluye texto "Correo transaccional", enlace de contacto y, si está configurada, la **dirección física** (mejora confianza y cumplimiento).

---

## 3. Panel → Configuración (recomendado)

Completa en **Panel → Configuración**:

| Campo | Uso |
|-------|-----|
| **Email de contacto** | Se usa como Reply-To y se muestra en el pie del correo. |
| **Teléfono** | Aparece en el pie. |
| **Dirección** | Se muestra en el pie; aporta confianza y ayuda a filtros anti-spam. |

Cuanto más completa y coherente sea la identidad del remitente, mejor suele ser la deliverabilidad.

---

## 4. Buenas prácticas de contenido

- Evitar en asunto y cuerpo: "GRATIS", "URGENTE", "¡Gana dinero!", muchos signos de exclamación, TODO EN MAYÚSCULAS.
- Enviar siempre versión **texto** y **HTML** (la app ya lo hace).
- No enviar solo imágenes; mantener proporción razonable texto/HTML (la app ya lo hace).
- Que el dominio del **From** coincida con el servidor SMTP (ej. noreply@barbershop.com.co enviado desde mail.barbershop.com.co).

---

## 5. Si sigues yendo a spam: servicio transaccional

Servicios como **SendGrid**, **Mailgun** o **Amazon SES**:
- Usan IPs y dominios con buena reputación.
- Te dan los registros SPF/DKIM para tu DNS.
- Suelen mejorar mucho la llegada a bandeja de entrada.

Solo cambias en `.env`: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (y si aplica `EMAIL_USE_TLS` / `EMAIL_USE_SSL`) según la documentación del proveedor.

---

## 6. Comprobar configuración

- **[mail-tester.com](https://www.mail-tester.com):** Envía un correo de prueba a la dirección que te dan (por ejemplo con `python manage.py send_test_email --email la-direccion@que-te-dan.com`). Revisa puntuación y sugerencias (SPF, DKIM, contenido, etc.).
- **[mxtoolbox.com](https://mxtoolbox.com):** Comprueba SPF, DKIM, blacklists y DNS del dominio.
- **Gmail:** Si tienes cuenta Gmail, envía un correo a ti mismo y en "Mostrar original" revisa que aparezcan "spf=pass" y "dkim=pass".
