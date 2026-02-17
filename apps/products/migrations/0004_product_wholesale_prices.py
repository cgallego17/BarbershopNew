# Generated manually - wholesale prices

from django.db import migrations, models
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_productvariable'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='wholesale_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
                verbose_name='Precio mayorista'
            ),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='wholesale_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name='Precio mayorista'
            ),
        ),
    ]
