from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_add_document_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.CharField(default='Mi dirección', max_length=80, verbose_name='Alias')),
                ('address', models.TextField(verbose_name='Dirección')),
                ('city', models.CharField(max_length=100, verbose_name='Ciudad')),
                ('state', models.CharField(blank=True, max_length=100, verbose_name='Departamento / Estado')),
                ('country', models.CharField(max_length=100, verbose_name='País')),
                ('postal_code', models.CharField(blank=True, max_length=20, verbose_name='Código postal')),
                ('is_default', models.BooleanField(default=False, verbose_name='Predeterminada')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Dirección de cliente',
                'verbose_name_plural': 'Direcciones de cliente',
                'ordering': ['-is_default', '-updated_at', '-id'],
            },
        ),
    ]
