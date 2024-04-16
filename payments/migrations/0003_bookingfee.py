# Generated by Django 2.2.28 on 2024-04-16 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_auto_20240321_0456'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingFee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fee', models.DecimalField(decimal_places=2, max_digits=8)),
            ],
        ),
    ]