# Generated by Django 5.1.3 on 2024-11-28 08:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_alter_customuser_pin_alter_customuser_plain_text_pin'),
        ('axes', '0009_add_session_hash'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomAccessLog',
            fields=[
                ('accesslog_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='axes.accesslog')),
                ('reason', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Custom Access Log',
                'verbose_name_plural': 'Custom Access Logs',
            },
            bases=('axes.accesslog',),
        ),
        migrations.DeleteModel(
            name='LoginAttempt',
        ),
    ]