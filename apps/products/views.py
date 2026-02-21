import json
from urllib.parse import urlencode
from django.db import models
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.views.decorators.http import require_POST

from .models import (
    Product, Category, Brand, ProductReview, ProductView, ProductFavorite
)


def _safe_next_url(request, candidate, fallback):
    if candidate and url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return fallback


class ProductListView(ListView):
    model = Product
    template_name = 'products/shop.html'
    context_object_name = 'products'
    paginate_by = 12

    def paginate_queryset(self, queryset, page_size):
        from django.core.paginator import Paginator, InvalidPage, Page
        paginator = Paginator(queryset, page_size)
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = max(1, int(page))
        except (ValueError, TypeError):
            page_number = 1
        try:
            page_obj = paginator.page(page_number)
        except InvalidPage:
            if paginator.num_pages == 0:
                # Queryset vacío: página 1 sin resultados
                page_obj = Page([], 1, paginator)
            else:
                # Página fuera de rango → última página válida
                page_obj = paginator.page(paginator.num_pages)
        return paginator, page_obj, page_obj.object_list, page_obj.has_other_pages()

    def get_queryset(self):
        from apps.core.models import SiteSettings
        from decimal import Decimal
        qs = Product.objects.filter(is_active=True).prefetch_related('categories', 'images', 'brand')
        if not SiteSettings.get().show_out_of_stock_products:
            qs = qs.filter(Product.q_in_stock())
        category_slug = self.kwargs.get('category_slug') or self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(categories__slug=category_slug)
        brand_slug = self.request.GET.get('brand')
        if brand_slug:
            qs = qs.filter(brand__slug=brand_slug)
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        try:
            if min_price:
                qs = qs.filter(regular_price__gte=Decimal(min_price))
            if max_price:
                qs = qs.filter(regular_price__lte=Decimal(max_price))
        except Exception:
            pass
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(sku__icontains=search) |
                models.Q(codigo__icontains=search)
            )
        sort = self.request.GET.get('sort', 'default')
        if sort == 'price_asc':
            qs = qs.order_by('sale_price', 'regular_price')
        elif sort == 'price_desc':
            qs = qs.order_by('-sale_price', '-regular_price')
        elif sort == 'name':
            qs = qs.order_by('name')
        elif sort == 'newest':
            qs = qs.order_by('-created_at')
        return qs.distinct()

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from decimal import Decimal
        context = super().get_context_data(**kwargs)
        # Conteo de la lista actual (filtrada) — siempre coherente con lo que se muestra
        context['products_count'] = context['page_obj'].paginator.count
        # Total sin filtro de categoría (para el enlace "Todas las categorías")
        from apps.core.models import SiteSettings
        base_qs = Product.objects.filter(is_active=True)
        if not SiteSettings.get().show_out_of_stock_products:
            base_qs = base_qs.filter(Product.q_in_stock())
        context['total_products_count'] = base_qs.count()
        # Misma lógica que la lista: contar solo productos que aparecerían en el listado
        count_filter = models.Q(products__is_active=True)
        if not SiteSettings.get().show_out_of_stock_products:
            count_filter = models.Q(products__in=base_qs)
        context['categories'] = Category.objects.filter(is_active=True).annotate(
            product_count=Count('products', filter=count_filter)
        ).filter(product_count__gt=0)
        context['brands'] = Brand.objects.filter(is_active=True).annotate(
            product_count=Count('products', filter=count_filter)
        ).filter(product_count__gt=0)
        filter_category = self.request.GET.get('category')
        if not filter_category:
            filter_category = self.kwargs.get('category_slug', '')
        context['filter_category'] = filter_category
        context['filter_brand'] = self.request.GET.get('brand', '')
        context['filter_q'] = self.request.GET.get('q', '')
        context['selected_category_obj'] = None
        if context['filter_category']:
            context['selected_category_obj'] = Category.objects.filter(
                is_active=True, slug=context['filter_category']
            ).first()
        context['selected_brand_obj'] = None
        if context['filter_brand']:
            context['selected_brand_obj'] = Brand.objects.filter(
                is_active=True, slug=context['filter_brand']
            ).first()
        context['filter_min_price'] = self.request.GET.get('min_price', '')
        context['filter_max_price'] = self.request.GET.get('max_price', '')
        context['favorite_product_ids'] = set()
        if self.request.user.is_authenticated:
            favorite_ids = ProductFavorite.objects.filter(
                user=self.request.user
            ).values_list('product_id', flat=True)
            context['favorite_product_ids'] = set(favorite_ids)
        # Rango de precios en catálogo (para placeholder en el form)
        price_range = Product.objects.filter(is_active=True).aggregate(
            min_p=models.Min('regular_price'),
            max_p=models.Max('regular_price')
        )
        context['price_min_catalog'] = int(price_range['min_p'] or 0)
        context['price_max_catalog'] = int(price_range['max_p'] or 1000000)
        site_name = getattr(self.request, 'site_settings', None)
        site_name = getattr(site_name, 'site_name', '') or 'The Barbershop'
        seo_scope = 'productos de barbería'
        if context['selected_category_obj']:
            seo_scope = context['selected_category_obj'].name
        elif context['selected_brand_obj']:
            seo_scope = f"marca {context['selected_brand_obj'].name}"
        elif context['filter_q']:
            seo_scope = f"resultados para {context['filter_q']}"

        context['seo_shop_title'] = f"Tienda: {seo_scope} | {site_name}"
        context['seo_shop_description'] = (
            f"Explora {seo_scope} en {site_name}. "
            "Compara precios, encuentra ofertas y compra online de forma rápida y segura."
        )
        facet_filter_keys = {'q', 'category', 'brand', 'min_price', 'max_price', 'sort'}
        query_dict = self.request.GET.copy()
        has_facet_filters = any(query_dict.get(key) for key in facet_filter_keys)
        has_extra_params = any(
            key not in facet_filter_keys and key != 'page' for key in query_dict.keys()
        )
        page_obj = context.get('page_obj')
        is_paginated_page = bool(page_obj and page_obj.number > 1)

        canonical_url = self.request.build_absolute_uri(self.request.path)
        if not has_facet_filters and not has_extra_params and is_paginated_page:
            canonical_url = (
                f"{canonical_url}?{urlencode({'page': page_obj.number})}"
            )

        context['seo_shop_robots'] = (
            'noindex, follow' if (has_facet_filters or has_extra_params) else 'index, follow'
        )
        context['seo_shop_canonical_url'] = canonical_url
        context['seo_shop_prev_url'] = ''
        context['seo_shop_next_url'] = ''
        if (
            page_obj
            and not has_facet_filters
            and not has_extra_params
            and page_obj.paginator.num_pages > 1
        ):
            if page_obj.has_previous():
                prev_num = page_obj.previous_page_number()
                if prev_num == 1:
                    context['seo_shop_prev_url'] = self.request.build_absolute_uri(
                        self.request.path
                    )
                else:
                    context['seo_shop_prev_url'] = (
                        f"{self.request.build_absolute_uri(self.request.path)}"
                        f"?{urlencode({'page': prev_num})}"
                    )
            if page_obj.has_next():
                next_num = page_obj.next_page_number()
                context['seo_shop_next_url'] = (
                    f"{self.request.build_absolute_uri(self.request.path)}"
                    f"?{urlencode({'page': next_num})}"
                )
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/shop-details.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._track_unique_view(self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related(
            'images', 'variants', 'reviews'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['approved_reviews'] = self.object.reviews.filter(is_approved=True).order_by('-created_at')
        context['share_url'] = self.request.build_absolute_uri(self.request.path)
        stats = self.object.get_rating_stats()
        context['product_rating_stats'] = stats
        context['rating_stars'] = round(stats['average'])  # 0-5 para pintar estrellas
        context['product_schema_json'] = self._build_product_schema_json(
            self.object, context['approved_reviews'], context['share_url'], stats
        )
        context['product_breadcrumb_schema_json'] = self._build_breadcrumb_schema_json(
            self.object
        )
        context['is_favorite'] = False
        if self.request.user.is_authenticated:
            context['is_favorite'] = ProductFavorite.objects.filter(
                product=self.object, user=self.request.user
            ).exists()
        return context

    def _track_unique_view(self, product):
        """Cuenta una vista real (única) por usuario o sesión."""
        if self.request.user.is_authenticated:
            already_viewed = ProductView.objects.filter(
                product=product, user=self.request.user
            ).exists()
            if already_viewed:
                return
            create_kwargs = {
                'product': product,
                'user': self.request.user,
                'session_key': self.request.session.session_key or '',
            }
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            already_viewed = ProductView.objects.filter(
                product=product, user__isnull=True, session_key=session_key
            ).exists()
            if already_viewed:
                return
            create_kwargs = {
                'product': product,
                'session_key': session_key,
            }

        try:
            ProductView.objects.create(**create_kwargs)
        except IntegrityError:
            # Otra petición paralela pudo registrar la vista.
            return

        Product.objects.filter(pk=product.pk).update(
            view_count=models.F('view_count') + 1
        )
        product.refresh_from_db(fields=['view_count'])

    def _build_product_schema_json(self, product, approved_reviews, share_url, rating_stats):
        """Schema.org Product + AggregateRating + Review para SEO (JSON-LD)."""
        from apps.core.models import SiteSettings
        request = self.request
        base = f"{request.scheme}://{request.get_host()}"
        images = [f"{base}{img.image.url}" for img in product.images.all()[:5]]
        if not images and product.get_main_image():
            img = product.get_main_image()
            images = [f"{base}{img.image.url}"]
        description = product.short_description or product.name
        if product.description:
            description = Truncator(strip_tags(product.description)).words(50)
        currency = (SiteSettings.get().currency or "COP").strip() or "COP"
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product.name,
            "description": description,
            "url": share_url,
            "image": images,
            "offers": {
                "@type": "Offer",
                "price": str(product.price),
                "priceCurrency": currency,
                "availability": "https://schema.org/InStock" if product.in_stock else "https://schema.org/OutOfStock",
            },
        }
        if rating_stats["count"] > 0:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(rating_stats["average"]),
                "bestRating": "5",
                "worstRating": "1",
                "ratingCount": str(rating_stats["count"]),
            }
            schema["review"] = [
                {
                    "@type": "Review",
                    "author": {"@type": "Person", "name": r.author_name},
                    "datePublished": r.created_at.strftime("%Y-%m-%d"),
                    "reviewRating": {
                        "@type": "Rating",
                        "ratingValue": str(r.rating),
                        "bestRating": "5",
                        "worstRating": "1",
                    },
                    "reviewBody": r.comment[:500],
                }
                for r in approved_reviews[:10]
            ]
        return json.dumps(schema, ensure_ascii=False)

    def _build_breadcrumb_schema_json(self, product):
        request = self.request
        base = f"{request.scheme}://{request.get_host()}"
        shop_url = f"{base}{reverse('products:list')}"
        category = product.categories.filter(is_active=True).first()
        item_list = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Inicio",
                "item": f"{base}{reverse('core:home')}",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Tienda",
                "item": shop_url,
            },
        ]
        position = 3
        if category:
            item_list.append(
                {
                    "@type": "ListItem",
                    "position": position,
                    "name": category.name,
                    "item": f"{shop_url}?{urlencode({'category': category.slug})}",
                }
            )
            position += 1
        item_list.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": product.name,
                "item": self.request.build_absolute_uri(self.request.path),
            }
        )
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": item_list,
        }
        return json.dumps(schema, ensure_ascii=False)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.POST.get('action') == 'review':
            name = (request.POST.get('author_name') or '').strip()
            email = (request.POST.get('author_email') or '').strip()
            try:
                rating = min(5, max(1, int(request.POST.get('rating', 5))))
            except (TypeError, ValueError):
                rating = 5
            comment = (request.POST.get('comment') or '').strip()
            if name and email and comment:
                ProductReview.objects.create(
                    product=self.object,
                    user=request.user if request.user.is_authenticated else None,
                    author_name=name,
                    author_email=email,
                    rating=rating,
                    comment=comment,
                    is_approved=False,
                )
                messages.success(request, 'Gracias. Tu reseña se publicará tras revisión.')
            else:
                messages.warning(request, 'Completa nombre, email y comentario para enviar la reseña.')
            url = reverse('products:detail', kwargs={'slug': self.object.slug}) + '#product-reviews'
            return redirect(url)
        return self.get(request, *args, **kwargs)


@require_POST
def toggle_favorite_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    fallback = reverse('products:detail', kwargs={'slug': product.slug})
    next_url = _safe_next_url(
        request,
        request.POST.get('next') or request.META.get('HTTP_REFERER'),
        fallback,
    )
    if not request.user.is_authenticated:
        return redirect_to_login(next_url)

    favorite, created = ProductFavorite.objects.get_or_create(
        product=product, user=request.user
    )
    if created:
        messages.success(request, f'"{product.name}" se agregó a tus favoritos.')
    else:
        favorite.delete()
        messages.info(request, f'"{product.name}" se quitó de favoritos.')
    return redirect(next_url)
