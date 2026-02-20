from django import forms
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    """Registro con datos completos: tipo (empresa/persona), documento, fecha nacimiento, nombre, teléfono."""
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

    def clean(self):
        data = super().clean()
        customer_type = data.get('customer_type', 'person')
        if customer_type == 'person':
            if not (data.get('last_name') or '').strip():
                self.add_error('last_name', _('El apellido es obligatorio para persona natural.'))
            if not (data.get('document_type') or '').strip():
                self.add_error('document_type', _('Debe seleccionar el tipo de documento.'))
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
        return user
