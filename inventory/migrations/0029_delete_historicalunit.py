# Generated by Django 5.1.3 on 2024-12-13 15:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0028_historicalunit'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HistoricalUnit',
        ),
    ]