# Generated by Django 2.2.28 on 2024-01-11 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20240102_0726'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Username'),
        ),
    ]