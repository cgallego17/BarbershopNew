# Generated manually for Meta Conversions API - Test Events support
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0023_add_meta_capi_settings')]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='meta_test_event_code',
            field=models.CharField(
                blank=True,
                help_text='Ej: TEST12345. Si se configura, los eventos se enviarán como test y aparecerán en Test Events Tool. Dejar vacío en producción.',
                max_length=20,
                verbose_name='Test Event Code (opcional)',
            ),
        ),
    ]
