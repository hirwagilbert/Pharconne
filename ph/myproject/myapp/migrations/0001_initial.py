# Generated by Django 5.1.4 on 2024-12-06 14:10

import myapp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Pharmacy',
            fields=[
                ('P_id', models.AutoField(primary_key=True, serialize=False)),
                ('P_name', models.CharField(max_length=100)),
                ('contact_info', models.CharField(max_length=13)),
                ('location', models.CharField(default='Unknown Location', max_length=100)),
                ('start_time', models.TimeField(default=myapp.models.default_start_time)),
                ('end_time', models.TimeField(default=myapp.models.default_end_time)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('stock_level', models.CharField(default='high', max_length=100)),
                ('password', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]