from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_contact_submission'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomePopupAnnouncement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False, verbose_name='Activo')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='Título')),
                ('content', models.TextField(blank=True, verbose_name='Contenido')),
                ('image', models.ImageField(blank=True, null=True, upload_to='home/popup/', verbose_name='Imagen')),
                ('button_text', models.CharField(blank=True, max_length=50, verbose_name='Texto del botón')),
                ('button_url', models.CharField(blank=True, max_length=255, verbose_name='URL del botón')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Popup del home',
                'verbose_name_plural': 'Popup del home',
            },
        ),
    ]
