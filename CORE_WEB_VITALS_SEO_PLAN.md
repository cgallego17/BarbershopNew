# Plan de Optimización: Core Web Vitals + SEO Técnico

Objetivo: llevar el sitio a **Lighthouse 90+** y mejorar posicionamiento orgánico sin afectar negativamente:

- imagen hero
- LCP
- contenido above-the-fold

---

## 1) Metas medibles

- **LCP:** < 2.5s (ideal < 2.0s en móvil real)
- **CLS:** < 0.10
- **INP:** < 200ms
- **TTFB:** < 800ms
- **Lighthouse móvil:** 90+ en Performance y SEO

Medición:

- Lab: Lighthouse / PageSpeed
- Real user monitoring: `web-vitals` + GA4

---

## 2) Reglas de implementación (sin dañar hero ni above-the-fold)

- [x] ~~No aplicar `loading="lazy"` al hero principal.~~
- [x] ~~Hero principal con `fetchpriority="high"` y preload.~~
- [x] ~~Todo lo below-the-fold: lazy loading + baja prioridad.~~
- [x] ~~Reservar espacio de imagen/contenedor para evitar CLS.~~
- [ ] Mantener contenido principal visible en móvil (mobile-first indexing).

---

## 3) Tareas técnicas priorizadas

### A. LCP y ruta crítica (prioridad alta)

- [ ] Definir **una sola** imagen candidata a LCP en home.
- [x] ~~Preload de hero:~~

```html
<link rel="preload" as="image" href="/img/hero.avif">
```

- [x] ~~Imagen hero:~~

```html
<img src="/img/hero.avif" width="1920" height="900" fetchpriority="high" decoding="async" alt="Hero principal">
```

- [x] ~~Reducir JS bloqueante antes del primer render (fase inicial: `defer` + refactor de handler sin dependencia temprana de jQuery).~~
- [ ] Cargar CSS crítico primero; diferir lo no crítico.

### B. Lazy loading below-the-fold (prioridad alta)

- [x] ~~Aplicar en galería, tarjetas, bloques secundarios:~~

```html
<img src="/img/card.webp" width="480" height="480" loading="lazy" fetchpriority="low" decoding="async" alt="">
```

- [ ] Iframes/videos con carga diferida.

### C. Optimización de imágenes (prioridad alta)

- [ ] Generar formatos modernos: AVIF + WebP (fallback JPG/PNG).
- [ ] Usar `srcset` y `sizes` para responsive real.
- [ ] Comprimir assets pesados (objetivo < 150 KB por imagen de card cuando sea posible).

### D. Evitar CLS (prioridad alta)

- [x] ~~Todas las imágenes con `width` + `height`.~~
- [x] ~~Contenedores dinámicos con `aspect-ratio`.~~
- [ ] No inyectar elementos por encima del contenido visible.
- [x] ~~Estabilizar badges/contadores con ancho fijo o `tabular-nums`.~~

### E. SEO técnico (prioridad alta)

- [~] `title` y `meta description` únicos por URL *(implementación dinámica inicial en tienda/categoría/búsqueda; faltan plantillas restantes)*.
- [x] ~~`canonical` correcto.~~
- [x] ~~`sitemap.xml` + `robots.txt` correctos.~~
- [~] Schema orgánico: `Product`, `Breadcrumb`, `Organization` (y `FAQ` si aplica).
- [ ] Mejorar enlazado interno entre categorías, productos y bloques destacados.
- [x] ~~Open Graph + Twitter Cards por plantilla (home, categoría, producto, blog).~~
- [x] ~~Control de indexación para filtros/facetas (`noindex,follow` cuando corresponda) (implementación inicial en tienda con querystring).~~
- [ ] Validación de snippets enriquecidos con Rich Results Test y Search Console.

### F. Móvil-first indexing (prioridad alta)

- [ ] Misma información en mobile y desktop.
- [ ] Evitar ocultar contenido clave en móvil.
- [ ] Tap targets y tipografía adecuados.
- [ ] JS total reducido en móvil.

---

## 4) Impacto esperado en ranking SEO

Mejoras en Core Web Vitals no reemplazan relevancia de contenido, pero sí impactan:

- mejor experiencia (menos rebote)
- mejor rastreo e indexación por eficiencia
- mejor conversión y señales de interacción

---

## 5) SEO avanzado para redes sociales (Open Graph / Twitter / WhatsApp)

Objetivo: que cada URL comparta correctamente en Facebook, Instagram (link preview), WhatsApp, X/Twitter y LinkedIn.

### Metadatos recomendados por página

- [x] ~~`og:title`, `og:description`, `og:type`, `og:url`, `og:image`~~
- [x] ~~`twitter:card=summary_large_image`, `twitter:title`, `twitter:description`, `twitter:image`~~
- [x] ~~`og:locale` y alternates si hay más idiomas~~

Ejemplo base:

```html
<meta property="og:type" content="website">
<meta property="og:title" content="The Barbershop - Productos para cuidado masculino">
<meta property="og:description" content="Compra productos premium para barba y cabello.">
<meta property="og:url" content="https://dominio.com/tienda/producto-x/">
<meta property="og:image" content="https://dominio.com/media/social/producto-x-1200x630.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Producto X | The Barbershop">
<meta name="twitter:description" content="Acabado premium para barba y cabello.">
<meta name="twitter:image" content="https://dominio.com/media/social/producto-x-1200x630.jpg">
```

### Reglas de imagen social

- [ ] Tamaño recomendado: **1200x630**
- [ ] Peso ideal: < 300 KB
- [x] ~~URL absoluta y pública (sin bloqueo por robots o auth)~~
- [ ] 1 imagen por URL, coherente con el contenido

### Validación obligatoria

- [ ] Facebook Sharing Debugger
- [ ] X Card Validator
- [ ] LinkedIn Post Inspector
- [ ] Pruebas manuales en WhatsApp (actualizar caché cambiando querystring si aplica)

---

## 6) Estrategia SEO técnica para ecommerce (alto impacto)

### Canonical y facetas

- Categorías principales: indexables
- Filtros de orden, precio, color, etc.: `noindex,follow` (según estrategia)
- [x] ~~Canonical a URL limpia (evitar duplicados por parámetros) (implementación inicial en tienda).~~

### Paginación y rastreo

- URLs paginadas indexables cuando aporten valor
- Navegación interna clara y crawlable
- Evitar enlaces internos con `#` como sustituto de URLs reales

### Datos estructurados recomendados

- [x] ~~Home: `Organization`, `WebSite` (+ SearchAction si aplica)~~
- [x] ~~Categorías / tienda: `BreadcrumbList`, `CollectionPage` (implementación inicial en listado de productos)~~
- Producto: `Product`, `Offer`, `AggregateRating`, `Review`
- Negocio local (si aplica): `LocalBusiness`

### Sitemaps

- `sitemap.xml` por tipo: productos, categorías, páginas, imágenes
- excluir URLs no indexables
- fecha de última modificación real (`lastmod`)

---

## 7) Buenas prácticas por stack

### WordPress

- Cache de página + object cache + CDN.
- Conversión WebP/AVIF automática.
- Reducir plugins que inyectan JS/CSS global.
- Preload de hero y fuentes principales.
- Plugin SEO bien configurado (titles, schema, canonicals, noindex de facetas).
- Generación automática de OG/Twitter por tipo de contenido.
- Revisar `wp_head` para evitar meta duplicadas entre tema + plugin.

### Vue

- Code splitting por rutas y componentes.
- Carga dinámica de componentes no críticos.
- SSR/prerender para páginas SEO.
- Imágenes responsive con pipeline (Vite + optimización).
- Head management consistente (`title`, canonical, OG, Twitter) por ruta.
- SSR recomendado para fichas de producto/categorías (evita depender de JS para SEO).

---

## 8) Plan de ejecución (14 días)

### Días 1-2: Baseline

- tomar métricas Lighthouse (mobile/desktop)
- tomar Core Web Vitals reales

### Días 3-5: LCP + render crítico

- [x] ~~preload hero~~
- [x] ~~fetchpriority~~
- [x] ~~recorte de JS bloqueante (fase inicial aplicada)~~

### Días 6-8: Imágenes

- [ ] AVIF/WebP
- [ ] `srcset/sizes`
- [x] ~~lazy below-the-fold~~

### Días 9-10: CLS hardening

- [x] ~~`width/height`~~
- [x] ~~`aspect-ratio`~~
- [x] ~~contenedores estables~~

### Días 11-12: SEO técnico + social tags

- [~] metas, canonical, schema, sitemap *(metas únicas aplicadas en Home/Tienda/Producto/Contacto/Nosotros/Mi cuenta/Checkout/Pedido; canonical para filtros/paginación aplicado; sitemap + robots verificados; schema Home/Tienda/Product/Breadcrumb aplicado; falta validación final en Search Console/Rich Results)*
- [x] ~~OG/Twitter por tipo de página~~
- [ ] validadores de share previews

### Días 13-14: QA y validación

- [ ] comparar before/after
- [ ] ajustar puntos restantes
- [ ] revisión de indexación (Search Console)
- [ ] revisión de snippets y cobertura de rastreo

---

## 9) Checklist de done

- [ ] LCP < 2.5s en móvil
- [ ] CLS < 0.1 en páginas principales
- [ ] INP < 200ms
- [ ] Lighthouse móvil 90+ en Home, Tienda, Producto, Checkout
- [ ] Schema validado sin errores críticos
- [ ] Sitemap indexado en Search Console
- [ ] OG/Twitter válidos en Home, Categoría, Producto y Blog
- [ ] Share preview correcto en WhatsApp, Facebook, X y LinkedIn
- [ ] URLs de filtros/facetas con directiva de indexación definida

---

## Nota operativa

Este documento es la guía para ejecutar las optimizaciones en el proyecto actual.
Próximo paso: aplicar punto por punto en templates, assets y carga de scripts, midiendo en cada iteración.

---

## 10) Roadmap en Sprints (con horas estimadas)

### Sprint 1 (rápido impacto: CWV + estabilidad) — 8 a 12 horas

Objetivo: asegurar base de performance y UX estable en Home, Tienda y Producto.

- [x] Hero: preload + `fetchpriority` + `loading` correcto (1.0 h)
- [x] Lazy loading below-the-fold en secciones principales (1.5 h)
- [x] CLS hardening (`width/height`, `aspect-ratio`, contenedores) (2.5 h)
- [ ] Reducir JS bloqueante inicial (`defer`, condicionales, limpieza plugins) (2.0 - 3.0 h)
- [ ] Medición before/after con Lighthouse móvil + desktop (1.0 - 2.0 h)

Entregable Sprint 1:
- LCP y CLS en verde en páginas clave (o muy cerca de objetivo).

### Sprint 2 (SEO técnico + social tags) — 10 a 16 horas

Objetivo: mejorar indexación, snippets y previews en redes.

- [x] OG/Twitter base por plantilla (1.5 h)
- [x] ~~Canonical strategy para facetas/filtros/paginación~~ (2.0 - 3.0 h)
- [~] Meta titles/descriptions únicos por tipo de página (2.0 - 3.0 h)
- [~] Schema completo (`Product`, `Breadcrumb`, `Organization`, etc.) (2.0 - 3.0 h)
- [ ] Validación social previews (Facebook/X/LinkedIn/WhatsApp) (1.0 - 2.0 h)
- [ ] Validación Rich Results + Search Console (1.0 - 2.0 h)

Entregable Sprint 2:
- Snippets y shares consistentes, cobertura SEO técnica sin errores críticos.

### Sprint 3 (optimización avanzada de imágenes + mobile-first) — 12 a 20 horas

Objetivo: consolidar rendimiento real y escalar SEO para móvil.

- [ ] Pipeline AVIF/WebP (generación y fallback) (4.0 - 6.0 h)
- [ ] `srcset/sizes` en plantillas críticas (3.0 - 5.0 h)
- [ ] Compresión masiva de assets legacy (2.0 - 4.0 h)
- [ ] Ajuste mobile-first indexing (contenido/paridad UX/tap targets) (2.0 - 3.0 h)
- [ ] QA final + monitoreo con Web Vitals reales (1.0 - 2.0 h)

Entregable Sprint 3:
- Lighthouse 90+ sostenible y mejora de métricas reales de usuarios.

---

## 11) Prioridad recomendada de ejecución

1. Sprint 1 completo
2. Sprint 2 completo
3. Sprint 3 completo

Si se requiere impacto inmediato en negocio:
- ejecutar primero: JS bloqueante + canonical/facetas + social previews.
