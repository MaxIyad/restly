# Generated by Django 5.1.3 on 2024-11-19 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_alter_historicalingredient_order_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalingredient',
            name='threshold',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='threshold',
            field=models.FloatField(default=0),
        ),
    ]