from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0024_add_meta_test_event_code')]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='meta_partner_agent',
            field=models.CharField(
                blank=True,
                help_text='Identificador de integración/agencia/plataforma para Meta (opcional).',
                max_length=120,
                verbose_name='Partner Agent (opcional)',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='meta_opt_out_default',
            field=models.BooleanField(
                default=False,
                help_text='Si está activo, eventos CAPI se envían con opt_out=true.',
                verbose_name='Opt out por defecto (Meta CAPI)',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='meta_data_processing_options',
            field=models.CharField(
                blank=True,
                help_text='Opciones separadas por coma. Ej: LDU',
                max_length=120,
                verbose_name='Data Processing Options (opcional)',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='meta_data_processing_country',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Código de país para data processing options. 0 si no aplica.',
                verbose_name='Data Processing Country',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='meta_data_processing_state',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Código de estado para data processing options. 0 si no aplica.',
                verbose_name='Data Processing State',
            ),
        ),
    ]
