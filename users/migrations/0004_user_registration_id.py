# Generated by Django 2.2.28 on 2024-01-31 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20240111_0937'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='registration_id',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]