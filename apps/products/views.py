import json
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.utils.html import strip_tags
from django.utils.text import Truncator

from .models import Product, Category, Brand, ProductReview


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
        context['filter_category'] = self.request.GET.get('category') or self.kwargs.get('category_slug', '')
        context['filter_brand'] = self.request.GET.get('brand', '')
        context['filter_min_price'] = self.request.GET.get('min_price', '')
        context['filter_max_price'] = self.request.GET.get('max_price', '')
        # Rango de precios en catálogo (para placeholder en el form)
        price_range = Product.objects.filter(is_active=True).aggregate(
            min_p=models.Min('regular_price'),
            max_p=models.Max('regular_price')
        )
        context['price_min_catalog'] = int(price_range['min_p'] or 0)
        context['price_max_catalog'] = int(price_range['max_p'] or 1000000)
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/shop-details.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

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
        return context

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
