# Generated manually - atributos y variantes para productos variables

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_product_sale_price_end_product_sale_price_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='productattribute',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='slug',
            field=models.SlugField(max_length=100, unique=True),
        ),
        migrations.CreateModel(
            name='ProductAttributeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=100)),
                ('order', models.PositiveIntegerField(default=0)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='products.productattribute')),
            ],
            options={
                'verbose_name': 'Valor de atributo',
                'verbose_name_plural': 'Valores de atributos',
                'ordering': ['order', 'value'],
                'unique_together': {('attribute', 'value')},
            },
        ),
        migrations.AddField(
            model_name='product',
            name='used_attributes',
            field=models.ManyToManyField(blank=True, related_name='products', to='products.productattribute', verbose_name='Atributos (producto variable)'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='sale_price_end',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fin oferta'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='sale_price_start',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Inicio oferta'),
        ),
    ]
