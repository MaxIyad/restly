# Generated by Django 3.1.6 on 2024-11-16 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_alter_historicalingredient_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='historicalingredient',
            name='id',
            field=models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]