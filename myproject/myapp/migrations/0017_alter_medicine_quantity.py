# Generated by Django 5.1.4 on 2024-12-10 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0016_alter_medicine_mfg_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medicine',
            name='quantity',
            field=models.PositiveIntegerField(default=0),
        ),
    ]