from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_newsletter_subscriber'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('honeypot_trigger', 'Honeypot activado'), ('rate_limit_block', 'Bloqueo por rate limit'), ('auth_honeypot', 'Honeypot en autenticación')], max_length=40, verbose_name='Tipo de evento')),
                ('source', models.CharField(max_length=80, verbose_name='Origen')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('path', models.CharField(blank=True, max_length=255, verbose_name='Ruta')),
                ('user_agent', models.CharField(blank=True, max_length=255, verbose_name='User agent')),
                ('details', models.JSONField(blank=True, default=dict, verbose_name='Detalles')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha')),
            ],
            options={
                'verbose_name': 'Evento de seguridad',
                'verbose_name_plural': 'Eventos de seguridad',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='securityevent',
            index=models.Index(fields=['-created_at'], name='core_securi_created_8534a4_idx'),
        ),
        migrations.AddIndex(
            model_name='securityevent',
            index=models.Index(fields=['event_type', '-created_at'], name='core_securi_event_t_0d388e_idx'),
        ),
        migrations.AddIndex(
            model_name='securityevent',
            index=models.Index(fields=['source', '-created_at'], name='core_securi_source_58a5f2_idx'),
        ),
    ]
