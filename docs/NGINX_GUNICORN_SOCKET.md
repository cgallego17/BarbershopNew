# Nginx + Gunicorn: socket path

Los logs de Nginx mostraban errores con dos rutas diferentes de socket:
- `/var/www/django_app/gunicorn.sock`
- `/run/gunicorn/gunicorn.sock`

**Debe coincidir** la ruta que usa Gunicorn con la que define Nginx.

## 1. Ver qué socket usa Gunicorn

```bash
sudo systemctl cat gunicorn | grep -i socket
# o
sudo systemctl cat gunicorn | grep -i bind
```

## 2. Ver qué socket espera Nginx

```bash
grep -r "gunicorn" /etc/nginx/
# Busca "proxy_pass" y "unix:"
```

## 3. Unificar

**Opción A**: Nginx debe apuntar al socket real de Gunicorn.  
Si Gunicorn usa `unix:/run/gunicorn/gunicorn.sock`, Nginx debe tener:

```nginx
upstream gunicorn {
    server unix:/run/gunicorn/gunicorn.sock fail_timeout=0;
}
```

**Opción B**: Crear el directorio y socket donde Nginx lo busca.  
Si Nginx usa `/var/www/django_app/gunicorn.sock`:

```bash
sudo mkdir -p /var/www/django_app
# Y configurar el servicio gunicorn para usar esa ruta
```

## 4. Reiniciar todo

```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## 5. Comprobar que el socket existe

```bash
ls -la /run/gunicorn/
# o
ls -la /var/www/django_app/*.sock
```
