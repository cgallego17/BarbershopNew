from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_add_maintenance_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='maintenance_message',
            field=models.TextField(
                blank=True,
                help_text='Texto que verán los visitantes en el modal de mantenimiento. Si está vacío se usa el mensaje por defecto.',
                verbose_name='Mensaje de mantenimiento',
            ),
        ),
    ]
