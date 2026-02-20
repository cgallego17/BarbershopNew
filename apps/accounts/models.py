from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario extendido para e-commerce."""
    ROLE_CHOICES = [
        ('client', 'Cliente'),
        ('wholesale', 'Cliente mayorista'),
        ('staff', 'Staff'),
        ('admin', 'Administrador'),
    ]
    CUSTOMER_TYPE_CHOICES = [
        ('person', 'Persona natural'),
        ('company', 'Empresa'),
    ]
    DOCUMENT_TYPE_CHOICES = [
        ('', '--'),
        ('CC', 'Cédula de ciudadanía'),
        ('CE', 'Cédula de extranjería'),
        ('PA', 'Pasaporte'),
    ]

    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='client',
        verbose_name='Tipo de usuario'
    )
    customer_type = models.CharField(
        max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='person',
        verbose_name='Registrado como', blank=True
    )
    document_type = models.CharField(
        'Tipo de documento', max_length=10,
        choices=DOCUMENT_TYPE_CHOICES, default='', blank=True
    )
    document_number = models.CharField(
        'Número de identificación', max_length=30, blank=True
    )
    date_of_birth = models.DateField('Fecha de nacimiento', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField('Departamento / Estado', max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def save(self, *args, **kwargs):
        # Username automático desde email (Django requiere username único, login es por email)
        if not self.username and self.email:
            self.username = (self.email or '').lower()[:150]
            if not self.pk and User.objects.filter(username=self.username).exists():
                import uuid
                self.username = f"{self.email.split('@')[0]}_{uuid.uuid4().hex[:8]}"[:150]
        # Sincronizar is_staff/is_superuser con role. Superusers sin role explícito se tratan como admin.
        if self.is_superuser and self.role == 'client':
            self.role = 'admin'
        if self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True
        elif self.role == 'staff':
            self.is_staff = False
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    @property
    def can_access_dashboard(self):
        """Staff y admin pueden acceder al panel de administración."""
        return self.role in ('staff', 'admin')

    @property
    def can_access_django_admin(self):
        """Solo administradores acceden a Django Admin."""
        return self.role == 'admin'

    @property
    def is_wholesale(self):
        return self.role == 'wholesale'

    @property
    def is_admin(self):
        return self.role == 'admin'
