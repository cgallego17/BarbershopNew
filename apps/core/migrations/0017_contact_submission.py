from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_securityevent'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Nombre')),
                ('email', models.EmailField(max_length=254, verbose_name='Correo')),
                ('phone', models.CharField(max_length=30, verbose_name='Teléfono')),
                ('message', models.TextField(verbose_name='Mensaje')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('user_agent', models.CharField(blank=True, max_length=300, verbose_name='User agent')),
                ('is_read', models.BooleanField(default=False, verbose_name='Leído')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha')),
            ],
            options={
                'verbose_name': 'Contacto (mensaje)',
                'verbose_name_plural': 'Contactos (mensajes)',
                'ordering': ['-created_at', '-id'],
            },
        ),
    ]
