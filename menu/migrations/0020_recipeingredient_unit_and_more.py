# Generated by Django 5.1.3 on 2024-12-09 22:30

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0027_alter_historicalingredient_quantity_and_more'),
        ('menu', '0019_menuitemsecondaryassociation'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipeingredient',
            name='unit',
            field=models.ForeignKey(default=37, on_delete=django.db.models.deletion.CASCADE, to='inventory.unit'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='secondary_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='quantity',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]