# Generated by Django 5.1.4 on 2024-12-10 07:05

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_delete_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('O_id', models.AutoField(primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField()),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('order_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('delivery_date', models.DateTimeField(blank=True, null=True)),
                ('medicine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='myapp.medicine')),
                ('pharmacy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='myapp.pharmacy')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='myapp.supplier')),
            ],
        ),
    ]
