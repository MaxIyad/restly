# Generated by Django 5.1.3 on 2024-11-21 23:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0004_menuitem_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]