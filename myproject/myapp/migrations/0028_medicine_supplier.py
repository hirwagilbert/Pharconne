# Generated by Django 5.1.4 on 2024-12-19 13:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0027_medicine_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicine',
            name='supplier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='addmedicine', to='myapp.supplier'),
        ),
    ]
