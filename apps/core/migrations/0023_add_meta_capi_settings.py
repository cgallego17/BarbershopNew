# Generated manually for Meta Conversions API
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0022_add_site_url')]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='meta_pixel_id',
            field=models.CharField(
                blank=True,
                help_text='ID del pixel de Meta (ej: 1190679916479399). Necesario para enviar eventos por Conversions API desde el servidor.',
                max_length=30,
                verbose_name='Meta Pixel ID',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='meta_conversions_api_token',
            field=models.CharField(
                blank=True,
                help_text='Token generado en Events Manager → Dataset → Configuración → Conversions API. Mantener confidencial.',
                max_length=500,
                verbose_name='Meta Conversions API - Token de acceso',
            ),
        ),
    ]
