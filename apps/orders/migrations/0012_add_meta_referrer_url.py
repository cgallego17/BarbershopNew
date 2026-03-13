from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0011_add_meta_fbp_fbc')]

    operations = [
        migrations.AddField(
            model_name='order',
            name='meta_referrer_url',
            field=models.URLField(
                blank=True,
                help_text='HTTP_REFERER capturado en el journey de compra para enviarlo en eventos web.',
                max_length=512,
                verbose_name='Referrer URL (Meta CAPI)',
            ),
        ),
    ]
