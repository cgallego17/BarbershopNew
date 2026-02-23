from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_home_popup_announcement'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='maintenance_mode',
            field=models.BooleanField(
                default=False,
                help_text='Si está activo, el sitio público mostrará la página de mantenimiento (excepto /panel/).',
                verbose_name='Modo mantenimiento',
            ),
        ),
    ]
