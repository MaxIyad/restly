# Generated by Django 5.1.3 on 2024-11-22 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0005_menuitem_cost'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='menucategory',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='menuitem',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='menucategory',
            name='order',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='order',
            field=models.PositiveIntegerField(default=1),
        ),
    ]