# Generated by Django 5.1.3 on 2024-11-28 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='denied_urls',
            field=models.JSONField(blank=True, default=list),
        ),
    ]