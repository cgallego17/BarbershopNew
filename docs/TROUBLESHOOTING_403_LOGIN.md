# 403 en login en producción

## Causas más frecuentes

### 1. **CSRF: dominio no está en CSRF_TRUSTED_ORIGINS**

La URL exacta con la que accedes debe estar en `.env`:

```env
CSRF_TRUSTED_ORIGINS=https://barbershop.com.co,https://www.barbershop.com.co
```

- Usa **https** (no http).
- Sin barra final: `https://barbershop.com.co`, no `https://barbershop.com.co/`
- Si usas subdominio: `https://tienda.barbershop.com.co`

### 2. **HTTPS mal configurado (cookies Secure)**

En producción `CSRF_COOKIE_SECURE=True` y `SESSION_COOKIE_SECURE=True`. Si entras por HTTP, las cookies no se envían y obtienes 403.

**Solución:** Usar HTTPS con certificado válido (p. ej. Let's Encrypt).

### 3. **Nginx no pasa correctamente los headers**

Nginx debe enviar a Gunicorn:

```nginx
proxy_set_header Host $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

### 4. **Modo mantenimiento activo**

Si `maintenance_mode` está activo en el panel, se redirige a `/mantenimiento/` (no 403). Comprueba en Ajustes del sitio.

---

## Depuración

Tras configurar `CSRF_FAILURE_VIEW`, Django escribe en los logs la causa del 403. En el servidor:

```bash
# Con systemd
sudo journalctl -u gunicorn -f | grep "CSRF 403"

# O en archivo de log si lo tienes configurado
tail -f /var/log/gunicorn/error.log
```

Ejemplo de log:

```
CSRF 403: reason=Referer checking failed - origin not in CSRF_TRUSTED_ORIGINS | 
path=/cuentas/login/ | host=barbershop.com.co | referer=... | trusted_origins=[...]
```

- `reason=No CSRF cookie` → Cookies no llegan (HTTPS, dominio, SameSite).
- `reason=Referer checking failed - origin not in...` → Añade la URL a `CSRF_TRUSTED_ORIGINS`.
- `reason=CSRF token missing or incorrect` → Token inválido o expirado (recarga la página).

---

## Checklist rápido

1. [ ] `CSRF_TRUSTED_ORIGINS` en `.env` incluye la URL exacta (https, sin `/` final)
2. [ ] Accedes por HTTPS, no HTTP
3. [ ] `ALLOWED_HOSTS` incluye tu dominio
4. [ ] Nginx pasa `Host` y `X-Forwarded-Proto`
5. [ ] Reiniciaste Gunicorn tras cambiar `.env`: `sudo systemctl restart gunicorn`
