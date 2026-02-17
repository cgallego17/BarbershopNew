# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sale_price_start',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Inicio oferta'),
        ),
        migrations.AddField(
            model_name='product',
            name='sale_price_end',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fin oferta'),
        ),
    ]
