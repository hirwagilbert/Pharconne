# Generated by Django 5.1.4 on 2024-12-07 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_alter_pharmacy_p_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pharmacy',
            name='P_id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]