"""Formularios para el panel de administración."""
from django import forms
from django.forms import inlineformset_factory
from django_ckeditor_5.widgets import CKEditor5Widget
from apps.core.html_sanitizer import sanitize_html

from apps.products.models import Product, Category, Brand, ProductAttribute, ProductAttributeValue, ProductVariant
from apps.orders.models import Order
from apps.coupons.models import Coupon
from apps.accounts.models import User
from apps.core.models import SiteSettings, HomeSection, HomeHeroSlide, HomeAboutBlock, HomeMeatCategoryBlock, HomeBrandBlock, HomeBrand, HomeTestimonial, HomePopupAnnouncement, Country, State, City, ShippingPrice
from apps.core.emails import notify_new_customer


def _add_form_control(form):
    from django_ckeditor_5.widgets import CKEditor5Widget
    for f in form.fields.values():
        if isinstance(f.widget, CKEditor5Widget):
            continue
        if 'class' not in f.widget.attrs:
            f.widget.attrs['class'] = 'form-control'
        elif 'form-control' not in f.widget.attrs['class']:
            f.widget.attrs['class'] += ' form-control'
        if isinstance(f.widget, forms.CheckboxInput):
            f.widget.attrs['class'] = f.widget.attrs.get('class', '').replace('form-control', 'form-check-input')


CKEDITOR_WIDGET = CKEditor5Widget(attrs={'class': 'django_ckeditor_5'})


class CategoryForm(forms.ModelForm):
    """Formulario de categoría."""

    class Meta:
        model = Category
        fields = ['name', 'slug', 'parent', 'description', 'image', 'order', 'is_active']
        widgets = {'description': CKEDITOR_WIDGET}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)

    def clean_description(self):
        return sanitize_html(self.cleaned_data.get('description'))


class ProductForm(forms.ModelForm):
    """Formulario de producto (campos principales)."""

    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'sku', 'codigo', 'external_id', 'description', 'short_description',
            'regular_price', 'sale_price', 'sale_price_start', 'sale_price_end',
            'wholesale_price', 'product_type', 'source', 'brand',
            'used_attributes', 'categories', 'is_active', 'is_featured',
            'manage_stock', 'stock_quantity', 'low_stock_threshold',
        ]
        widgets = {
            'description': CKEDITOR_WIDGET,
            'short_description': forms.TextInput(attrs={'placeholder': 'Descripción breve'}),
            'sale_price_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'sale_price_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)
        for f in ('sale_price_start', 'sale_price_end'):
            if f in self.fields:
                self.fields[f].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d']
        self.fields['used_attributes'].required = False
        self.fields['used_attributes'].help_text = 'Solo para productos variables.'
        self.fields['brand'].required = False

    def clean_description(self):
        return sanitize_html(self.cleaned_data.get('description'))


class BrandForm(forms.ModelForm):
    """Formulario de marca de catálogo."""

    class Meta:
        model = Brand
        fields = ['name', 'slug', 'logo', 'description', 'order', 'is_active']
        widgets = {'description': CKEDITOR_WIDGET}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)

    def clean_description(self):
        return sanitize_html(self.cleaned_data.get('description'))


class ProductAttributeForm(forms.ModelForm):
    """Formulario de atributo."""

    class Meta:
        model = ProductAttribute
        fields = ['name', 'slug', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)


class ProductAttributeValueForm(forms.ModelForm):
    """Formulario de valor de atributo."""

    class Meta:
        model = ProductAttributeValue
        fields = ['value', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)


ProductAttributeValueFormSet = inlineformset_factory(
    ProductAttribute, ProductAttributeValue,
    form=ProductAttributeValueForm, extra=1, can_delete=True
)


class ProductVariantForm(forms.ModelForm):
    """Formulario de variante."""

    class Meta:
        model = ProductVariant
        fields = [
            'sku', 'regular_price', 'sale_price', 'wholesale_price',
            'sale_price_start', 'sale_price_end',
            'stock_quantity', 'image', 'is_active'
        ]
        widgets = {
            'sale_price_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'sale_price_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)
        if product:
            for attr in product.used_attributes.all().prefetch_related('values'):
                choices = [('', '---')] + [(v.value, v.value) for v in attr.values.all()]
                self.fields[f'attr_{attr.slug}'] = forms.ChoiceField(
                    label=attr.name, choices=choices, required=True
                )
                if self.instance and self.instance.pk and self.instance.attributes:
                    val = self.instance.attributes.get(attr.slug, '')
                    self.initial[f'attr_{attr.slug}'] = val
        for f in ('sale_price_start', 'sale_price_end'):
            if f in self.fields:
                self.fields[f].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d']

    def get_attributes_json(self):
        if not getattr(self, 'cleaned_data', None):
            return {}
        return {
            k.replace('attr_', ''): v
            for k, v in self.cleaned_data.items()
            if k.startswith('attr_') and v
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'cleaned_data') and self.cleaned_data:
            instance.attributes = self.get_attributes_json()
        if commit:
            instance.save()
        return instance


def get_product_variant_formset(product, data=None, files=None):
    """Retorna el formset de variantes para un producto."""
    FormSet = inlineformset_factory(
        Product, ProductVariant,
        form=ProductVariantForm,
        extra=1, can_delete=True, max_num=50
    )
    return FormSet(data or None, files or None, instance=product, form_kwargs={'product': product})


class CustomerForm(forms.ModelForm):
    """Formulario para editar cliente. Username se genera automático desde email."""

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name',
            'role', 'phone', 'address', 'city', 'state', 'country', 'postal_code',
            'is_active'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)
        self.fields['role'].help_text = 'Cliente: compras normales. Mayorista: panel con precios especiales. Staff: dashboard. Admin: todo.'
        self.fields['country'].widget = forms.Select(choices=[('', '---------')] + [(c.name, c.name) for c in Country.objects.all().order_by('name')])
        self.fields['state'].widget = forms.Select(choices=[('', 'Seleccione departamento...')])
        self.fields['state'].widget.attrs['data-geo'] = 'state'
        self.fields['city'].widget = forms.Select(choices=[('', 'Seleccione ciudad...')])
        self.fields['city'].widget.attrs['data-geo'] = 'city'


class CustomerCreateForm(forms.ModelForm):
    """Formulario para crear cliente. Username se genera automático desde email."""

    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name',
            'role', 'phone', 'address', 'city', 'state', 'country', 'postal_code',
            'is_active'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)
        self.fields['role'].help_text = 'Cliente: compras normales. Mayorista: panel con precios especiales. Staff: dashboard. Admin: todo.'
        self.fields['country'].widget = forms.Select(choices=[('', '---------')] + [(c.name, c.name) for c in Country.objects.all().order_by('name')])
        self.fields['state'].widget = forms.Select(choices=[('', 'Seleccione departamento...')])
        self.fields['state'].widget.attrs['data-geo'] = 'state'
        self.fields['city'].widget = forms.Select(choices=[('', 'Seleccione ciudad...')])
        self.fields['city'].widget.attrs['data-geo'] = 'city'

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.username and user.email:
            user.username = (user.email or '').lower()[:150]
            if user.__class__.objects.filter(username=user.username).exists():
                import uuid
                user.username = f"{user.email.split('@')[0]}_{uuid.uuid4().hex[:8]}"[:150]
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            try:
                notify_new_customer(user)
            except Exception:
                pass
        return user


class OrderStatusForm(forms.ModelForm):
    """Formulario para actualizar estado del pedido."""

    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'notes']
        widgets = {'notes': CKEDITOR_WIDGET}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)

    def clean_notes(self):
        return sanitize_html(self.cleaned_data.get('notes'))


class CouponForm(forms.ModelForm):
    """Formulario de cupón."""

    class Meta:
        model = Coupon
        fields = [
            'code', 'discount_type', 'discount_value',
            'minimum_amount', 'maximum_amount',
            'usage_limit', 'date_start', 'date_end', 'is_active',
        ]
        widgets = {
            'date_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'date_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)
        if not self.instance or not self.instance.pk:
            self.fields['code'].required = False
            attrs = self.fields['code'].widget.attrs
            if 'placeholder' not in attrs:
                attrs['placeholder'] = 'Vacío = se genera automáticamente'
        for f in ('date_start', 'date_end'):
            if f in self.fields:
                self.fields[f].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d']


class SiteSettingsForm(forms.ModelForm):
    """Formulario de configuración del sitio."""

    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'tagline', 'logo',
            'topbar_marquee_text',
            'email', 'phone', 'whatsapp',
            'address', 'city', 'state', 'country', 'postal_code',
            'business_hours',
            'facebook_url', 'instagram_url', 'twitter_url', 'youtube_url', 'tiktok_url',
            'show_out_of_stock_products',
            'maintenance_mode',
            'maintenance_message',
            'about_text', 'currency',
            'terms_url', 'privacy_url',
            'meta_description',
        ]
        widgets = {
            'about_text': CKEDITOR_WIDGET,
            'meta_description': forms.Textarea(attrs={'rows': 2}),
            'topbar_marquee_text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej: Envíos a todo el país • Ofertas esta semana • Contáctanos por WhatsApp'}),
            'show_out_of_stock_products': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Estamos mejorando el sitio. Volvemos muy pronto.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)
        # País: opciones desde la base de datos
        select_attrs = {'class': 'form-control'}
        countries = Country.objects.all().order_by('name')
        self.fields['country'].widget = forms.Select(
            choices=[('', '---------')] + [(c.name, c.name) for c in countries],
            attrs=select_attrs
        )
        # Estado y ciudad: opciones desde la base según país/estado guardados
        state_choices = [('', 'Seleccione departamento...')]
        city_choices = [('', 'Seleccione ciudad...')]
        if self.instance and self.instance.pk and self.instance.country:
            country = Country.objects.filter(name=self.instance.country.strip()).first()
            if country:
                states = State.objects.filter(country=country).order_by('name')
                state_choices += [(s.name, s.name) for s in states]
                if self.instance.state:
                    state_obj = State.objects.filter(country=country, name=self.instance.state.strip()).first()
                    if state_obj:
                        cities = City.objects.filter(state=state_obj).order_by('name')
                        city_choices += [(c.name, c.name) for c in cities]
        self.fields['state'].widget = forms.Select(choices=state_choices, attrs={**select_attrs, 'data-geo': 'state'})
        self.fields['city'].widget = forms.Select(choices=city_choices, attrs={**select_attrs, 'data-geo': 'city'})

    def clean_about_text(self):
        return sanitize_html(self.cleaned_data.get('about_text'))


# --- Formularios Secciones del Home ---

class HomeSectionForm(forms.ModelForm):
    class Meta:
        model = HomeSection
        fields = ['order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)


class HomeHeroSlideForm(forms.ModelForm):
    class Meta:
        model = HomeHeroSlide
        fields = ['title', 'subtitle', 'text', 'image', 'shape_image', 'button_text', 'button_url', 'video_url', 'order']
        widgets = {'text': CKEDITOR_WIDGET}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)

    def clean_text(self):
        return sanitize_html(self.cleaned_data.get('text'))


class HomePopupAnnouncementForm(forms.ModelForm):
    class Meta:
        model = HomePopupAnnouncement
        fields = ['is_active', 'title', 'content', 'image', 'button_text', 'button_url']
        widgets = {'content': CKEDITOR_WIDGET}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)

    def clean_content(self):
        return sanitize_html(self.cleaned_data.get('content'))


class HomeAboutBlockForm(forms.ModelForm):
    class Meta:
        model = HomeAboutBlock
        fields = [
            'title', 'subtitle', 'content',
            'image1', 'image2', 'experience_years',
            'button_text', 'button_url',
        ]
        widgets = {'content': CKEDITOR_WIDGET}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)

    def clean_content(self):
        return sanitize_html(self.cleaned_data.get('content'))


class HomeMeatCategoryBlockForm(forms.ModelForm):
    class Meta:
        model = HomeMeatCategoryBlock
        fields = ['tagline', 'title', 'top_image', 'background_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)


class HomeBrandBlockForm(forms.ModelForm):
    class Meta:
        model = HomeBrandBlock
        fields = ['background_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)


class HomeBrandForm(forms.ModelForm):
    class Meta:
        model = HomeBrand
        fields = ['name', 'logo', 'url', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)


class HomeTestimonialForm(forms.ModelForm):
    class Meta:
        model = HomeTestimonial
        fields = ['name', 'designation', 'text', 'image', 'order']
        widgets = {'text': CKEDITOR_WIDGET}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)

    def clean_text(self):
        return sanitize_html(self.cleaned_data.get('text'))


class ShippingPriceForm(forms.ModelForm):
    """Formulario de precio de envío por ciudad. Departamento + ciudad en cascada con autocomplete."""

    state = forms.ModelChoiceField(
        label='Departamento / Estado',
        queryset=State.objects.select_related('country').order_by('country__name', 'name'),
        required=False,
        empty_label='Seleccione departamento primero'
    )

    class Meta:
        model = ShippingPrice
        fields = ['city', 'price', 'delivery_days_min', 'delivery_days_max', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)
        self.fields['state'].widget.attrs['id'] = 'id_shipping_state'
        self.fields['city'].widget.attrs['id'] = 'id_shipping_city'
        self.fields['city'].empty_label = 'Seleccione ciudad'
        self.fields['city'].required = True
        # Queryset de city se ajusta en la vista según state (POST o instance)
        if self.data.get('state'):
            self.fields['city'].queryset = City.objects.filter(
                state_id=self.data.get('state')
            ).order_by('name')
            used = ShippingPrice.objects.values_list('city_id', flat=True)
            if not self.instance.pk:
                self.fields['city'].queryset = self.fields['city'].queryset.exclude(pk__in=used)
        elif self.instance and self.instance.pk and self.instance.city_id:
            self.fields['state'].initial = self.instance.city.state_id
            self.fields['city'].queryset = City.objects.filter(
                state_id=self.instance.city.state_id
            ).order_by('name')
        else:
            self.fields['city'].queryset = City.objects.none()

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if not city:
            return city
        qs = ShippingPrice.objects.filter(city=city)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Esta ciudad ya tiene un precio de envío configurado.')
        return city

    def clean(self):
        data = super().clean()
        d_min = data.get('delivery_days_min')
        d_max = data.get('delivery_days_max')
        if d_min is not None and d_max is not None and d_min > d_max:
            raise forms.ValidationError('El mínimo de días no puede ser mayor que el máximo.')
        return data


class ShippingFreeRuleForm(forms.ModelForm):
    """Formulario para configurar el umbral de envío gratis."""

    class Meta:
        model = SiteSettings
        fields = ['free_shipping_min_amount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_form_control(self)
