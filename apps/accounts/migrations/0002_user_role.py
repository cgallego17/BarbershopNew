# Generated manually - add role and sync existing users

from django.db import migrations, models


def set_initial_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        if user.is_superuser:
            user.role = 'admin'
        elif user.is_staff:
            user.role = 'staff'
        else:
            user.role = 'client'
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('client', 'Cliente'), ('wholesale', 'Cliente mayorista'), ('staff', 'Staff'), ('admin', 'Administrador')],
                default='client',
                max_length=20,
                verbose_name='Tipo de usuario'
            ),
            preserve_default=False,
        ),
        migrations.RunPython(set_initial_roles, migrations.RunPython.noop),
    ]
