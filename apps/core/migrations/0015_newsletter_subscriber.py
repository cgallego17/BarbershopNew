from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_add_free_shipping_threshold'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsletterSubscriber',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('source', models.CharField(default='footer', max_length=80, verbose_name='Origen')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Suscrito en')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Suscriptor newsletter',
                'verbose_name_plural': 'Suscriptores newsletter',
                'ordering': ['-created_at'],
            },
        ),
    ]
