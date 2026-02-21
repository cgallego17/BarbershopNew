from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm, LoginForm, ResetPasswordForm
from apps.core.security import log_security_event
from apps.core.emails import notify_new_customer

from .models import User, UserAddress


class CustomSignupForm(SignupForm):
    """Registro con datos completos para persona o empresa."""
    CUSTOMER_TYPE_CHOICES = [
        ('person', _('Persona natural')),
        ('company', _('Empresa')),
    ]

    first_name = forms.CharField(
        max_length=150,
        label=_('Nombre'),
        widget=forms.TextInput(attrs={'placeholder': _('Nombre')})
    )
    last_name = forms.CharField(
        max_length=150,
        label=_('Apellido'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Apellido')})
    )
    customer_type = forms.ChoiceField(
        choices=CUSTOMER_TYPE_CHOICES,
        label=_('Registrarse como'),
        initial='person'
    )
    DOCUMENT_TYPE_CHOICES = [
        ('', _('-- Seleccione --')),
        ('CC', _('Cédula de ciudadanía')),
        ('CE', _('Cédula de extranjería')),
        ('PA', _('Pasaporte')),
    ]
    document_type = forms.ChoiceField(
        choices=DOCUMENT_TYPE_CHOICES,
        label=_('Tipo de documento'),
        required=False
    )
    document_number = forms.CharField(
        max_length=30,
        label=_('Número de identificación'),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': _('Cédula, NIT, etc.')})
    )
    phone = forms.CharField(
        max_length=20,
        label=_('Teléfono'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Teléfono')})
    )
    date_of_birth = forms.DateField(
        label=_('Fecha de nacimiento'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean(self):
        data = super().clean()
        if (data.get('website') or '').strip():
            log_security_event(
                getattr(self, 'request', None),
                event_type='auth_honeypot',
                source='signup',
                details={'reason': 'honeypot_field_filled'},
            )
            raise forms.ValidationError(_('No fue posible procesar el registro.'))
        customer_type = data.get('customer_type', 'person')
        if customer_type == 'person':
            if not (data.get('last_name') or '').strip():
                self.add_error(
                    'last_name',
                    _('El apellido es obligatorio para persona natural.'),
                )
            if not (data.get('document_type') or '').strip():
                self.add_error(
                    'document_type',
                    _('Debe seleccionar el tipo de documento.'),
                )
        else:
            data['last_name'] = ''
            data['date_of_birth'] = None
            data['document_type'] = ''
        return data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.customer_type = self.cleaned_data.get('customer_type', 'person')
        user.document_type = self.cleaned_data.get('document_type', '') or ''
        user.document_number = self.cleaned_data.get('document_number', '')
        user.phone = self.cleaned_data.get('phone', '')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        user.save()
        notify_new_customer(user)
        return user


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone',
            'customer_type',
            'document_type',
            'document_number',
            'date_of_birth',
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Apellido'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Teléfono'}),
            'document_number': forms.TextInput(
                attrs={'placeholder': 'Número de identificación'}
            ),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class CustomLoginForm(LoginForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned = super().clean()
        if (cleaned.get('website') or '').strip():
            log_security_event(
                getattr(self, 'request', None),
                event_type='auth_honeypot',
                source='login',
                details={'reason': 'honeypot_field_filled'},
            )
            raise forms.ValidationError(_('No fue posible iniciar sesión.'))
        return cleaned


class CustomResetPasswordForm(ResetPasswordForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned = super().clean()
        if (cleaned.get('website') or '').strip():
            log_security_event(
                getattr(self, 'request', None),
                event_type='auth_honeypot',
                source='password_reset',
                details={'reason': 'honeypot_field_filled'},
            )
            raise forms.ValidationError(_('No fue posible procesar la solicitud.'))
        return cleaned


class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'address',
            'city',
            'state',
            'country',
            'postal_code',
        )
        widgets = {
            'address': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Dirección completa'}
            ),
            'city': forms.TextInput(attrs={'placeholder': 'Ciudad'}),
            'state': forms.TextInput(
                attrs={'placeholder': 'Departamento / Estado'}
            ),
            'country': forms.TextInput(attrs={'placeholder': 'País'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Código postal'}),
        }


class CustomerPasswordChangeForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['old_password'].widget.attrs.update(
            {'placeholder': 'Contraseña actual'}
        )
        self.fields['new_password1'].widget.attrs.update(
            {'placeholder': 'Nueva contraseña'}
        )
        self.fields['new_password2'].widget.attrs.update(
            {'placeholder': 'Confirma la nueva contraseña'}
        )


class AddressBookForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = (
            'alias',
            'address',
            'country',
            'state',
            'city',
            'postal_code',
            'is_default',
        )
        widgets = {
            'alias': forms.TextInput(attrs={'placeholder': 'Ej: Casa, Oficina'}),
            'address': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Dirección completa'}
            ),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Código postal'}),
        }
