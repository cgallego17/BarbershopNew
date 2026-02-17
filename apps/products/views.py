from django.db import models
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView

from .models import Product, Category


class ProductListView(ListView):
    model = Product
    template_name = 'products/shop.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).prefetch_related('categories', 'images')
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            qs = qs.filter(categories__slug=category_slug)
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
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
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
