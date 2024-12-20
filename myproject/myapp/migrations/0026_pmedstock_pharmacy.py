# Generated by Django 5.1.4 on 2024-12-19 13:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0025_supplier_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='pmedstock',
            name='pharmacy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='addmedicine', to='myapp.pharmacy'),
        ),
    ]
