# Generated by Django 5.1.3 on 2024-12-08 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0017_menuitem_secondary_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='associated_secondary_items',
            field=models.ManyToManyField(blank=True, related_name='associated_with', to='menu.menuitem'),
        ),
    ]