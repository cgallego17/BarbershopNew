from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('orders', '0010_add_meta_client_data')]

    operations = [
        migrations.AddField(
            model_name='order',
            name='meta_fbp',
            field=models.CharField(
                blank=True,
                help_text='Valor de cookie _fbp capturado temprano para mejorar match quality en Purchase.',
                max_length=255,
                verbose_name='fbp del cliente (Meta CAPI)',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='meta_fbc',
            field=models.CharField(
                blank=True,
                help_text='Valor de cookie _fbc capturado temprano para mejorar match quality en Purchase.',
                max_length=255,
                verbose_name='fbc del cliente (Meta CAPI)',
            ),
        ),
    ]
