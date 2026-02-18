"""Vistas CRUD del panel de administración (sin Django Admin)."""
import io
from django.db import models
from django.db.models import Q, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages

from apps.products.models import Product, Category, Brand, ProductAttribute
from apps.orders.models import Order
from apps.coupons.models import Coupon
from apps.accounts.models import User
from .forms import (
    CategoryForm, BrandForm, ProductForm, OrderStatusForm, CouponForm,
    ProductAttributeForm, ProductAttributeValueFormSet,
    get_product_variant_formset, CustomerForm, CustomerCreateForm, SiteSettingsForm,
    HomeSectionForm, HomeHeroSlideForm, HomeAboutBlockForm, HomeMeatCategoryBlockForm, HomeBrandForm, HomeTestimonialForm,
    ShippingPriceForm,
)
from .models import SiteSettings, HomeSection, HomeHeroSlide, HomeAboutBlock, HomeMeatCategoryBlock, HomeBrand, HomeTestimonial, ShippingPrice, Country, City


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin que requiere rol staff o admin (acceso al panel de administración)."""

    def test_func(self):
        return getattr(self.request.user, 'can_access_dashboard', False)


def _dashboard_required(view):
    """Decorador: requiere can_access_dashboard (staff o admin)."""
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not getattr(request.user, 'can_access_dashboard', False):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Sin acceso')
        return view(request, *args, **kwargs)
    return wrapped


# --- Categorías ---

class CategoryListView(StaffRequiredMixin, ListView):
    model = Category
    template_name = 'dashboard/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        return Category.objects.annotate(
            product_count=Count('products')
        ).order_by('order', 'name')


class CategoryProductListView(StaffRequiredMixin, ListView):
    """Lista los productos de una categoría (al hacer clic en el contador)."""
    model = Product
    template_name = 'dashboard/category_products.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        self.category = get_object_or_404(Category, pk=self.kwargs['pk'])
        return self.category.products.all().select_related('brand').order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category'] = self.category
        return ctx


class CategoryCreateView(StaffRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('admin_panel:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría creada correctamente.')
        return super().form_valid(form)


class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    context_object_name = 'category'
    success_url = reverse_lazy('admin_panel:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría actualizada correctamente.')
        return super().form_valid(form)


class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Category
    template_name = 'dashboard/category_confirm_delete.html'
    context_object_name = 'category'
    success_url = reverse_lazy('admin_panel:category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Categoría eliminada.')
        return super().delete(request, *args, **kwargs)


@_dashboard_required
def category_toggle_active_view(request, pk):
    """Activa o inactiva una categoría."""
    if request.method != 'POST':
        return redirect('admin_panel:category_list')
    category = get_object_or_404(Category, pk=pk)
    category.is_active = not category.is_active
    category.save()
    action = 'activada' if category.is_active else 'inactivada'
    messages.success(request, f'Categoría «{category.name}» {action} correctamente.')
    return redirect('admin_panel:category_list')


# --- Marcas (catálogo) ---

class BrandListView(StaffRequiredMixin, ListView):
    model = Brand
    template_name = 'dashboard/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 20

    def get_queryset(self):
        return Brand.objects.annotate(
            product_count=models.Count('products')
        ).order_by('order', 'name')


class BrandCreateView(StaffRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'dashboard/brand_form.html'
    success_url = reverse_lazy('admin_panel:brand_list')

    def form_valid(self, form):
        messages.success(self.request, 'Marca creada correctamente.')
        return super().form_valid(form)


class BrandUpdateView(StaffRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'dashboard/brand_form.html'
    context_object_name = 'brand'
    success_url = reverse_lazy('admin_panel:brand_list')

    def form_valid(self, form):
        messages.success(self.request, 'Marca actualizada correctamente.')
        return super().form_valid(form)


class BrandDeleteView(StaffRequiredMixin, DeleteView):
    model = Brand
    template_name = 'dashboard/brand_confirm_delete.html'
    context_object_name = 'brand'
    success_url = reverse_lazy('admin_panel:brand_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Marca eliminada.')
        return super().delete(request, *args, **kwargs)


# --- Atributos ---

class AttributeListView(StaffRequiredMixin, ListView):
    model = ProductAttribute
    template_name = 'dashboard/attribute_list.html'
    context_object_name = 'attributes'
    paginate_by = 20


class AttributeCreateView(StaffRequiredMixin, CreateView):
    model = ProductAttribute
    form_class = ProductAttributeForm
    template_name = 'dashboard/attribute_form.html'
    success_url = reverse_lazy('admin_panel:attribute_list')

    def form_valid(self, form):
        messages.success(self.request, 'Atributo creado. Agrega sus valores editándolo.')
        return super().form_valid(form)


class AttributeUpdateView(StaffRequiredMixin, UpdateView):
    model = ProductAttribute
    form_class = ProductAttributeForm
    template_name = 'dashboard/attribute_form.html'
    context_object_name = 'attribute'
    success_url = reverse_lazy('admin_panel:attribute_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            ctx['value_formset'] = ProductAttributeValueFormSet(
                self.request.POST, instance=self.object
            )
        else:
            ctx['value_formset'] = ProductAttributeValueFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data(form=form)
        value_formset = ctx['value_formset']
        if value_formset.is_valid():
            form.save()
            value_formset.save()
            messages.success(self.request, 'Atributo y valores actualizados.')
            return redirect(self.success_url)
        return self.render_to_response(ctx)


class AttributeDeleteView(StaffRequiredMixin, DeleteView):
    model = ProductAttribute
    template_name = 'dashboard/attribute_confirm_delete.html'
    context_object_name = 'attribute'
    success_url = reverse_lazy('admin_panel:attribute_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Atributo eliminado.')
        return super().delete(request, *args, **kwargs)


# --- Productos ---

class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'dashboard/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('brand').prefetch_related('categories', 'images')
        search = (self.request.GET.get('q') or '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(codigo__icontains=search) |
                Q(short_description__icontains=search)
            )
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(categories__id=category).distinct()
        brand = self.request.GET.get('brand')
        if brand:
            qs = qs.filter(brand_id=brand)
        product_type = self.request.GET.get('type')
        if product_type:
            qs = qs.filter(product_type=product_type)
        featured = self.request.GET.get('featured')
        if featured == '1':
            qs = qs.filter(is_featured=True)
        elif featured == '0':
            qs = qs.filter(is_featured=False)
        sort = self.request.GET.get('sort', '-created_at')
        allowed_sort = {'name': 'name', '-name': '-name', 'price': 'regular_price', '-price': '-regular_price',
                       'created': '-created_at', '-created': 'created_at', 'sku': 'sku'}
        order = allowed_sort.get(sort, '-created_at')
        return qs.order_by(order)

    def get_context_data(self, **kwargs):
        from apps.products.models import Category, Brand
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(is_active=True).order_by('name')
        ctx['brands'] = Brand.objects.filter(is_active=True).order_by('name')
        return ctx


@_dashboard_required
def sync_tersa_products_view(request):
    """Importa productos desde API Tersa (solo BARBERSHOP y BARBER UP)."""
    if request.method != 'POST':
        return redirect('admin_panel:product_list')
    try:
        from apps.integrations.services import sync_tersa_products
        result = sync_tersa_products(brands=['BARBERSHOP', 'BARBER UP'], download_images=True)
        messages.success(
            request,
            f'Tersa: {result["total"]} productos (BARBERSHOP, BARBER UP). '
            f'{result["created"]} creados, {result["updated"]} actualizados.'
        )
    except Exception as e:
        messages.error(request, f'Error al sincronizar Tersa: {e}')
    return redirect('admin_panel:product_list')


class ProductCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('admin_panel:product_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Producto creado. Edita el producto para agregar variantes si es variable.')
        return redirect('admin_panel:product_edit', pk=self.object.pk)


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    context_object_name = 'product'
    success_url = reverse_lazy('admin_panel:product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object
        if product and product.product_type == 'variable':
            ctx['variant_formset'] = get_product_variant_formset(
                product,
                data=self.request.POST if self.request.method == 'POST' else None,
                files=self.request.FILES if self.request.method == 'POST' else None
            )
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        product = self.object
        if product.product_type == 'variable':
            formset = get_product_variant_formset(product, data=self.request.POST, files=self.request.FILES)
            if formset.is_valid():
                formset.save()
                messages.success(self.request, 'Producto y variantes actualizados.')
            else:
                messages.warning(self.request, 'Producto guardado pero hay errores en las variantes.')
        else:
            product.variants.all().delete()
            messages.success(self.request, 'Producto actualizado correctamente.')
        return response


@_dashboard_required
def product_toggle_active_view(request, pk):
    """Activa o inactiva un producto."""
    if request.method != 'POST':
        return redirect('admin_panel:product_list')
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    action = 'activado' if product.is_active else 'inactivado'
    messages.success(request, f'Producto {action} correctamente.')
    return redirect('admin_panel:product_list')


class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'dashboard/product_confirm_delete.html'
    context_object_name = 'product'
    success_url = reverse_lazy('admin_panel:product_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Producto eliminado.')
        return super().delete(request, *args, **kwargs)


# --- Clientes ---

class CustomerListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'dashboard/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 25

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                models.Q(username__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs


class CustomerCreateView(StaffRequiredMixin, CreateView):
    model = User
    form_class = CustomerCreateForm
    template_name = 'dashboard/customer_form.html'
    success_url = reverse_lazy('admin_panel:customer_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import Country
        import json
        ctx['geo_countries_json'] = json.dumps([{'id': c.id, 'name': c.name} for c in Country.objects.all().order_by('name')])
        ctx['geo_states_url'] = reverse('geo_states')
        ctx['geo_cities_url'] = reverse('geo_cities')
        ctx['initial_state'] = ''
        ctx['initial_city'] = ''
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado correctamente.')
        return super().form_valid(form)


@_dashboard_required
def customer_detail_view(request, pk):
    """Detalle de cliente con sus pedidos."""
    from django.db.models import Sum
    customer = get_object_or_404(User.objects.prefetch_related('orders'), pk=pk)
    orders = customer.orders.all().order_by('-created_at')[:20]
    total_spent = customer.orders.filter(
        status__in=['completed', 'processing']
    ).aggregate(Sum('total'))['total__sum'] or 0
    return render(request, 'dashboard/customer_detail.html', {
        'customer': customer,
        'orders': orders,
        'total_spent': total_spent,
    })


class CustomerUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = CustomerForm
    template_name = 'dashboard/customer_form.html'
    context_object_name = 'customer'
    success_url = reverse_lazy('admin_panel:customer_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import Country
        import json
        ctx['geo_countries_json'] = json.dumps([{'id': c.id, 'name': c.name} for c in Country.objects.all().order_by('name')])
        ctx['geo_states_url'] = reverse('geo_states')
        ctx['geo_cities_url'] = reverse('geo_cities')
        customer = ctx.get('customer')
        ctx['initial_state'] = getattr(customer, 'state', '') or ''
        ctx['initial_city'] = getattr(customer, 'city', '') or ''
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado correctamente.')
        return super().form_valid(form)


# --- Pedidos ---

class OrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = 'dashboard/order_list.html'
    context_object_name = 'orders'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('user')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                order_number__icontains=search
            ) | qs.filter(billing_email__icontains=search)
        return qs.order_by('-created_at')


@_dashboard_required
def order_detail_view(request, pk):
    """Detalle y actualización de pedido."""
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pedido actualizado.')
            return redirect('admin_panel:order_detail', pk=order.pk)
    else:
        form = OrderStatusForm(instance=order)
    return render(request, 'dashboard/order_detail.html', {'order': order, 'form': form})


# --- Cupones ---

class CouponListView(StaffRequiredMixin, ListView):
    model = Coupon
    template_name = 'dashboard/coupon_list.html'
    context_object_name = 'coupons'
    paginate_by = 20


class CouponCreateView(StaffRequiredMixin, CreateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'dashboard/coupon_form.html'
    success_url = reverse_lazy('admin_panel:coupon_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cupón creado correctamente.')
        return super().form_valid(form)


class CouponUpdateView(StaffRequiredMixin, UpdateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'dashboard/coupon_form.html'
    context_object_name = 'coupon'
    success_url = reverse_lazy('admin_panel:coupon_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cupón actualizado correctamente.')
        return super().form_valid(form)


class CouponDeleteView(StaffRequiredMixin, DeleteView):
    model = Coupon
    template_name = 'dashboard/coupon_confirm_delete.html'
    context_object_name = 'coupon'
    success_url = reverse_lazy('admin_panel:coupon_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cupón eliminado.')
        return super().delete(request, *args, **kwargs)


# --- Precios de envío por ciudad ---

class ShippingPriceListView(StaffRequiredMixin, ListView):
    model = ShippingPrice
    template_name = 'dashboard/shipping_price_list.html'
    context_object_name = 'shipping_prices'
    paginate_by = 25

    def get_queryset(self):
        return ShippingPrice.objects.select_related('city', 'city__state', 'city__state__country').order_by('city__state__name', 'city__name')


@_dashboard_required
def shipping_price_export_excel_view(request):
    """Exporta todos los precios de envío a Excel (.xlsx). Requiere openpyxl."""
    from django.utils import timezone

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
    except ModuleNotFoundError:
        messages.error(
            request,
            'Para exportar en Excel debe instalar openpyxl. '
            'En la misma terminal donde ejecuta el servidor (runserver), ejecute: pip install openpyxl '
            'y luego reinicie el servidor.'
        )
        return redirect('admin_panel:shipping_price_list')

    qs = ShippingPrice.objects.select_related('city', 'city__state', 'city__state__country').order_by('city__state__name', 'city__name')
    timestamp = timezone.now().strftime('%Y%m%d-%H%M')

    wb = Workbook()
    ws = wb.active
    ws.title = 'Precios de envío'
    headers = ['Ciudad', 'Departamento', 'País', 'Precio', 'Días mín', 'Días máx', 'Estado']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    for row, sp in enumerate(qs, 2):
        ws.cell(row=row, column=1, value=sp.city.name)
        ws.cell(row=row, column=2, value=sp.city.state.name)
        ws.cell(row=row, column=3, value=sp.city.state.country.name)
        ws.cell(row=row, column=4, value=float(sp.price))
        ws.cell(row=row, column=5, value=sp.delivery_days_min)
        ws.cell(row=row, column=6, value=sp.delivery_days_max)
        ws.cell(row=row, column=7, value='Activo' if sp.is_active else 'Inactivo')
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f'precios-envio-{timestamp}.xlsx'
    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@_dashboard_required
def shipping_price_load_all_colombia_view(request):
    """Crea precio de envío (0, 0-0 días) para todas las ciudades de Colombia que aún no tengan uno."""
    if request.method != 'POST':
        return redirect('admin_panel:shipping_price_list')
    try:
        colombia = Country.objects.get(name='Colombia')
    except Country.DoesNotExist:
        messages.error(request, 'No existe el país Colombia. Ejecute: python manage.py load_colombia_geo')
        return redirect('admin_panel:shipping_price_list')
    cities = City.objects.filter(state__country=colombia).select_related('state')
    created = 0
    for city in cities:
        _, created_flag = ShippingPrice.objects.get_or_create(
            city=city,
            defaults={
                'price': 0,
                'delivery_days_min': 0,
                'delivery_days_max': 0,
                'is_active': True,
            }
        )
        if created_flag:
            created += 1
    messages.success(request, f'Se agregaron {created} ciudades de Colombia con precio 0 y días 0-0. ({cities.count() - created} ya existían.)')
    return redirect('admin_panel:shipping_price_list')


class ShippingPriceCreateView(StaffRequiredMixin, CreateView):
    model = ShippingPrice
    form_class = ShippingPriceForm
    template_name = 'dashboard/shipping_price_form.html'
    success_url = reverse_lazy('admin_panel:shipping_price_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['geo_cities_url'] = reverse('geo_cities')
        ctx['initial_state_id'] = ''
        ctx['initial_city_id'] = ''
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Precio de envío agregado correctamente.')
        return super().form_valid(form)


class ShippingPriceUpdateView(StaffRequiredMixin, UpdateView):
    model = ShippingPrice
    form_class = ShippingPriceForm
    template_name = 'dashboard/shipping_price_form.html'
    context_object_name = 'shipping_price'
    success_url = reverse_lazy('admin_panel:shipping_price_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['geo_cities_url'] = reverse('geo_cities')
        obj = ctx.get('shipping_price')
        if obj and obj.city_id:
            ctx['initial_state_id'] = obj.city.state_id
            ctx['initial_city_id'] = obj.city_id
        else:
            ctx['initial_state_id'] = ''
            ctx['initial_city_id'] = ''
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Precio de envío actualizado.')
        return super().form_valid(form)


class ShippingPriceDeleteView(StaffRequiredMixin, DeleteView):
    model = ShippingPrice
    template_name = 'dashboard/shipping_price_confirm_delete.html'
    context_object_name = 'shipping_price'
    success_url = reverse_lazy('admin_panel:shipping_price_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Precio de envío eliminado.')
        return super().delete(request, *args, **kwargs)


# --- Configuración del sitio ---

class SiteSettingsUpdateView(StaffRequiredMixin, UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'dashboard/config_form.html'
    context_object_name = 'settings'
    success_url = reverse_lazy('admin_panel:config')

    def get_object(self, queryset=None):
        return SiteSettings.get()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import Country
        import json
        ctx['geo_countries_json'] = json.dumps([{'id': c.id, 'name': c.name} for c in Country.objects.all().order_by('name')])
        ctx['geo_states_url'] = reverse('geo_states')
        ctx['geo_cities_url'] = reverse('geo_cities')
        obj = ctx.get('settings')
        ctx['initial_state'] = getattr(obj, 'state', '') or ''
        ctx['initial_city'] = getattr(obj, 'city', '') or ''
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Configuración guardada correctamente.')
        return super().form_valid(form)


# --- Secciones del Home ---

class HomeSectionsConfigView(StaffRequiredMixin, ListView):
    """Vista principal de administración de secciones del home."""
    model = HomeSection
    template_name = 'dashboard/home_sections_config.html'
    context_object_name = 'sections'

    def get_queryset(self):
        return HomeSection.objects.all().order_by('order')

    def get_context_data(self, **kwargs):
        from django.forms import modelformset_factory
        from .forms import HomeSectionForm
        ctx = super().get_context_data(**kwargs)
        FormSet = modelformset_factory(HomeSection, form=HomeSectionForm, extra=0)
        ctx['formset'] = kwargs.get('formset') or FormSet(queryset=self.get_queryset())
        ctx['hero_slides_count'] = HomeHeroSlide.objects.count()
        ctx['brands_count'] = Brand.objects.count()
        ctx['testimonials_count'] = HomeTestimonial.objects.count()
        return ctx

    def post(self, request, *args, **kwargs):
        from django.forms import modelformset_factory
        from .forms import HomeSectionForm
        self.object_list = self.get_queryset()
        FormSet = modelformset_factory(HomeSection, form=HomeSectionForm, extra=0)
        formset = FormSet(request.POST, queryset=self.get_queryset())
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Configuración de secciones guardada.')
            return redirect('admin_panel:home_sections')
        return self.render_to_response(self.get_context_data(formset=formset))


class HomeHeroSlideListView(StaffRequiredMixin, ListView):
    model = HomeHeroSlide
    template_name = 'dashboard/home_hero_list.html'
    context_object_name = 'slides'


class HomeHeroSlideCreateView(StaffRequiredMixin, CreateView):
    model = HomeHeroSlide
    form_class = HomeHeroSlideForm
    template_name = 'dashboard/home_hero_form.html'
    success_url = reverse_lazy('admin_panel:home_hero_list')

    def form_valid(self, form):
        messages.success(self.request, 'Slide creado.')
        return super().form_valid(form)


class HomeHeroSlideUpdateView(StaffRequiredMixin, UpdateView):
    model = HomeHeroSlide
    form_class = HomeHeroSlideForm
    template_name = 'dashboard/home_hero_form.html'
    context_object_name = 'slide'
    success_url = reverse_lazy('admin_panel:home_hero_list')

    def form_valid(self, form):
        messages.success(self.request, 'Slide actualizado.')
        return super().form_valid(form)


class HomeHeroSlideDeleteView(StaffRequiredMixin, DeleteView):
    model = HomeHeroSlide
    template_name = 'dashboard/home_hero_confirm_delete.html'
    context_object_name = 'slide'
    success_url = reverse_lazy('admin_panel:home_hero_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Slide eliminado.')
        return super().delete(request, *args, **kwargs)


class HomeAboutBlockUpdateView(StaffRequiredMixin, UpdateView):
    model = HomeAboutBlock
    form_class = HomeAboutBlockForm
    template_name = 'dashboard/home_about_form.html'
    context_object_name = 'block'
    success_url = reverse_lazy('admin_panel:home_sections')

    def get_object(self, queryset=None):
        return HomeAboutBlock.get()

    def form_valid(self, form):
        messages.success(self.request, 'Bloque sobre nosotros actualizado.')
        return super().form_valid(form)


class HomeMeatCategoryBlockUpdateView(StaffRequiredMixin, UpdateView):
    model = HomeMeatCategoryBlock
    form_class = HomeMeatCategoryBlockForm
    template_name = 'dashboard/home_meat_category_form.html'
    context_object_name = 'block'
    success_url = reverse_lazy('admin_panel:home_sections')

    def get_object(self, queryset=None):
        return HomeMeatCategoryBlock.get()

    def form_valid(self, form):
        messages.success(self.request, 'Sección categorías actualizada.')
        return super().form_valid(form)


class HomeBrandListView(StaffRequiredMixin, ListView):
    """Lista las marcas del modelo de producto (Brand), no HomeBrand."""
    model = Brand
    template_name = 'dashboard/home_brand_list.html'
    context_object_name = 'brands'
    queryset = Brand.objects.all()


class HomeBrandCreateView(StaffRequiredMixin, CreateView):
    model = HomeBrand
    form_class = HomeBrandForm
    template_name = 'dashboard/home_brand_form.html'
    success_url = reverse_lazy('admin_panel:home_brand_list')

    def form_valid(self, form):
        messages.success(self.request, 'Marca creada.')
        return super().form_valid(form)


class HomeBrandUpdateView(StaffRequiredMixin, UpdateView):
    model = HomeBrand
    form_class = HomeBrandForm
    template_name = 'dashboard/home_brand_form.html'
    context_object_name = 'brand'
    success_url = reverse_lazy('admin_panel:home_brand_list')

    def form_valid(self, form):
        messages.success(self.request, 'Marca actualizada.')
        return super().form_valid(form)


class HomeBrandDeleteView(StaffRequiredMixin, DeleteView):
    model = HomeBrand
    template_name = 'dashboard/home_brand_confirm_delete.html'
    context_object_name = 'brand'
    success_url = reverse_lazy('admin_panel:home_brand_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Marca eliminada.')
        return super().delete(request, *args, **kwargs)


class HomeTestimonialListView(StaffRequiredMixin, ListView):
    model = HomeTestimonial
    template_name = 'dashboard/home_testimonial_list.html'
    context_object_name = 'testimonials'


class HomeTestimonialCreateView(StaffRequiredMixin, CreateView):
    model = HomeTestimonial
    form_class = HomeTestimonialForm
    template_name = 'dashboard/home_testimonial_form.html'
    success_url = reverse_lazy('admin_panel:home_testimonial_list')

    def form_valid(self, form):
        messages.success(self.request, 'Testimonio creado.')
        return super().form_valid(form)


class HomeTestimonialUpdateView(StaffRequiredMixin, UpdateView):
    model = HomeTestimonial
    form_class = HomeTestimonialForm
    template_name = 'dashboard/home_testimonial_form.html'
    context_object_name = 'testimonial'
    success_url = reverse_lazy('admin_panel:home_testimonial_list')

    def form_valid(self, form):
        messages.success(self.request, 'Testimonio actualizado.')
        return super().form_valid(form)


class HomeTestimonialDeleteView(StaffRequiredMixin, DeleteView):
    model = HomeTestimonial
    template_name = 'dashboard/home_testimonial_confirm_delete.html'
    context_object_name = 'testimonial'
    success_url = reverse_lazy('admin_panel:home_testimonial_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Testimonio eliminado.')
        return super().delete(request, *args, **kwargs)
