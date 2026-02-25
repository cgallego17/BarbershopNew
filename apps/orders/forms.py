from django import forms
from django.core.validators import RegexValidator


class CheckoutForm(forms.Form):
    CUSTOMER_TYPE_CHOICES = (
        ("person", "Persona natural"),
        ("company", "Empresa"),
    )
    DOCUMENT_TYPE_CHOICES = (
        ("", "Seleccione"),
        ("CC", "Cédula ciudadanía"),
        ("CE", "Cédula extranjería"),
        ("PA", "Pasaporte"),
        ("NIT", "NIT"),
    )

    billing_customer_type = forms.ChoiceField(choices=CUSTOMER_TYPE_CHOICES)
    billing_document_type = forms.ChoiceField(choices=DOCUMENT_TYPE_CHOICES)
    billing_document_number = forms.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9.\-]{5,30}$",
                message="Número de identificación inválido.",
            )
        ],
    )
    billing_date_of_birth = forms.DateField(required=False)
    billing_first_name = forms.CharField(max_length=150)
    billing_last_name = forms.CharField(required=False, max_length=150)
    billing_email = forms.EmailField(max_length=254)
    billing_phone = forms.CharField(required=True, max_length=20)
    billing_address = forms.CharField(max_length=255)
    billing_city = forms.CharField(max_length=100)
    billing_state = forms.CharField(required=False, max_length=100)
    billing_country = forms.CharField(max_length=100)
    billing_postal_code = forms.CharField(required=False, max_length=20)
    coupon_code = forms.CharField(required=False, max_length=40)
    accept_terms = forms.BooleanField(required=True)
    accept_privacy = forms.BooleanField(required=True)

    def clean(self):
        cleaned = super().clean()
        customer_type = cleaned.get("billing_customer_type")
        document_type = cleaned.get("billing_document_type")
        last_name = (cleaned.get("billing_last_name") or "").strip()

        if customer_type == "person":
            if not last_name:
                self.add_error(
                    "billing_last_name",
                    "El apellido es obligatorio para persona natural.",
                )
            if document_type not in {"CC", "CE", "PA"}:
                self.add_error(
                    "billing_document_type",
                    "Tipo de documento inválido para persona natural.",
                )
        elif customer_type == "company":
            cleaned["billing_last_name"] = ""
            cleaned["billing_date_of_birth"] = None
            if document_type != "NIT":
                self.add_error(
                    "billing_document_type",
                    "Para empresa debes usar NIT.",
                )

        return cleaned
