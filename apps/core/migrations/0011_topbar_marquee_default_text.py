# Generated manually

from django.db import migrations

DEFAULT_MARQUEE = 'Por compras superiores a $120.000 el envío es gratis'


def set_default_marquee(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    SiteSettings.objects.filter(topbar_marquee_text='').update(topbar_marquee_text=DEFAULT_MARQUEE)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_add_topbar_marquee_text'),
    ]

    operations = [
        migrations.RunPython(set_default_marquee, noop),
    ]
