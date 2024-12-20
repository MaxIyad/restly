# Generated by Django 5.1.3 on 2024-11-25 12:29

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_loginattempt_reason_alter_loginattempt_success'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='address',
            field=models.TextField(blank=True, null=True, verbose_name='Address'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='hourly_wage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Hourly Wage'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='join_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Join Date'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='Phone Number'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('Staff', 'Staff'), ('Manager', 'Manager'), ('Admin', 'Admin')], default='Staff', max_length=50),
        ),
        migrations.AddField(
            model_name='customuser',
            name='staff_meal_limit',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Staff Meal Limit'),
        ),
    ]
