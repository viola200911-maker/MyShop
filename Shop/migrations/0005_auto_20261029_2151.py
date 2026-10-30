from django.db import migrations

def create_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        id=1,
        defaults={
            'domain': 'myshop-lnqp.onrender.com',
            'name': 'MyShop',
        }
    )

class Migration(migrations.Migration):

    dependencies = [
        ('Shop', '0004_review'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_site),
    ]