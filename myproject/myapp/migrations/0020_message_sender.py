# Generated by Django 5.1.4 on 2024-12-10 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0019_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='sender',
            field=models.CharField(default='Unknown Sender', max_length=255),
        ),
    ]
