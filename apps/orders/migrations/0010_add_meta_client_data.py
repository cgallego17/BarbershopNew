# Capturar IP y User-Agent en página de pago para Meta Conversions API (Purchase)
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0009_alter_order_status')]

    operations = [
        migrations.AddField(
            model_name='order',
            name='meta_client_ip',
            field=models.CharField(
                blank=True,
                help_text='IP del navegador al momento de ir a pagar. Se usa en el evento Purchase para mejorar EMQ.',
                max_length=45,
                verbose_name='IP del cliente (Meta CAPI)',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='meta_client_user_agent',
            field=models.CharField(
                blank=True,
                help_text='User-Agent del navegador al momento de ir a pagar. Se usa en el evento Purchase.',
                max_length=256,
                verbose_name='User-Agent del cliente (Meta CAPI)',
            ),
        ),
    ]
